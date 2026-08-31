"""Milestone 12 — append-only question-audit records (Section 3)."""

from __future__ import annotations

import dataclasses
import json

import httpx
import pytest

from kendra_api.answering.model_client import OllamaAnswerModel
from kendra_api.answering.models import Evidence, SourceRecord
from kendra_api.answering.retrieval import EmptyRetriever
from kendra_api.answering.service import answer_question
from kendra_api.answering.sources import InMemorySourceRegistry
from kendra_api.audit.models import AuditRecord, CitedSource
from kendra_api.audit.sink import GENESIS_HASH, InMemoryAuditSink, compute_record_hash

pytestmark = pytest.mark.milestone12

REQUIRED_FIELDS = frozenset(
    {
        "record_id",
        "request_id",
        "timestamp_utc",
        "question",
        "mode",
        "collection_id",
        "selected_document_ids",
        "status",
        "supported",
        "duration_ms",
        "cited",
        "source_revision",
        "source_revision_dirty",
        "answer_model",
        "embedding_model",
        "error_category",
        "evaluation_run_id",
    }
)

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "answer",
        "claims",
        "claim_text",
        "text",
        "excerpt",
        "excerpts",
        "evidence",
        "evidence_text",
        "prompt",
        "raw",
        "raw_output",
        "model_output",
        "reasoning",
        "thinking",
    }
)


def _field_names() -> set[str]:
    return {field.name for field in dataclasses.fields(AuditRecord)}


# --------------------------------------------------------------------------------------
# Schema: the excluded content has nowhere to go, structurally.
# --------------------------------------------------------------------------------------


def test_audit_record_has_exactly_the_required_fields():
    assert _field_names() == REQUIRED_FIELDS


def test_audit_record_has_no_field_capable_of_holding_answer_text_or_reasoning():
    assert _field_names() & FORBIDDEN_FIELD_NAMES == set()


# --------------------------------------------------------------------------------------
# Hash chain.
# --------------------------------------------------------------------------------------


def _record(**overrides) -> AuditRecord:
    from datetime import UTC, datetime

    defaults = dict(
        record_id="rec-1",
        request_id="req-1",
        timestamp_utc=datetime(2026, 8, 31, tzinfo=UTC),
        question="When was it issued?",
        mode="answer",
        collection_id="default",
        selected_document_ids=None,
        status="insufficient_evidence",
        supported=False,
        duration_ms=12,
        cited=[],
        source_revision="a" * 40,
        source_revision_dirty=False,
        answer_model="qwen2.5:7b-instruct",
        embedding_model="bge-m3",
        error_category=None,
        evaluation_run_id=None,
    )
    defaults.update(overrides)
    return AuditRecord(**defaults)


async def test_hash_chain_starts_from_genesis_and_links_forward():
    sink = InMemoryAuditSink()
    first = _record(record_id="rec-1")
    second = _record(record_id="rec-2")

    await sink.write(first)
    await sink.write(second)

    assert sink.record_hashes[0] == compute_record_hash(first, GENESIS_HASH)
    assert sink.record_hashes[1] == compute_record_hash(second, sink.record_hashes[0])
    assert sink.record_hashes[0] != sink.record_hashes[1]


async def test_hash_changes_if_any_field_differs():
    sink = InMemoryAuditSink()
    await sink.write(_record(record_id="rec-1", duration_ms=12))
    baseline = sink.record_hashes[0]

    other_sink = InMemoryAuditSink()
    await other_sink.write(_record(record_id="rec-1", duration_ms=13))
    assert other_sink.record_hashes[0] != baseline


# --------------------------------------------------------------------------------------
# Every path out of `answer_question` writes exactly one record.
# --------------------------------------------------------------------------------------


class _RaisingRetriever:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def retrieve(self, question: str, collection_id: str):  # noqa: ARG002
        raise self._exc


class _RaisingModel:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def generate(self, question: str, evidence):  # noqa: ARG002
        raise self._exc


class _RaisingRegistry:
    async def resolve(self, version_id: str):  # noqa: ARG002
        raise RuntimeError("registry boom")

    async def is_active_generation(self, generation_id: str) -> bool:  # noqa: ARG002
        return False

    async def active_collections(self) -> list[str]:
        return []


class _StaticModel:
    def __init__(self, payload: dict | None = None, raw: str | None = None) -> None:
        self._payload = payload
        self._raw = raw

    async def generate(self, question: str, evidence):  # noqa: ARG002
        if self._raw is not None:
            return self._raw
        return json.dumps(self._payload)


class _StaticRetriever:
    def __init__(self, evidence: list[Evidence]) -> None:
        self._evidence = evidence

    async def retrieve(self, question: str, collection_id: str):  # noqa: ARG002
        return list(self._evidence)


COMMON_KWARGS = dict(
    question="When was it issued?",
    collection_id="default",
    pipeline_git_revision="a" * 40,
    source_revision="a" * 40,
    source_revision_dirty=False,
    answer_model_name="qwen2.5:7b-instruct",
    embedding_model_name="bge-m3",
)


async def test_no_evidence_writes_exactly_one_record():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=EmptyRetriever(),
        model=_StaticModel(payload={"status": "insufficient_evidence", "claims": [], "limitations": []}),
        registry=InMemorySourceRegistry([], active_generation_id="gen"),
        audit=sink,
        **COMMON_KWARGS,
    )
    assert len(sink.records) == 1
    assert sink.records[0].status == "insufficient_evidence"
    assert sink.records[0].error_category is None


