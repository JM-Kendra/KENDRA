"""Injection seam for the answering surface.

Defaults are fail-closed on purpose: an API with no retriever, no model, and no
resolvable sources abstains rather than guesses. Deployments and tests override
these; nothing here reaches out to a service at import time.
"""

from __future__ import annotations

from fastapi import Request

from kendra_api.answering.model_client import AnswerModel, UnavailableAnswerModel
from kendra_api.answering.retrieval import EmptyRetriever, Retriever
from kendra_api.answering.sources import EmptySourceRegistry, SourceRegistry


def get_retriever(request: Request) -> Retriever:
    return getattr(request.app.state, "retriever", None) or EmptyRetriever()


def get_answer_model(request: Request) -> AnswerModel:
    return getattr(request.app.state, "answer_model", None) or UnavailableAnswerModel()


def get_source_registry(request: Request) -> SourceRegistry:
    return getattr(request.app.state, "source_registry", None) or EmptySourceRegistry()
