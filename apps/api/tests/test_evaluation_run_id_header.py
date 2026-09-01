"""Milestone 12 — `X-Kendra-Evaluation-Run-Id` header validation.

Found by external review: the header was written verbatim into the append-only,
hash-chained audit table with no length or character constraint, so any caller
could inject arbitrary content into an immutable record.
"""

from __future__ import annotations

import httpx
import pytest

from kendra_api.answering import dependencies as deps
from kendra_api.audit.sink import InMemoryAuditSink
from kendra_api.config import Settings
from kendra_api.main import create_app

pytestmark = pytest.mark.milestone12


def _app():
    # No collaborators wired at all: the default EmptyRetriever/UnavailableAnswerModel/
    # EmptySourceRegistry give a fail-closed `insufficient_evidence` for any question,
    # so the header's own validation is the only thing under test here.
    settings = Settings(_env_file=None, postgres_password="header-test")  # type: ignore[call-arg]
    app = create_app(settings, probes=[])
    app.dependency_overrides[deps.get_audit_sink] = lambda: InMemoryAuditSink()
    return app


async def _post(client: httpx.AsyncClient, *, evaluation_run_id: str | None):
    headers = {}
    if evaluation_run_id is not None:
        headers["X-Kendra-Evaluation-Run-Id"] = evaluation_run_id
    return await client.post(
        "/api/v1/questions",
        json={"question": "irrelevant?", "collection_id": "default"},
        headers=headers,
    )


async def test_absent_header_is_accepted():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_app()), base_url="http://testserver"
    ) as client:
        response = await _post(client, evaluation_run_id=None)
    assert response.status_code == 200


async def test_well_formed_header_is_accepted():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_app()), base_url="http://testserver"
    ) as client:
        response = await _post(client, evaluation_run_id="eval-09875fbc-9543-4ad9")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "bad_value",
    [
        "x" * 129,  # over length
        "has a space",
        "has\nnewline",
        "semi;colon",
        "<script>alert(1)</script>",
        "",
    ],
    ids=["too_long", "space", "newline", "semicolon", "markup", "empty_string"],
)
async def test_malformed_header_is_rejected_with_422(bad_value):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_app()), base_url="http://testserver"
    ) as client:
        response = await _post(client, evaluation_run_id=bad_value)
    assert response.status_code == 422
