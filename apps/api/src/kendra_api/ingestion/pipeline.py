"""Milestone 9 ingestion orchestration; no question-answering behavior lives here."""

import uuid
from pathlib import Path

from kendra_api.ingestion.chunking import PageChunker
from kendra_api.ingestion.embedding import Embedder
from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.extraction import PageExtractionPipeline
from kendra_api.ingestion.models import (
    DocumentIdentity,
    IngestionResult,
    IntakeManifest,
    ProcessingState,
)
from kendra_api.ingestion.registry import Registry
from kendra_api.ingestion.storage import LocalDocumentAdmissionStore
from kendra_api.ingestion.validation import validate_pdf
from kendra_api.ingestion.vector_store import VectorGenerationStore


def _identity() -> DocumentIdentity:
    return DocumentIdentity(
        ingestion_id=f"ing-{uuid.uuid4()}",
        document_id=f"doc-{uuid.uuid4()}",
        version_id=f"ver-{uuid.uuid4()}",
        processing_run_id=f"run-{uuid.uuid4()}",
        generation_id=f"gen-{uuid.uuid4()}",
    )


class IngestionPipeline:
    def __init__(
        self,
        registry: Registry,
        storage: LocalDocumentAdmissionStore,
        extractor: PageExtractionPipeline,
        chunker: PageChunker,
        embedder: Embedder,
        vectors: VectorGenerationStore,
        max_bytes: int,
        max_pages: int,
        pipeline_revision: str,
    ) -> None:
        self._registry = registry
        self._storage = storage
        self._extractor = extractor
        self._chunker = chunker
        self._embedder = embedder
        self._vectors = vectors
        self._max_bytes = max_bytes
        self._max_pages = max_pages
        self._pipeline_revision = pipeline_revision

    async def ingest(self, path: Path, intake: IntakeManifest) -> IngestionResult:
        validated = validate_pdf(path, intake, self._max_bytes, self._max_pages)
        await self._registry.initialize()
        existing = await self._registry.find_by_checksum(validated.sha256)
        if existing:
            return IngestionResult(
                ingestion_id="duplicate",
                document_id=existing.document_id,
                version_id=existing.version_id,
                sha256=existing.sha256,
                state=existing.state,
                duplicate=True,
                page_count=validated.page_count,
                chunk_count=0,
                generation_id=None,
            )

        identity = _identity()
        stored = self._storage.admit(
            validated, intake, identity, self._pipeline_revision
        )
        registered = False
        collection_name: str | None = None
        try:
            race_duplicate = await self._registry.begin_processing(
                identity,
                validated,
                intake,
                stored,
                self._pipeline_revision,
                self._extractor.tool_identity,
                self._embedder.model_identity,
            )
            if race_duplicate:
                self._storage.discard_unregistered(identity)
                return IngestionResult(
                    ingestion_id=identity.ingestion_id,
                    document_id=race_duplicate.document_id,
                    version_id=race_duplicate.version_id,
                    sha256=race_duplicate.sha256,
                    state=race_duplicate.state,
                    duplicate=True,
                    page_count=validated.page_count,
                    chunk_count=0,
                    generation_id=None,
                )
            registered = True
            pages = self._extractor.extract(
                self._storage.source_path(identity.document_id, identity.version_id),
                identity.version_id,
                identity.processing_run_id,
                validated.page_count,
            )
            chunks = self._chunker.chunk(pages, validated.sha256)
            if not chunks:
                raise IngestionError("empty_derived_records", "no publishable chunks were produced")
            embeddings = await self._embedder.embed([chunk.text for chunk in chunks])
            await self._registry.save_derived_records(pages, chunks)
            collection_name = await self._vectors.index(
                identity.generation_id, chunks, embeddings
            )
            await self._registry.mark_ready(identity, collection_name)
            return IngestionResult(
                ingestion_id=identity.ingestion_id,
                document_id=identity.document_id,
                version_id=identity.version_id,
                sha256=validated.sha256,
                state=ProcessingState.READY,
                duplicate=False,
                page_count=len(pages),
                chunk_count=len(chunks),
                generation_id=identity.generation_id,
            )
        except Exception as exc:
            error_code = exc.code if isinstance(exc, IngestionError) else "processing_failure"
            if collection_name is not None:
                try:
                    await self._vectors.discard(collection_name)
                except Exception:
                    error_code = "partial_cleanup_failure"
            if registered:
                try:
                    await self._registry.mark_failed(identity, error_code)
                except Exception as state_exc:
                    raise IngestionError(
                        "failure_state_update_failed",
                        "processing failed and its failed state could not be recorded",
                    ) from state_exc
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(error_code, "ingestion processing failed") from exc
