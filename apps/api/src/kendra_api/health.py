"""Dependency readiness endpoint with a deliberately minimal response."""

import asyncio
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from kendra_api.readiness import ProbeResult, ReadinessCode, ReadinessProbe


router = APIRouter(tags=["health"])


class ServiceReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "not_ready"]
    code: ReadinessCode


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "not_ready"]
    services: dict[str, ServiceReadiness]
    source_revision: str
    source_revision_dirty: bool
    release_tag: str
    answering_enabled: bool
    answer_model: str
    embedding_model: str
    retrieval_top_k: int
    retrieval_score_threshold: float


async def _safe_check(probe: ReadinessProbe) -> ProbeResult:
    try:
        return await probe.check()
    except Exception:
        return ProbeResult(probe.name, False, "unavailable")


@router.get("/api/v1/health", response_model=HealthResponse)
async def health(request: Request) -> JSONResponse:
    results = await asyncio.gather(
        *(_safe_check(probe) for probe in request.app.state.readiness_probes)
    )
    services = {
        result.service: ServiceReadiness(
            status="ready" if result.ready else "not_ready",
            code=result.code,
        )
        for result in results
    }
    response = HealthResponse(
        status="ready" if all(result.ready for result in results) else "not_ready",
        services=services,
        source_revision=request.app.state.source_revision,
        source_revision_dirty=request.app.state.source_revision_dirty,
        release_tag=request.app.state.release_tag,
        answering_enabled=request.app.state.answering_enabled,
        answer_model=request.app.state.answer_model_name,
        embedding_model=request.app.state.embedding_model_name,
        retrieval_top_k=request.app.state.retrieval_top_k,
        retrieval_score_threshold=request.app.state.retrieval_score_threshold,
    )
    return JSONResponse(
        status_code=200 if response.status == "ready" else 503,
        content=response.model_dump(mode="json"),
    )
