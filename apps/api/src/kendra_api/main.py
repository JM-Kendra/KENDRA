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
from kendra_api.answering.router import router as answering_router
from kendra_api.health import router as health_router
from kendra_api.readiness import ReadinessProbe
from kendra_api.storage.local import LocalDocumentStore


def _attach_answering(application: FastAPI, settings: Settings) -> None:
    """Attach the real answering collaborators.

    Only called when KENDRA_ANSWERING_ENABLED is true. Without it the dependency
    defaults stay fail-closed and every question abstains.
    """
    from qdrant_client import AsyncQdrantClient

    from kendra_api.answering.model_client import OllamaAnswerModel
    from kendra_api.answering.retrieval import QdrantRetriever
    from kendra_api.answering.sources import PostgresSourceRegistry
    from kendra_api.ingestion.embedding import OllamaBgeM3Embedder

    postgres = PostgresConnection(settings)
    registry = PostgresSourceRegistry(postgres)
    qdrant = AsyncQdrantClient(
        url=str(settings.qdrant_url),
        api_key=(
            settings.qdrant_api_key.get_secret_value()
            if settings.qdrant_api_key
            else None
        ),
    )
    embedder = OllamaBgeM3Embedder(
        base_url=str(settings.ollama_url),
        model=settings.embedding_model,
        batch_size=settings.embedding_batch_size,
        timeout_seconds=settings.ingestion_tool_timeout_seconds,
    )
    application.state.source_registry = registry
    application.state.retriever = QdrantRetriever(
        client=qdrant,
        embedder=embedder,
        postgres=postgres,
        registry=registry,
        top_k=settings.retrieval_top_k,
        score_threshold=settings.retrieval_score_threshold,
    )
    application.state.answer_model = OllamaAnswerModel(
        base_url=str(settings.ollama_url),
        model=settings.answer_model,
        timeout_seconds=settings.answer_timeout_seconds,
    )


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
    # Required secrets are supplied by BaseSettings from the runtime environment.
    resolved_settings = settings or Settings()  # type: ignore[call-arg]
    readiness_probes = (
        list(probes) if probes is not None else _default_probes(resolved_settings)
    )

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
    application.state.pipeline_git_revision = resolved_settings.pipeline_git_revision
    # Answering collaborators are attached by the deployment (or overridden by tests).
    # Absent them the dependency defaults are fail-closed and the API abstains.
    application.state.retriever = None
    application.state.answer_model = None
    application.state.source_registry = None
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_values,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.include_router(health_router)
    application.include_router(answering_router)
    if resolved_settings.answering_enabled:
        _attach_answering(application, resolved_settings)
    return application
