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
    )
    return JSONResponse(
        status_code=200 if response.status == "ready" else 503,
        content=response.model_dump(mode="json"),
    )
