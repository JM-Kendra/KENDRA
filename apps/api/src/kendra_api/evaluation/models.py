"""Gold-dataset and run-result shapes for the Milestone 12 evaluation runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Phase = Literal["cold", "warm"]
ExpectedResult = Literal["supported", "unsupported"]


class PreflightError(Exception):
    """A fail-loud, single-line preflight gate failure (Section 2.6)."""


@dataclass(frozen=True, slots=True)
class GoldDocument:
    filename: str
    sha256: str
    pages: int
    format_class: str


@dataclass(frozen=True, slots=True)
class GoldCase:
    case_id: str
    category: str
    question: str
    expected_result: ExpectedResult
    expected_answer_facts: list[str]
    authoritative_filenames: list[str]
    expected_pages: dict[str, list[int]]
    unacceptable_answer_behavior: str
    ambiguity_notes: str
    ocr_required: bool


@dataclass(frozen=True, slots=True)
class GoldDataset:
    dataset_id: str
    dataset_status: str
    dataset_sha256: str
    documents: list[GoldDocument]
    cases: list[GoldCase]


@dataclass(frozen=True, slots=True)
class CaseRunResult:
    """One case's complete, preserved outcome. Written verbatim to `cases.jsonl`."""

    case_id: str
    category: str
    ocr_required: bool
    expected_result: ExpectedResult
    predicted_label: Literal["supported", "unsupported"]
    http_status: int
    response_status: str
    answer: str
    citations: list[dict]
    request_id: str | None
    timed_out: bool
    error: str | None
    duration_ms: int
    evaluation_run_id: str


@dataclass(frozen=True, slots=True)
class FactWorksheetEntry:
    case_id: str
    fact: str
    provisional_label: Literal["TP", "FN"]
    reviewed_label: Literal["TP", "FN", "FP"] | None = None


@dataclass
class RunConfig:
    dataset_path: str
    dataset_sha256: str
    dataset_status: str
    source_revision: str
    source_revision_dirty: bool
    answer_model: str
    embedding_model: str
    retrieval_top_k: int | None
    retrieval_score_threshold: float | None
    seed: int
    phase: Phase
    api_base: str
    fake_model: bool
    evaluation_run_id: str
    timestamp_utc: str
