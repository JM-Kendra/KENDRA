"""Preflight gates (Section 5). Any failure raises `PreflightError` with one clear
line; the runner exits non-zero rather than producing a report of "unsupported"
results against a system that was never actually ready (Section 2.6)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import httpx

from kendra_api.evaluation.models import PreflightError


async def check_api_health(client: httpx.AsyncClient, *, allow_unknown_revision: bool = False) -> dict:
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
    if not allow_unknown_revision:
        # Invariant 2: a citation must carry a stable producing pipeline/Git
        # revision. A run whose citations are meant to be relied on must not start
        # from a source_revision the deployment itself couldn't resolve, or from a
        # working tree with uncommitted changes the citation's revision can't
        # actually reproduce.
        if body.get("source_revision") in (None, "unknown"):
            raise PreflightError(
                "source_revision is 'unknown' — citations from this run would not "
                "resolve to a real pipeline revision (invariant 2); export "
                "KENDRA_SOURCE_REVISION on the deployment host, or pass "
                "--allow-unknown-revision to run anyway"
            )
        if body.get("source_revision_dirty"):
            raise PreflightError(
                "source_revision_dirty is true — the deployment has uncommitted "
                "changes, so this run's revision would not reproduce what was "
                "actually served; commit or stash them, or pass "
                "--allow-unknown-revision to run anyway"
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


def check_source_revision_matches_head(
    health_body: dict, *, repo_root: Path, allow_mismatch: bool
) -> bool:
    """`docs/incidents/INC-001-ghost-evaluation-runs.md`: a run's citations and
    audit records are only trustworthy against the code that actually served
    them. A stale baked `KENDRA_SOURCE_REVISION` (an image built before the
    latest commit landed) would silently produce a run whose recorded revision
    does not match the code the deployment is actually running.

    Returns `True` if a mismatch was found and overridden (the caller should
    record this in the run's report), `False` if the two matched cleanly.
    Raises `PreflightError` on a mismatch unless `allow_mismatch` is set."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PreflightError(f"could not run 'git rev-parse HEAD' at {repo_root}: {exc}") from None
    if completed.returncode != 0:
        raise PreflightError(
            f"'git rev-parse HEAD' failed at {repo_root}: {completed.stderr.strip()}"
        )
    head = completed.stdout.strip()
    reported = health_body.get("source_revision")
    if reported == head:
        return False
    if not allow_mismatch:
        raise PreflightError(
            f"source_revision mismatch: /api/v1/health reports {reported!r}, but "
            f"'git rev-parse HEAD' at {repo_root} is {head!r} -- the deployment's "
            "baked revision does not match the current checkout, so this run's "
            "citations/audit records would carry a stale revision. Rebuild and "
            "recreate the deployment, or pass --allow-revision-mismatch to run "
            "anyway (recorded in the run's report, not silently accepted)"
        )
    return True