async def test_retriever_exception_writes_one_record_with_retrieval_unavailable():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=_RaisingRetriever(RuntimeError("connection refused")),
        model=_StaticModel(payload={"status": "insufficient_evidence", "claims": [], "limitations": []}),
        registry=InMemorySourceRegistry([], active_generation_id="gen"),
        audit=sink,
        **COMMON_KWARGS,
    )
    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.status == "system_error"
    assert record.error_category == "retrieval_unavailable"


async def test_retriever_timeout_is_classified_as_timeout():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=_RaisingRetriever(TimeoutError("retrieval timed out")),
        model=_StaticModel(payload={"status": "insufficient_evidence", "claims": [], "limitations": []}),
        registry=InMemorySourceRegistry([], active_generation_id="gen"),
        audit=sink,
        **COMMON_KWARGS,
    )
    assert sink.records[0].error_category == "timeout"


EVIDENCE = [
    Evidence(
        evidence_id="ev-1",
        text="Synthetic fixture sentence.",
        document_id="doc-1",
        version_id="ver-1",
        filename="SYNTHETIC.pdf",
        page=1,
        chunk_id="chunk-1",
        source_sha256="a" * 64,
        processing_run_id="run-1",
        extraction_method="pdf_text",
        generation_id="gen-active",
    )
]

REGISTRY = InMemorySourceRegistry(
    [
        SourceRecord(
            document_id="doc-1",
            version_id="ver-1",
            filename="SYNTHETIC.pdf",
            sha256="a" * 64,
            page_count=5,
        )
    ],
    active_generation_id="gen-active",
)


async def test_registry_exception_writes_one_record_with_registry_unresolved():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=_StaticRetriever(EVIDENCE),
        model=_StaticModel(payload={"status": "insufficient_evidence", "claims": [], "limitations": []}),
        registry=_RaisingRegistry(),
        audit=sink,
        **COMMON_KWARGS,
    )
    assert len(sink.records) == 1
    assert sink.records[0].error_category == "registry_unresolved"


async def test_model_exception_writes_one_record_with_model_unavailable():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=_StaticRetriever(EVIDENCE),
        model=_RaisingModel(RuntimeError("model connection refused")),
        registry=REGISTRY,
        audit=sink,
        **COMMON_KWARGS,
    )
    assert len(sink.records) == 1
    assert sink.records[0].error_category == "model_unavailable"


async def test_malformed_model_output_writes_one_record_with_validation_failed():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=_StaticRetriever(EVIDENCE),
        model=_StaticModel(raw="not json"),
        registry=REGISTRY,
        audit=sink,
        **COMMON_KWARGS,
    )
    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.status == "system_error"
    assert record.error_category == "validation_failed"


async def test_supported_answer_audit_has_no_answer_or_claim_text():
    sink = InMemoryAuditSink()
    secret_claim_text = "UNIQUE_MARKER_claim_prose_should_never_be_audited"
    await answer_question(
        retriever=_StaticRetriever(EVIDENCE),
        model=_StaticModel(
            payload={
                "status": "supported",
                "claims": [{"text": secret_claim_text, "evidence_ids": ["ev-1"]}],
                "limitations": [],
            }
        ),
        registry=REGISTRY,
        audit=sink,
        **COMMON_KWARGS,
    )
    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.status == "supported"
    assert record.supported is True
    assert record.cited == [
        CitedSource(document_id="doc-1", version_id="ver-1", filename="SYNTHETIC.pdf", page=1)
    ]
    serialized = json.dumps(dataclasses.asdict(record), default=str)
    assert secret_claim_text not in serialized


async def test_evaluation_run_id_sets_mode_evaluation_and_is_cross_referenced():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=EmptyRetriever(),
        model=_StaticModel(payload={"status": "insufficient_evidence", "claims": [], "limitations": []}),
        registry=InMemorySourceRegistry([], active_generation_id="gen"),
        audit=sink,
        evaluation_run_id="eval-run-42",
        **COMMON_KWARGS,
    )
    record = sink.records[0]
    assert record.mode == "evaluation"
    assert record.evaluation_run_id == "eval-run-42"


async def test_answer_mode_is_the_default_without_an_evaluation_run_id():
    sink = InMemoryAuditSink()
    await answer_question(
        retriever=EmptyRetriever(),
        model=_StaticModel(payload={"status": "insufficient_evidence", "claims": [], "limitations": []}),
        registry=InMemorySourceRegistry([], active_generation_id="gen"),
        audit=sink,
        **COMMON_KWARGS,
    )
    assert sink.records[0].mode == "answer"


# --------------------------------------------------------------------------------------
# Model reasoning ("thinking") is dropped before anything reaches the model client's
# caller, so it never has a chance to be persisted.
# --------------------------------------------------------------------------------------


async def test_ollama_answer_model_drops_the_thinking_field():
    secret_reasoning = "UNIQUE_MARKER_internal_chain_of_thought"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "response": json.dumps(
                    {"status": "insufficient_evidence", "claims": [], "limitations": []}
                ),
                "thinking": secret_reasoning,
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://ollama")
    model = OllamaAnswerModel(base_url="http://ollama", model="qwen2.5:7b-instruct", client=client)

    raw = await model.generate("question?", [])

    assert secret_reasoning not in raw
    await client.aclose()
