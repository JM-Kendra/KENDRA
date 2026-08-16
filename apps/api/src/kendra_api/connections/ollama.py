"""Ollama HTTP connection and readiness probe."""

import httpx

from kendra_api.config import Settings
from kendra_api.readiness import ProbeResult


class OllamaConnection:
    name = "ollama"

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=str(settings.ollama_url).rstrip("/"),
            timeout=settings.readiness_timeout_seconds,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    async def check(self) -> ProbeResult:
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
        except Exception:
            return ProbeResult(self.name, False, "unreachable")
        return ProbeResult(self.name, True, "reachable")

    async def close(self) -> None:
        await self._client.aclose()
