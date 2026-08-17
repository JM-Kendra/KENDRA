"""Local BGE-M3 embeddings through Ollama's batch embed endpoint."""

import math
from typing import Protocol

import httpx

from kendra_api.ingestion.errors import IngestionError


class Embedder(Protocol):
    model_identity: str

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OllamaBgeM3Embedder:
    def __init__(
        self,
        base_url: str,
        model: str = "bge-m3",
        batch_size: int = 16,
        timeout_seconds: int = 300,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if "bge-m3" not in model.lower():
            raise ValueError("the Milestone 9 embedding model must be BGE-M3")
        self.model_identity = model
        self._batch_size = batch_size
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout_seconds
        )
        self._owns_client = client is None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        dimension: int | None = None
        for offset in range(0, len(texts), self._batch_size):
            batch = texts[offset : offset + self._batch_size]
            try:
                response = await self._client.post(
                    "/api/embed",
                    json={"model": self.model_identity, "input": batch, "truncate": False},
                )
                response.raise_for_status()
                payload = response.json()
                embedded = payload["embeddings"]
            except Exception as exc:
                raise IngestionError("embedding_failure", "local embedding failed") from exc
            if not isinstance(embedded, list) or len(embedded) != len(batch):
                raise IngestionError("embedding_count_mismatch", "embedding batch is incomplete")
            for vector in embedded:
                if not isinstance(vector, list) or not vector:
                    raise IngestionError("embedding_dimension_mismatch", "embedding is empty")
                if dimension is None:
                    dimension = len(vector)
                if len(vector) != dimension or not all(
                    isinstance(value, (int, float)) and math.isfinite(value)
                    for value in vector
                ):
                    raise IngestionError("invalid_embedding", "embedding values are invalid")
                vectors.append([float(value) for value in vector])
        if len(vectors) != len(texts):
            raise IngestionError("embedding_count_mismatch", "embedding result is incomplete")
        return vectors

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
