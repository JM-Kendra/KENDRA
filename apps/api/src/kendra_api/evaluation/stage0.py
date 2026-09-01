"""EXP-11 draft, Section 4 — Stage 0 diagnostic classification.

Distinguishes, for a case whose external result is `insufficient_evidence`,
whether that is because the model itself declined (`model-abstained`), the
answering contract's own gate discarded an attempted answer (`gate-rejected`),
the model's raw output could not be parsed against the schema
(`schema-invalid`), a different status was returned or every candidate failed
admission (`other`), or the case did not even reproduce the reference result
under replay (`not-reproduced`).

Calls `kendra_api.answering.service.answer_question()` directly, in-process —
never through the API or the HTTP evaluation client — exactly as
`kendra_api.evaluation.fake_model` already does for the hermetic M12 test tier,
substituting a real model for its scripted one. The `audit` argument passed to
`answer_question()` is always an `InMemoryAuditSink`: `answer_question()` has a
hard invariant that every call writes exactly one audit record before
returning, and this module must never let one reach the real Postgres
`question_audit` table. Every read this module performs (admission checks
against `document_versions`/`index_generations`) is a plain `SELECT`; nothing
here writes to a real table.

This is diagnostic-only. It does not decide `answer_question()`'s real
outcome — that remains authoritative and unmodified — it only re-derives, from
the same private helpers `_run_pipeline` itself uses (`_parse_model_output`,
`_admit`), a finer-grained label than the external status alone carries. See
`evaluation/EXP-11_PREREG_DRAFT.md` Section 4 for the frozen classification
mapping this module implements.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Literal

from kendra_api.answering.model_client import AnswerModel
from kendra_api.answering.models import Evidence
from kendra_api.answering.retrieval import Retriever
from kendra_api.answering.service import MAX_CLAIMS, _admit, _parse_model_output, answer_question
from kendra_api.answering.sources import SourceRegistry
from kendra_api.audit.sink import InMemoryAuditSink

Classification = Literal["model-abstained", "gate-rejected", "schema-invalid", "other", "not-reproduced"]

# The frozen mapping from EXP-11_PREREG_DRAFT.md Section 4 -- but only for the
# branches of `_run_pipeline` that produce the SAME external status as our
# candidate cases' reference ("insufficient_evidence" via `_unsupported()`):
# admission failing outright, the model itself declaring insufficient
# evidence, and every claim-level gate rejection all return
# "insufficient_evidence" through that one helper.
#
# Every other branch returns a DIFFERENT external status --
# "source_unavailable" (503), "system_error" (a raised exception, or
# `_parse_model_output` returning None), "conflicting_evidence", or
# "supported" -- so any case reaching one of those can never satisfy the
# reproduction criterion against a reference of "insufficient_evidence" in the
# first place; `classify_case` already resolves it to "not-reproduced" before
# this table is ever consulted. `schema-invalid` stays a defined
# `Classification` value for a case set whose reference status is something
# other than "insufficient_evidence" (this module's `reference_status`
# parameter is not hardcoded), but it is *not reachable* through this table
# for the reference this project's EXP-11 draft actually uses -- confirmed by
# `test_scripted_schema_invalid` in `apps/api/tests/test_stage0.py`, which
# initially assumed the opposite and had to be corrected against the real
# code.
_BRANCH_CLASSIFICATION: dict[str, Classification] = {
    "admission_failed": "other",
    "insufficient_evidence_from_model": "model-abstained",
    "claims_empty_or_oversized": "gate-rejected",
    "claim_not_dict": "gate-rejected",
    "claim_missing_text": "gate-rejected",
    "claim_missing_evidence_ids": "gate-rejected",
    "claim_unknown_evidence_id": "gate-rejected",
}


class _FrozenEvidenceRetriever:
    """Stage 0's retrieval stand-in: always returns exactly the evidence
    captured for one case, regardless of the question or collection_id passed
    in. No live Qdrant query, no live embedding call — matches
    `kendra_api.evaluation.fake_model`'s `_StaticRetriever` shape."""

    def __init__(self, evidence: list[Evidence]) -> None:
        self._evidence = list(evidence)

    async def retrieve(self, question: str, collection_id: str) -> list[Evidence]:  # noqa: ARG002
        return list(self._evidence)


class _RecordingModel:
    """Wraps a real `AnswerModel` and records the raw string it returns,
    without altering behavior. Stage 0 needs the model's raw output for
    diagnosis; `answer_question()` itself never exposes it."""

    def __init__(self, inner: AnswerModel) -> None:
        self._inner = inner
        self.raw_output: str | None = None

    async def generate(self, question: str, evidence: list[Evidence]) -> str:
        raw = await self._inner.generate(question, evidence)
        self.raw_output = raw
        return raw


