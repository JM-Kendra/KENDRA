"""Answering records and the wire contract from MVP_SPEC Section 7.

Nothing here is authoritative evidence. Every field the client sees is either
model-authored prose that survived validation, or a value the API read from its
own records. The model never supplies source metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

# MVP_SPEC Step 12 / Section 7.3. Immutable contract text, exactly 51 ASCII characters.
EXACT_UNSUPPORTED_ANSWER = "Insufficient information in the uploaded documents."

AnswerStatus = Literal[
    "supported",
    "insufficient_evidence",
    "conflicting_evidence",
    "source_unavailable",
    "system_error",
]

MODEL_STATUSES = frozenset({"supported", "insufficient_evidence", "conflicting_evidence"})


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Server-owned identity for one admitted document version."""

    document_id: str
    version_id: str
    filename: str
    sha256: str
    page_count: int


@dataclass(frozen=True, slots=True)
class Evidence:
    """One retrieved candidate. `evidence_id` is opaque and request-scoped: it is the
    only handle the model is given, so a model cannot name a document or a page."""

    evidence_id: str
    text: str
    document_id: str
    version_id: str
    filename: str
    page: int
    chunk_id: str
    source_sha256: str
    processing_run_id: str
    extraction_method: str
    generation_id: str


class QuestionRequest(BaseModel):
    """MVP_SPEC 7.1 accepts these two fields and no others."""

    model_config = {"extra": "forbid"}

    question: str = Field(min_length=1, max_length=4_000)
    collection_id: str = Field(min_length=1, max_length=200)


class Citation(BaseModel):
    citation_id: str
    claim_id: str
    document_id: str
    version_id: str
    source_sha256: str
    filename: str
    page: int
    excerpt: str
    chunk_id: str
    extraction_method: str
    processing_run_id: str
    pipeline_git_revision: str
    source_url: str


class Claim(BaseModel):
    claim_id: str
    text: str
    citation_ids: list[str]


class AnswerResponse(BaseModel):
    request_id: str
    status: AnswerStatus
    answer: str
    claims: list[Claim] = []
    citations: list[Citation] = []
    limitations: list[str] = []
