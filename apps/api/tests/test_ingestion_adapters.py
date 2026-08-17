import json
from types import SimpleNamespace

import httpx
import pytest

from kendra_api.ingestion.embedding import OllamaBgeM3Embedder
from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import ChunkRecord, ExtractionMethod
from kendra_api.ingestion.vector_store import QdrantVectorGenerationStore


@pytest.mark.asyncio
async def test_ollama_generates_bge_m3_embeddings_locally_without_truncation() -> None:
    requests: list[bytes] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.content)
        assert request.url.path == "/api/embed"
        payload = json.loads(request.content)
        assert payload == {
            "model": "bge-m3:test",
            "input": ["first chunk", "second chunk"],
            "truncate": False,
        }
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://ollama:11434"
    )
    embedder = OllamaBgeM3Embedder(
        "http://ollama:11434", "bge-m3:test", client=client
    )

    assert await embedder.embed(["first chunk", "second chunk"]) == [
        [0.1, 0.2],
        [0.3, 0.4],
    ]
    assert len(requests) == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_ollama_rejects_partial_embedding_batch() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://ollama:11434"
    )
    embedder = OllamaBgeM3Embedder("http://ollama:11434", client=client)
    with pytest.raises(IngestionError) as failure:
        await embedder.embed(["one", "two"])
    assert failure.value.code == "embedding_count_mismatch"
    await client.aclose()


class FakeQdrant:
    def __init__(self, fail_upsert: bool = False) -> None:
        self.fail_upsert = fail_upsert
        self.created: str | None = None
        self.points: list[object] = []
        self.deleted: list[str] = []

    async def create_collection(self, *, collection_name: str, vectors_config: object) -> None:
        self.created = collection_name

    async def upsert(self, *, collection_name: str, points: list[object], wait: bool) -> None:
        if self.fail_upsert:
            raise RuntimeError("injected")
        self.points = points

    async def get_collection(self, collection_name: str) -> object:
        return SimpleNamespace(points_count=len(self.points))

    async def delete_collection(self, collection_name: str) -> None:
        self.deleted.append(collection_name)


def _chunk() -> ChunkRecord:
    return ChunkRecord(
        chunk_id="123e4567-e89b-12d3-a456-426614174000",
        version_id="ver-1",
        source_sha256="a" * 64,
        processing_run_id="run-1",
        page_number=3,
        sequence=0,
        start_offset=0,
        end_offset=4,
        text="text",
        extraction_method=ExtractionMethod.DOCLING,
        content_sha256="b" * 64,
        chunker_version="test",
    )


@pytest.mark.asyncio
async def test_qdrant_payload_is_minimal_and_page_aware() -> None:
    client = FakeQdrant()
    store = QdrantVectorGenerationStore(client, "kendra-test")  # type: ignore[arg-type]

    collection = await store.index("gen-1", [_chunk()], [[0.1, 0.2]])

    assert collection == "kendra-test_gen-1"
    point = client.points[0]
    assert point.payload == {  # type: ignore[attr-defined]
        "chunk_id": _chunk().chunk_id,
        "version_id": "ver-1",
        "source_sha256": "a" * 64,
        "physical_page": 3,
        "processing_run_id": "run-1",
        "index_generation_id": "gen-1",
    }


@pytest.mark.asyncio
async def test_qdrant_partial_failure_discards_staging_collection() -> None:
    client = FakeQdrant(fail_upsert=True)
    store = QdrantVectorGenerationStore(client, "kendra-test")  # type: ignore[arg-type]

    with pytest.raises(IngestionError) as failure:
        await store.index("gen-1", [_chunk()], [[0.1, 0.2]])

    assert failure.value.code == "qdrant_failure"
    assert client.deleted == ["kendra-test_gen-1"]
