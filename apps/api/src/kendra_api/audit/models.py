"""Append-only question-audit record shape (Milestone 12).

`question_audit` records what was asked and how the system behaved. It deliberately
excludes answer text, claim text, evidence text, excerpts, prompts, model raw output,
and model reasoning (`thinking`) — none of those fields exist on `AuditRecord`, so
there is nowhere for them to be persisted even by accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

AuditMode = Literal["answer", "retrieval_only", "evaluation"]

ErrorCategory = Literal[
    "timeout",
    "model_unavailable",
    "retrieval_unavailable",
    "registry_unresolved",
    "validation_failed",
    "internal",
]

ERROR_CATEGORIES: frozenset[str] = frozenset(
    {
        "timeout",
        "model_unavailable",
        "retrieval_unavailable",
        "registry_unresolved",
        "validation_failed",
        "internal",
    }
)


@dataclass(frozen=True, slots=True)
class CitedSource:
    document_id: str
    version_id: str
    filename: str
    page: int


@dataclass(frozen=True, slots=True)
class AuditRecord:
    record_id: str
    request_id: str
    timestamp_utc: datetime
    question: str
    mode: AuditMode
    collection_id: str
    selected_document_ids: list[str] | None
    status: str
    supported: bool
    duration_ms: int
    cited: list[CitedSource]
    source_revision: str
    source_revision_dirty: bool
    answer_model: str
    embedding_model: str
    error_category: ErrorCategory | None
    evaluation_run_id: str | None
