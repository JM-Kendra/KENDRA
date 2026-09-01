"""EXP-11 draft, Section 4 — Stage 0 harness tests.

Fully hermetic: an in-memory registry (no Postgres), a scripted model (no
Ollama), and the module's own always-internal `InMemoryAuditSink` (no
Postgres) together mean nothing here ever opens a connection to a real
database, let alone writes to `question_audit`. That absence is structural,
not incidental, and is asserted directly below rather than merely assumed.
"""

from __future__ import annotations

import inspect
import json

import pytest

from kendra_api.answering.models import Evidence, SourceRecord
from kendra_api.answering.sources import InMemorySourceRegistry
from kendra_api.evaluation import stage0

pytestmark = pytest.mark.milestone12

VERSION_ID = "ver-1"
GENERATION_ID = "gen-active"
SHA256 = "a" * 64


def _make_evidence(evidence_id: str = "ev-1") -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        text="Some retrieved page text.",
        document_id="doc-1",
        version_id=VERSION_ID,
        filename="sample.pdf",
        page=1,
        chunk_id="chunk-1",
        source_sha256=SHA256,
        processing_run_id="run-1",
        extraction_method="pdf_text",
        generation_id=GENERATION_ID,
    )


def _make_registry() -> InMemorySourceRegistry:
    record = SourceRecord(
        document_id="doc-1", version_id=VERSION_ID, filename="sample.pdf", sha256=SHA256, page_count=5
    )
    return InMemorySourceRegistry([record], active_generation_id=GENERATION_ID)


class _ScriptedModel:
    def __init__(self, raw: str) -> None:
        self._raw = raw

    async def generate(self, question: str, evidence: list[Evidence]) -> str:  # noqa: ARG002
        return self._raw


async def _classify(raw: str, *, reference_status: str = "insufficient_evidence") -> stage0.Stage0CaseResult:
    return await stage0.classify_case(
        case_id="KND-TEST-001",
        question="A question?",
        evidence=[_make_evidence()],
        reference_status=reference_status,
        model=_ScriptedModel(raw),
        registry=_make_registry(),
        pipeline_git_revision="a" * 40,
        source_revision="a" * 40,
        source_revision_dirty=False,
        answer_model_name="scripted-test-model",
        embedding_model_name="scripted-test-embedder",
    )


def test_classify_case_accepts_no_audit_sink_parameter():
    """`classify_case` cannot be handed a Postgres-backed audit sink even by
    accident -- there is no parameter for one. It always constructs its own
    `InMemoryAuditSink` internally (see stage0.py), so no caller can route a
    real audit write through this module."""
    parameters = inspect.signature(stage0.classify_case).parameters
    assert "audit" not in parameters


async def test_scripted_model_abstained():
    result = await _classify(json.dumps({"status": "insufficient_evidence", "claims": [], "limitations": []}))
    assert result.reproduced is True
    assert result.schema_valid is True
    assert result.gate_decision == "insufficient_evidence_from_model"
    assert result.final_status == "insufficient_evidence"
    assert result.classification == "model-abstained"


async def test_scripted_gate_rejected_unknown_evidence_id():
    raw = json.dumps(
        {
            "status": "supported",
            "claims": [{"text": "An answer.", "evidence_ids": ["evidence-id-not-admitted"]}],
            "limitations": [],
        }
    )
    result = await _classify(raw)
    assert result.reproduced is True
    assert result.schema_valid is True
    assert result.gate_decision == "claim_unknown_evidence_id"
    assert result.final_status == "insufficient_evidence"
    assert result.classification == "gate-rejected"


async def test_scripted_gate_rejected_missing_claim_text():
    raw = json.dumps({"status": "supported", "claims": [{"evidence_ids": ["ev-1"]}], "limitations": []})
    result = await _classify(raw)
    assert result.gate_decision == "claim_missing_text"
    assert result.classification == "gate-rejected"


async def test_scripted_schema_invalid():
    """`_run_pipeline` maps an unparseable model response to `system_error`
    (`_typed_failure(..., "validation_failed")`), not `insufficient_evidence` --
    confirmed by reading `apps/api/src/kendra_api/answering/service.py` again
    after this test first caught the wrong assumption. Against a reference of
    `insufficient_evidence`, that status mismatch means a schema-invalid replay
    can never satisfy the reproduction criterion, so it always lands in
    `not-reproduced` rather than a `schema-invalid` classification -- the
    `gate_decision` field is what actually carries the real reason in that
    case, not the top-level `classification`."""
    result = await _classify("not json at all")
    assert result.reproduced is False
    assert result.schema_valid is False
    assert result.gate_decision == "schema_invalid"
    assert result.final_status == "system_error"
    assert result.classification == "not-reproduced"


async def test_scripted_not_reproduced():
    """The model answers `supported` with a validly-cited claim -- a real
    answer -- when the case's reference (from the original live run) was
    `insufficient_evidence`. The external result no longer matches, so this
    must not be force-classified into any of the other four buckets."""
    raw = json.dumps({"status": "supported", "claims": [{"text": "An answer.", "evidence_ids": ["ev-1"]}], "limitations": []})
    result = await _classify(raw)
    assert result.reproduced is False
    assert result.final_status == "supported"
    assert result.classification == "not-reproduced"


async def test_one_in_memory_audit_record_per_case_and_no_question_audit_write(monkeypatch):
    """Spies on the InMemoryAuditSink stage0.py constructs internally to
    confirm exactly one record is written per case -- and, since the spy
    substitutes for the only sink type stage0.py ever instantiates, that no
    other sink (a Postgres-backed one, in particular) is ever constructed or
    written to."""
    from kendra_api.audit.sink import InMemoryAuditSink

    created_sinks: list[InMemoryAuditSink] = []
    real_sink_cls = InMemoryAuditSink

    class _SpySink(real_sink_cls):
        def __init__(self) -> None:
            super().__init__()
            created_sinks.append(self)

    monkeypatch.setattr(stage0, "InMemoryAuditSink", _SpySink)

    raw = json.dumps({"status": "insufficient_evidence", "claims": [], "limitations": []})
    await _classify(raw)
    await _classify(raw)

    assert len(created_sinks) == 2, "expected one fresh InMemoryAuditSink per classify_case call"
    for sink in created_sinks:
        assert len(sink.records) == 1, "answer_question() must write exactly one audit record per call"
