import httpx
import pytest

from kendra_api.config import Settings
from kendra_api.connections.ollama import OllamaConnection
from kendra_api.connections.postgres import PostgresConnection
from kendra_api.connections.qdrant import QdrantConnection


class ReadyQdrantClient:
    async def get_collections(self) -> object:
        return object()

    async def close(self) -> None:
        return None


class UnavailableQdrantClient(ReadyQdrantClient):
    async def get_collections(self) -> object:
        raise RuntimeError("contains internal endpoint details")


class ReadyPostgresConnection:
    def __init__(self) -> None:
        self.closed = False

    async def fetchval(self, query: str) -> int:
        assert query == "SELECT 1"
        return 1

    async def close(self, timeout: float) -> None:
        assert timeout == 3.0
        self.closed = True


@pytest.mark.asyncio
async def test_postgres_connection_opens_checks_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_connection = ReadyPostgresConnection()

    async def fake_connect(*, dsn: str, timeout: float) -> ReadyPostgresConnection:
        assert dsn.startswith("postgresql://kendra:")
        assert timeout == 3.0
        return fake_connection

    monkeypatch.setattr(
        "kendra_api.connections.postgres.asyncpg.connect",
        fake_connect,
    )

    result = await PostgresConnection(
        Settings(_env_file=None, postgres_password="test-only")
    ).check()

    assert (result.ready, result.code) == (True, "reachable")
    assert fake_connection.closed is True


@pytest.mark.asyncio
async def test_qdrant_connection_reports_sanitized_readiness() -> None:
    settings = Settings(_env_file=None, postgres_password="test-only")
    ready = await QdrantConnection(settings, client=ReadyQdrantClient()).check()  # type: ignore[arg-type]
    unavailable = await QdrantConnection(
        settings,
        client=UnavailableQdrantClient(),  # type: ignore[arg-type]
    ).check()

    assert (ready.ready, ready.code) == (True, "reachable")
    assert (unavailable.ready, unavailable.code) == (False, "unreachable")
    assert "endpoint" not in repr(unavailable)


@pytest.mark.asyncio
async def test_ollama_connection_checks_local_tags_endpoint() -> None:
    seen_paths: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        return httpx.Response(200, json={"models": []})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://ollama:11434",
    )
    connection = OllamaConnection(
        Settings(_env_file=None, postgres_password="test-only"), client=client
    )

    result = await connection.check()
    await connection.close()

    assert result.ready is True
    assert result.code == "reachable"
    assert seen_paths == ["/api/tags"]
