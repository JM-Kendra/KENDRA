from pathlib import Path

import pytest

from kendra_api.ingestion.chunking import PageChunker
from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.extraction import PageExtractionPipeline
from kendra_api.ingestion.models import ExistingVersion, ProcessingState
from kendra_api.ingestion.pipeline import IngestionPipeline
from kendra_api.ingestion.storage import LocalDocumentAdmissionStore
from pdf_fixtures import make_digital_pdf, manifest_for


class StaticExtractor:
    version = "static-docling"

    def extract_pages(self, path: Path, page_count: int) -> list[str]:
        return [f"page {number} contains enough synthetic searchable text" for number in range(1, page_count + 1)]


class NoOcr:
    version = "no-ocr"

    def extract_page(self, path: Path, page_number: int) -> str:
        raise AssertionError("OCR was unexpectedly called")


class StaticNativeExtractor:
    version = "static-native"

    def extract_page(self, path: Path, page_number: int) -> str:
        return f"page {page_number} contains enough synthetic searchable text"


class FakeEmbedder:
    model_identity = "bge-m3:test"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(index), 1.0, 0.5] for index, _ in enumerate(texts)]


class FakeVectors:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.indexed = 0
        self.discarded: list[str] = []

    async def index(self, generation_id: str, chunks: list[object], vectors: list[list[float]]) -> str:
        if self.fail:
            raise IngestionError("qdrant_failure", "injected partial failure")
        self.indexed = len(chunks)
        return f"collection-{generation_id}"

    async def discard(self, collection_name: str) -> None:
        self.discarded.append(collection_name)


class FakeRegistry:
    def __init__(self, duplicate: ExistingVersion | None = None) -> None:
        self.duplicate = duplicate
        self.transitions: list[str] = []
        self.pages: list[object] = []
        self.chunks: list[object] = []

    async def initialize(self) -> None:
        self.transitions.append("initialized")

    async def find_by_checksum(self, sha256: str) -> ExistingVersion | None:
        return self.duplicate

    async def begin_processing(self, *args: object, **kwargs: object) -> None:
        self.transitions.append("processing")

    async def save_derived_records(self, pages: list[object], chunks: list[object]) -> None:
        self.pages = pages
        self.chunks = chunks
        self.transitions.append("derived_saved")

    async def mark_ready(self, identity: object, qdrant_collection: str) -> None:
        self.transitions.append("ready")

    async def mark_failed(self, identity: object, error_code: str) -> None:
        self.transitions.append(f"failed:{error_code}")


def _pipeline(tmp_path: Path, registry: FakeRegistry, vectors: FakeVectors) -> IngestionPipeline:
    return IngestionPipeline(
        registry=registry,
        storage=LocalDocumentAdmissionStore(tmp_path / "repository"),
        extractor=PageExtractionPipeline(
            StaticExtractor(), StaticNativeExtractor(), NoOcr(), minimum_chars=10
        ),
        chunker=PageChunker(size=100, overlap=20),
        embedder=FakeEmbedder(),
        vectors=vectors,
        max_bytes=1_000_000,
        max_pages=10,
        pipeline_revision="test-revision",
    )


@pytest.mark.asyncio
async def test_successful_processing_transitions_to_ready(tmp_path: Path) -> None:
    pdf = make_digital_pdf(tmp_path / "digital.pdf", ["first", "second"])
    registry = FakeRegistry()
    vectors = FakeVectors()

    result = await _pipeline(tmp_path, registry, vectors).ingest(pdf, manifest_for(pdf, 2))

    assert result.state is ProcessingState.READY
    assert result.page_count == 2
    assert result.chunk_count == 2
    assert registry.transitions == ["initialized", "processing", "derived_saved", "ready"]
    assert [page.page_number for page in registry.pages] == [1, 2]  # type: ignore[attr-defined]
    assert vectors.indexed == 2


@pytest.mark.asyncio
async def test_duplicate_checksum_returns_existing_without_new_original(tmp_path: Path) -> None:
    pdf = make_digital_pdf(tmp_path / "duplicate.pdf", ["duplicate"])
    existing = ExistingVersion("doc-existing", "ver-existing", manifest_for(pdf, 1).expected_sha256, ProcessingState.READY)
    registry = FakeRegistry(existing)

    result = await _pipeline(tmp_path, registry, FakeVectors()).ingest(pdf, manifest_for(pdf, 1))

    assert result.duplicate is True
    assert result.document_id == "doc-existing"
    assert not (tmp_path / "repository" / "objects").exists()
    assert registry.transitions == ["initialized"]


@pytest.mark.asyncio
async def test_partial_vector_failure_marks_failed_and_preserves_original(tmp_path: Path) -> None:
    pdf = make_digital_pdf(tmp_path / "failure.pdf", ["partial failure"])
    registry = FakeRegistry()
    pipeline = _pipeline(tmp_path, registry, FakeVectors(fail=True))

    with pytest.raises(IngestionError) as failure:
        await pipeline.ingest(pdf, manifest_for(pdf, 1))

    assert failure.value.code == "qdrant_failure"
    assert registry.transitions[-1] == "failed:qdrant_failure"
    stored_sources = list((tmp_path / "repository" / "objects").glob("*/*/source.pdf"))
    assert len(stored_sources) == 1
    assert stored_sources[0].read_bytes() == pdf.read_bytes()
