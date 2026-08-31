"""Preflight gates (Section 5). Any failure raises `PreflightError` with one clear
line; the runner exits non-zero rather than producing a report of "unsupported"
results against a system that was never actually ready (Section 2.6)."""

from __future__ import annotations

import httpx

from kendra_api.evaluation.models import PreflightError


async def check_api_health(client: httpx.AsyncClient) -> dict:
    try:
        response = await client.get("/api/v1/health")
    except httpx.HTTPError as exc:
        raise PreflightError(f"API health check failed: {exc}") from None
    try:
        body = response.json()
    except ValueError:
        raise PreflightError("API health response was not valid JSON") from None
    if response.status_code != 200 or body.get("status") != "ready":
        raise PreflightError(
            f"API is not ready: http_status={response.status_code} status={body.get('status')}"
        )
    if not body.get("answering_enabled"):
        raise PreflightError(
            "answering is disabled (answering_enabled=false in /api/v1/health); "
            "set KENDRA_ANSWERING_ENABLED=true and rerun"
        )
    return body


async def check_ollama_has_models(
    client: httpx.AsyncClient, *, answer_model: str, embedding_model: str
) -> None:
    try:
        response = await client.get("/api/tags")
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise PreflightError(f"could not reach Ollama /api/tags: {exc}") from None
    try:
        body = response.json()
    except ValueError:
        raise PreflightError("Ollama /api/tags response was not valid JSON") from None
    names = {model.get("name", "") for model in body.get("models", [])}
    base_names = {name.split(":")[0] for name in names}
    missing = [
        model
        for model in (answer_model, embedding_model)
        if model not in names and model.split(":")[0] not in base_names
    ]
    if missing:
        raise PreflightError(
            f"model(s) not present in Ollama /api/tags: {missing} (have: {sorted(names)})"
        )
