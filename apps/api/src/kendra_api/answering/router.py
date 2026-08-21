"""POST /api/v1/questions (MVP_SPEC Section 7.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from kendra_api.answering.dependencies import (
    get_answer_model,
    get_retriever,
    get_source_registry,
)
from kendra_api.answering.model_client import AnswerModel
from kendra_api.answering.models import AnswerResponse, QuestionRequest
from kendra_api.answering.retrieval import Retriever
from kendra_api.answering.service import answer_question
from kendra_api.answering.sources import SourceRegistry

router = APIRouter(tags=["questions"])


@router.post("/api/v1/questions", response_model=AnswerResponse)
async def ask_question(
    payload: QuestionRequest,
    request: Request,
    retriever: Retriever = Depends(get_retriever),
    model: AnswerModel = Depends(get_answer_model),
    registry: SourceRegistry = Depends(get_source_registry),
) -> JSONResponse:
    outcome = await answer_question(
        question=payload.question,
        collection_id=payload.collection_id,
        retriever=retriever,
        model=model,
        registry=registry,
        pipeline_git_revision=request.app.state.pipeline_git_revision,
    )
    return JSONResponse(
        status_code=outcome.http_status,
        content=outcome.response.model_dump(),
    )
