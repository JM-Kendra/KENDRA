"""HTTP client seam for the evaluation runner.

The method requires the timer to start when the question is accepted and stop when
the complete answer and citations are available (`docs/EVALUATION_METHOD.md`, Run
protocol). An in-process call would understate latency, so the runner always talks
HTTP — the only thing `--fake-model` changes is the transport underneath the same
`httpx.AsyncClient`, not the shape of the interaction.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class AskResult:
    http_status: int
    body: dict
    duration_ms: int
    timed_out: bool
    error: str | None


class EvaluationClient:
    def __init__(self, client: httpx.AsyncClient, *, request_timeout_seconds: float | None = None) -> None:
        self._client = client
        # Enforced with `asyncio.wait_for` rather than relying solely on the
        # underlying transport's own timeout handling: `httpx.ASGITransport` (used
        # by `--fake-model`) does not implement one, so a scripted hang would
        # otherwise never time out in the hermetic tier.
        self._request_timeout_seconds = request_timeout_seconds

    async def ask(self, *, question: str, collection_id: str, evaluation_run_id: str) -> AskResult:
        started = time.monotonic()
        try:
            coro = self._client.post(
                "/api/v1/questions",
                json={"question": question, "collection_id": collection_id},
                headers={"X-Kendra-Evaluation-Run-Id": evaluation_run_id},
            )
            if self._request_timeout_seconds is not None:
                response = await asyncio.wait_for(coro, timeout=self._request_timeout_seconds)
            else:
                response = await coro
        except (httpx.TimeoutException, TimeoutError):
            duration_ms = int((time.monotonic() - started) * 1000)
            return AskResult(0, {}, duration_ms, True, "timeout")
        except httpx.HTTPError as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            return AskResult(0, {}, duration_ms, False, f"{type(exc).__name__}: {exc}")

        duration_ms = int((time.monotonic() - started) * 1000)
        try:
            body = response.json()
        except ValueError:
            body = {}
        return AskResult(response.status_code, body, duration_ms, False, None)

    async def health(self) -> dict:
        response = await self._client.get("/api/v1/health")
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()

    @property
    def raw(self) -> httpx.AsyncClient:
        """Escape hatch for preflight checks that need the status code, not just
        the parsed body `health()` returns."""
        return self._client


def http_evaluation_client(api_base: str, timeout_seconds: float) -> EvaluationClient:
    return EvaluationClient(
        httpx.AsyncClient(base_url=api_base.rstrip("/"), timeout=timeout_seconds),
        request_timeout_seconds=timeout_seconds,
    )