@dataclasses.dataclass(frozen=True, slots=True)
class Stage0CaseResult:
    """One case's complete Stage 0 outcome. Written verbatim to
    `stage0_cases.jsonl`."""

    case_id: str
    reproduced: bool
    raw_model_output: str | None
    schema_valid: bool | None
    gate_decision: str
    final_status: str
    classification: Classification


async def _determine_branch(
    *, raw: str | None, evidence: list[Evidence], registry: SourceRegistry
) -> tuple[str, bool | None]:
    """Re-derives which `_run_pipeline` branch produced `raw`, using the same
    private helpers `_run_pipeline` itself calls (not a reimplementation of
    their logic). Returns (branch, schema_valid)."""
    admitted, unresolved_source = await _admit(list(evidence), registry)
    if not admitted:
        return ("source_unavailable" if unresolved_source else "admission_failed", None)

    if raw is None:
        return "model_call_failed", None

    payload = _parse_model_output(raw)
    if payload is None:
        return "schema_invalid", False

    status = payload["status"]
    if status == "insufficient_evidence":
        return "insufficient_evidence_from_model", True
    if status == "conflicting_evidence":
        return "conflicting_evidence_returned", True

    # status == "supported"
    admitted_by_id = {item.evidence_id for item, _ in admitted}
    raw_claims = payload.get("claims")
    if not raw_claims or len(raw_claims) > MAX_CLAIMS:
        return "claims_empty_or_oversized", True
    for raw_claim in raw_claims:
        if not isinstance(raw_claim, dict):
            return "claim_not_dict", True
        text = raw_claim.get("text")
        if not isinstance(text, str) or not text.strip():
            return "claim_missing_text", True
        evidence_ids = raw_claim.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            return "claim_missing_evidence_ids", True
        for evidence_id in evidence_ids:
            if not isinstance(evidence_id, str) or evidence_id not in admitted_by_id:
                return "claim_unknown_evidence_id", True
    return "answered_supported", True


async def classify_case(
    *,
    case_id: str,
    question: str,
    evidence: list[Evidence],
    reference_status: str,
    model: AnswerModel,
    registry: SourceRegistry,
    pipeline_git_revision: str,
    source_revision: str,
    source_revision_dirty: bool,
    answer_model_name: str,
    embedding_model_name: str,
    evaluation_run_id: str | None = None,
) -> Stage0CaseResult:
    """Runs one case through the real answering contract, in-process, against
    frozen evidence, and classifies the result. `reference_status` is the
    `response_status` the case's original live run recorded — reproduction is
    checked against exactly that value, not hardcoded to
    `"insufficient_evidence"`, so this also works for a case whose reference
    status was something else.

    The `audit` sink passed to `answer_question()` is always a fresh, private
    `InMemoryAuditSink` — its one record is discarded when this function
    returns; nothing is written to any persisted table."""
    retriever: Retriever = _FrozenEvidenceRetriever(evidence)
    recording_model = _RecordingModel(model)
    audit = InMemoryAuditSink()

    outcome = await answer_question(
        question=question,
        collection_id="default",
        retriever=retriever,
        model=recording_model,
        registry=registry,
        pipeline_git_revision=pipeline_git_revision,
        audit=audit,
        source_revision=source_revision,
        source_revision_dirty=source_revision_dirty,
        answer_model_name=answer_model_name,
        embedding_model_name=embedding_model_name,
        evaluation_run_id=evaluation_run_id,
    )

    final_status = outcome.response.status
    reproduced = final_status == reference_status

    branch, schema_valid = await _determine_branch(
        raw=recording_model.raw_output, evidence=evidence, registry=registry
    )

    classification: Classification = (
        "not-reproduced" if not reproduced else _BRANCH_CLASSIFICATION.get(branch, "other")
    )

    return Stage0CaseResult(
        case_id=case_id,
        reproduced=reproduced,
        raw_model_output=recording_model.raw_output,
        schema_valid=schema_valid,
        gate_decision=branch,
        final_status=final_status,
        classification=classification,
    )


def write_stage0_cases(run_dir: Path, results: list[Stage0CaseResult]) -> None:
    """Writes `stage0_cases.jsonl` under `run_dir` (expected to be inside
    `evaluation/runs/EXP-11/<run-id>/`, already git-ignored)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "stage0_cases.jsonl").open("w", encoding="utf-8") as stream:
        for result in results:
            stream.write(json.dumps(dataclasses.asdict(result), sort_keys=True) + "\n")
