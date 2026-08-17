"""Disposable Qdrant generation writer with minimal source payloads."""

import re
from typing import Protocol

from qdrant_client import AsyncQdrantClient, models

from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import ChunkRecord


class VectorGenerationStore(Protocol):
    async def index(
        self, generation_id: str, chunks: list[ChunkRecord], vectors: list[list[float]]
    ) -> str: ...

    async def discard(self, collection_name: str) -> None: ...


class QdrantVectorGenerationStore:
    def __init__(self, client: AsyncQdrantClient, collection_prefix: str) -> None:
        safe_prefix = re.sub(r"[^A-Za-z0-9_-]", "_", collection_prefix).strip("_")
        if not safe_prefix:
            raise ValueError("Qdrant collection prefix is invalid")
        self._client = client
        self._prefix = safe_prefix

    def collection_name(self, generation_id: str) -> str:
        safe_generation = re.sub(r"[^A-Za-z0-9_-]", "_", generation_id)
        return f"{self._prefix}_{safe_generation}"[:255]

    async def index(
        self, generation_id: str, chunks: list[ChunkRecord], vectors: list[list[float]]
    ) -> str:
        if not chunks or len(chunks) != len(vectors):
            raise IngestionError("vector_count_mismatch", "chunk and vector counts differ")
        dimension = len(vectors[0])
        if dimension <= 0 or any(len(vector) != dimension for vector in vectors):
            raise IngestionError("vector_dimension_mismatch", "vector dimensions differ")
        collection = self.collection_name(generation_id)
        try:
            await self._client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )
            points = [
                models.PointStruct(
                    id=chunk.chunk_id,
                    vector=vector,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "version_id": chunk.version_id,
                        "source_sha256": chunk.source_sha256,
                        "physical_page": chunk.page_number,
                        "processing_run_id": chunk.processing_run_id,
                        "index_generation_id": generation_id,
                    },
                )
                for chunk, vector in zip(chunks, vectors, strict=True)
            ]
            await self._client.upsert(collection_name=collection, points=points, wait=True)
            info = await self._client.get_collection(collection)
            if info.points_count != len(points):
                raise IngestionError("vector_count_mismatch", "Qdrant point count differs")
            return collection
        except IngestionError:
            await self.discard(collection)
            raise
        except Exception as exc:
            await self.discard(collection)
            raise IngestionError("qdrant_failure", "Qdrant staging generation failed") from exc

    async def discard(self, collection_name: str) -> None:
        try:
            await self._client.delete_collection(collection_name)
        except Exception:
            return
