"""Milestone 12 — preflight gates (Section 5), hermetic tier.

Found by external review: preflight accepted a healthy-but-untrustworthy API — one
reporting source_revision="unknown" or source_revision_dirty=true — with no gate.
Invariant 2 requires a citation to carry a real, stable producing-pipeline revision;
a run whose citations are meant to be relied on must refuse to start against either.
"""

from __future__ import annotations

import httpx
import pytest

from kendra_api.evaluation.models import PreflightError
from kendra_api.evaluation.preflight import check_api_health

pytestmark = pytest.mark.milestone12


def _client(body: dict, status_code: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:  # noqa: ARG001
        return httpx.Response(status_code, json=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://api")


READY_BODY = {
    "status": "ready",
    "answering_enabled": True,
    "source_revision": "a" * 40,
    "source_revision_dirty": False,
    "answer_model": "qwen2.5:7b-instruct",
    "embedding_model": "bge-m3",
}


async def test_healthy_ready_response_passes():
    body = await check_api_health(_client(READY_BODY))
    assert body["source_revision"] == "a" * 40


async def test_unknown_revision_is_rejected_by_default():
    body = {**READY_BODY, "source_revision": "unknown"}
    with pytest.raises(PreflightError, match="source_revision is 'unknown'"):
        await check_api_health(_client(body))


async def test_unknown_revision_passes_with_allow_unknown_revision():
    body = {**READY_BODY, "source_revision": "unknown"}
    result = await check_api_health(_client(body), allow_unknown_revision=True)
    assert result["source_revision"] == "unknown"


async def test_dirty_revision_is_rejected_by_default():
    body = {**READY_BODY, "source_revision_dirty": True}
    with pytest.raises(PreflightError, match="source_revision_dirty is true"):
        await check_api_health(_client(body))


async def test_dirty_revision_passes_with_allow_unknown_revision():
    body = {**READY_BODY, "source_revision_dirty": True}
    result = await check_api_health(_client(body), allow_unknown_revision=True)
    assert result["source_revision_dirty"] is True


async def test_not_ready_status_still_fails_regardless_of_allow_unknown_revision():
    body = {**READY_BODY, "status": "not_ready"}
    with pytest.raises(PreflightError, match="not ready"):
        await check_api_health(_client(body, status_code=503), allow_unknown_revision=True)


async def test_answering_disabled_still_fails_regardless_of_allow_unknown_revision():
    body = {**READY_BODY, "answering_enabled": False}
    with pytest.raises(PreflightError, match="answering is disabled"):
        await check_api_health(_client(body), allow_unknown_revision=True)
