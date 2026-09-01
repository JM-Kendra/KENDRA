"""Milestone 12 — evaluation runner, live tier. Requires a running API (with
answering enabled) plus Ollama serving the configured answer and embedding models.
Skipped unless KENDRA_M12_LIVE=1, mirroring `milestone10_live` in
test_milestone10_contract.py. Not run by the default `pytest -q` deselection.

    KENDRA_M12_LIVE=1 python -m pytest -m milestone12_live
"""

from __future__ import annotations

import os

import httpx
import pytest

from kendra_api.evaluation.client import http_evaluation_client
from kendra_api.evaluation.preflight import check_api_health, check_ollama_has_models

live = pytest.mark.skipif(
    os.environ.get("KENDRA_M12_LIVE") != "1",
    reason="live tier needs a running, answering-enabled API plus Ollama",
)

API_BASE = os.environ.get("KENDRA_API_BASE", "http://127.0.0.1:8000")
OLLAMA_BASE = os.environ.get("KENDRA_OLLAMA_BASE", "http://127.0.0.1:11434")


@pytest.mark.milestone12_live
@live
async def test_live_api_is_ready_and_answering_enabled():
    client = http_evaluation_client(API_BASE, timeout_seconds=10.0)
    try:
        health = await check_api_health(client.raw)
    finally:
        await client.aclose()

    assert health["answering_enabled"] is True
    assert health["source_revision"] != "unknown"
    assert health["answer_model"]
    assert health["embedding_model"]


@pytest.mark.milestone12_live
@live
async def test_live_ollama_serves_the_configured_models():
    client = http_evaluation_client(API_BASE, timeout_seconds=10.0)
    try:
        health = await check_api_health(client.raw)
    finally:
        await client.aclose()

    ollama_client = httpx.AsyncClient(base_url=OLLAMA_BASE.rstrip("/"), timeout=10.0)
    try:
        await check_ollama_has_models(
            ollama_client,
            answer_model=health["answer_model"],
            embedding_model=health["embedding_model"],
        )
    finally:
        await ollama_client.aclose()
