"""Retrieval gate (MVP_SPEC Step 9).

Qdrant holds no document text — the Milestone 9 payload carries only chunk_id,
version_id, source_sha256, physical_page, processing_run_id, and generation. Chunk
text is read back from PostgreSQL, so the vector index can never be the source of
an excerpt.

Failures here are deliberately NOT swallowed. A broken client or an unreachable
Qdrant must surface as a typed system error, because an exception treated as
"no results" is indistinguishable to the caller from a truthful abstention — and
a false abstention is a wrong answer with a calm face.

COLLECTION LAYOUT: Milestone 9 writes one Qdrant collection per document version,
so no single collection spans the corpus. The request's `collection_id` therefore
labels the approved corpus; it is not a Qdrant collection name. Retrieval searches
every active collection and merges by score, which is what makes a cross-document
question answerable at all under this layout.

CONFIGURATION WARNING: `top_k` and the candidate threshold below are engineering
defaults. EXP-02 — the retrieval experiment ADR-003 and MVP_SPEC Step 9 require to
select them — has never been run. These numbers are not experiment-derived and no
recall claim may be made from them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from kendra_api.answering.models import Evidence
from kendra_api.connections.postgres import PostgresConnection
from kendra_api.ingestion.embedding import Embedder

if TYPE_CHECKING:  # pragma: no cover
    from kendra_api.answering.sources import SourceRegistry as SourceRegistryLike


class Retriever(Protocol):
    async def retrieve(self, question: str, collection_id: str) -> list[Evidence]: ...


class EmptyRetriever:
    """Fail-closed default: retrieves nothing, so the API abstains."""

    async def retrieve(self, question: str, collection_id: str) -> list[Evidence]:  # noqa: ARG002
        return []


class QdrantRetriever:
    _CHUNK_SQL = """
        SELECT c.chunk_id::text AS chunk_id,
               c.version_id,
               c.source_sha256,
               c.processing_run_id,
               c.page_number,
               c.text,
               c.extraction_method,
               v.document_id,
               v.original_filename
        FROM chunks c
        JOIN document_versions v ON v.version_id = c.version_id
        WHERE c.chunk_id = ANY($1::uuid[])
    """

    def __init__(
        self,
        client: AsyncQdrantClient,
        embedder: Embedder,
        postgres: PostgresConnection,
        registry: "SourceRegistryLike",
        top_k: int,
        score_threshold: float,
    ) -> None:
        self._client = client
        self._embedder = embedder
        self._postgres = postgres
        self._registry = registry
        self._top_k = top_k
        self._score_threshold = score_threshold

    async def retrieve(self, question: str, collection_id: str) -> list[Evidence]:
        vectors = await self._embedder.embed([question])
        if not vectors:
            return []
        collections = await self._registry.active_collections()
        if not collections:
            return []

        scored: list[tuple[float, dict]] = []
        for collection in collections:
            try:
                response = await self._client.query_points(
                    collection_name=collection,
                    query=vectors[0],
                    limit=self._top_k,
                    score_threshold=self._score_threshold,
                    with_payload=True,
                )
            except UnexpectedResponse as exc:
                if exc.status_code == 404:
                    # The generation is registered but its collection is gone. That
                    # is a reconciliation fault, not evidence; skip this collection.
                    continue
                raise
            for hit in response.points:
                payload = hit.payload or {}
                if payload.get("chunk_id"):
                    scored.append((float(hit.score), payload))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        payloads: dict[str, dict] = {}
        for _score, payload in scored:
            chunk_id = str(payload["chunk_id"])
            if chunk_id not in payloads:
                payloads[chunk_id] = payload
            if len(payloads) >= self._top_k:
                break
        if not payloads:
            return []

        async with self._postgres.connection() as connection:
            rows = await connection.fetch(self._CHUNK_SQL, list(payloads))

        evidence: list[Evidence] = []
        for index, row in enumerate(rows):
            payload = payloads.get(row["chunk_id"], {})
            evidence.append(
                Evidence(
                    # Opaque and request-scoped: the model never sees a chunk id.
                    evidence_id=f"ev-{index + 1}",
                    text=row["text"],
                    document_id=row["document_id"],
                    version_id=row["version_id"],
                    filename=row["original_filename"],
                    page=row["page_number"],
                    chunk_id=row["chunk_id"],
                    source_sha256=row["source_sha256"],
                    processing_run_id=row["processing_run_id"],
                    extraction_method=row["extraction_method"],
                    generation_id=str(payload.get("index_generation_id", "")),
                )
            )
        return evidence
