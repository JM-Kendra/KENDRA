"""Qdrant connection and readiness probe."""

from qdrant_client import AsyncQdrantClient

from kendra_api.config import Settings
from kendra_api.readiness import ProbeResult


class QdrantConnection:
    name = "qdrant"

    def __init__(
        self,
        settings: Settings,
        client: AsyncQdrantClient | None = None,
    ) -> None:
        self._client = client or AsyncQdrantClient(
            url=str(settings.qdrant_url),
            api_key=settings.qdrant_api_key_value,
            timeout=settings.readiness_timeout_seconds,
            check_compatibility=False,
        )

    @property
    def client(self) -> AsyncQdrantClient:
        return self._client

    async def check(self) -> ProbeResult:
        try:
            await self._client.get_collections()
        except Exception:
            return ProbeResult(self.name, False, "unreachable")
        return ProbeResult(self.name, True, "reachable")

    async def close(self) -> None:
        await self._client.close()
