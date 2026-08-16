from dataclasses import dataclass

import httpx
import pytest

from kendra_api.config import Settings
from kendra_api.main import create_app
from kendra_api.readiness import ProbeResult


@dataclass
class FakeProbe:
    name: str
    ready: bool
    code: str

    async def check(self) -> ProbeResult:
        return ProbeResult(self.name, self.ready, self.code)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_health_returns_ready_without_configuration_details() -> None:
    secret = "must-never-appear"
    app = create_app(
        Settings(_env_file=None, postgres_password=secret),
        probes=[
            FakeProbe("postgres", True, "reachable"),
            FakeProbe("qdrant", True, "reachable"),
            FakeProbe("ollama", True, "reachable"),
            FakeProbe("document_store", True, "available"),
        ],
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert secret not in response.text
    assert "postgresql://" not in response.text
    assert "/documents" not in response.text
    assert set(response.json()["services"]["postgres"]) == {"status", "code"}


@pytest.mark.asyncio
async def test_health_returns_503_when_a_dependency_is_unavailable() -> None:
    app = create_app(
        Settings(_env_file=None),
        probes=[
            FakeProbe("postgres", False, "unreachable"),
            FakeProbe("document_store", True, "available"),
        ],
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "services": {
            "postgres": {"status": "not_ready", "code": "unreachable"},
            "document_store": {"status": "ready", "code": "available"},
        },
    }
