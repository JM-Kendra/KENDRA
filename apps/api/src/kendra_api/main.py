"""FastAPI application factory for the Milestone 8 foundation."""

import inspect
from collections.abc import Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kendra_api import __version__
from kendra_api.config import Settings
from kendra_api.connections.ollama import OllamaConnection
from kendra_api.connections.postgres import PostgresConnection
from kendra_api.connections.qdrant import QdrantConnection
from kendra_api.health import router as health_router
from kendra_api.readiness import ReadinessProbe
from kendra_api.storage.local import LocalDocumentStore


def _default_probes(settings: Settings) -> list[ReadinessProbe]:
    return [
        PostgresConnection(settings),
        QdrantConnection(settings),
        OllamaConnection(settings),
        LocalDocumentStore(settings.document_store_root),
    ]


def create_app(
    settings: Settings | None = None,
    probes: Sequence[ReadinessProbe] | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    readiness_probes = list(probes) if probes is not None else _default_probes(resolved_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        for probe in readiness_probes:
            close = getattr(probe, "close", None)
            if close is None:
                continue
            result = close()
            if inspect.isawaitable(result):
                await result

    application = FastAPI(
        title="Kendra API",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.state.readiness_probes = readiness_probes
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_values,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Content-Type"],
    )
    application.include_router(health_router)
    return application


app = create_app()
