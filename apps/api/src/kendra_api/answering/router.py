"""POST /api/v1/questions (MVP_SPEC Section 7.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse

from kendra_api.answering.dependencies import (
    get_answer_model,
    get_audit_sink,
    get_retriever,
    get_source_registry,
)
from kendra_api.answering.model_client import AnswerModel
from kendra_api.answering.models import AnswerResponse, QuestionRequest
from kendra_api.answering.retrieval import Retriever
from kendra_api.answering.service import answer_question
from kendra_api.answering.sources import SourceRegistry
from kendra_api.audit.sink import AuditSink

router = APIRouter(tags=["questions"])


@router.post("/api/v1/questions", response_model=AnswerResponse)
async def ask_question(
    payload: QuestionRequest,
    request: Request,
    retriever: Retriever = Depends(get_retriever),
    model: AnswerModel = Depends(get_answer_model),
    registry: SourceRegistry = Depends(get_source_registry),
    audit: AuditSink = Depends(get_audit_sink),
    # Evaluation-run tagging only — never part of the MVP_SPEC 7.1 request body,
    # which accepts exactly `question` and `collection_id` and no others. An
    # absent or blank header means an ordinary answering request. Constrained to a
    # short opaque token: this value is written verbatim into the append-only,
    # hash-chained audit table, so an unbounded or unvalidated header would let any
    # caller inject arbitrary content into an immutable record.
    evaluation_run_id: str | None = Header(
        default=None,
        alias="X-Kendra-Evaluation-Run-Id",
        pattern=r"^[A-Za-z0-9._-]{1,128}$",
    ),
) -> JSONResponse:
    outcome = await answer_question(
        question=payload.question,
        collection_id=payload.collection_id,
        retriever=retriever,
        model=model,
        registry=registry,
        pipeline_git_revision=request.app.state.pipeline_git_revision,
        audit=audit,
        source_revision=request.app.state.source_revision,
        source_revision_dirty=request.app.state.source_revision_dirty,
        answer_model_name=request.app.state.answer_model_name,
        embedding_model_name=request.app.state.embedding_model_name,
        evaluation_run_id=evaluation_run_id or None,
    )
    return JSONResponse(
        status_code=outcome.http_status,
        content=outcome.response.model_dump(),
    )
