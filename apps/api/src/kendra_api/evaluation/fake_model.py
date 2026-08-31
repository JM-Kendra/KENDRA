"""`--fake-model`: a fully hermetic transport for the evaluation runner.

Builds a real `create_app()` instance wired with dependency overrides — the same
pattern the Milestone 10 contract tests use — and drives it over an in-process
`httpx.ASGITransport`. The client code path (`EvaluationClient`) is identical to a
live run; only the transport and the answering collaborators are fake. No Postgres,
Qdrant, or Ollama is contacted.

Each case is scripted to one of four behaviors, cycling deterministically by index so
a run is reproducible: `good` (a correct, on-contract answer), `bad` (a wrong or
incomplete one — a false answer for unsupported cases, an incomplete one for
supported cases), `timeout` (the model hangs past the request timeout), and
`malformed` (the model returns invalid JSON, which the answering contract must
reject closed).
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

import httpx

from kendra_api.answering import dependencies as deps
from kendra_api.answering.models import Evidence, SourceRecord
from kendra_api.answering.sources import InMemorySourceRegistry
from kendra_api.audit.sink import InMemoryAuditSink
from kendra_api.config import Settings
from kendra_api.evaluation.client import EvaluationClient
from kendra_api.evaluation.models import GoldDataset
from kendra_api.main import create_app

# Weighted cycle rather than an even 4-way split: a run where a quarter of all cases
# hang until the timeout fires would make even the hermetic tier needlessly slow.
# 60% good, 20% bad, 10% timeout, 10% malformed — still guarantees every bucket
# appears at least once across the 50-case gold set.
SCRIPT_BUCKETS = (
    "good",
    "good",
    "good",
    "bad",
    "good",
    "good",
    "bad",
    "timeout",
    "good",
    "malformed",
)


@dataclass(frozen=True, slots=True)
class _CaseFixture:
    evidence: list[Evidence]
    bucket: str
    expected_result: str
    expected_answer_facts: list[str]


class _StaticRetriever:
    def __init__(self, by_question: dict[str, list[Evidence]]) -> None:
        self._by_question = by_question

    async def retrieve(self, question: str, collection_id: str):  # noqa: ARG002
        return list(self._by_question.get(question, []))


class _ScriptedModel:
    def __init__(self, by_question: dict[str, _CaseFixture], *, hang_seconds: float) -> None:
        self._by_question = by_question
        self._hang_seconds = hang_seconds

    async def generate(self, question: str, evidence: list[Evidence]) -> str:
        fixture = self._by_question[question]
        if fixture.bucket == "timeout":
            await asyncio.sleep(self._hang_seconds)
            # Only reached if the client's own timeout did not fire first.
            return json.dumps({"status": "insufficient_evidence", "claims": [], "limitations": []})
        if fixture.bucket == "malformed":
            return "not json at all"
        if fixture.bucket == "good":
            if fixture.expected_result == "unsupported":
                return json.dumps(
                    {"status": "insufficient_evidence", "claims": [], "limitations": []}
                )
            return json.dumps(
                {
                    "status": "supported",
                    "claims": [
                        {
                            "text": " ".join(fixture.expected_answer_facts),
                            "evidence_ids": [item.evidence_id for item in evidence],
                        }
                    ],
                    "limitations": [],
                }
            )
        # "bad"
        if fixture.expected_result == "unsupported":
            return json.dumps(
                {
                    "status": "supported",
                    "claims": [
                        {
                            "text": "A confidently wrong definitive answer.",
                            "evidence_ids": [evidence[0].evidence_id] if evidence else [],
                        }
                    ],
                    "limitations": [],
                }
            )
        return json.dumps(
            {
                "status": "supported",
                "claims": [
                    {
                        "text": "An incorrect and incomplete answer.",
                        "evidence_ids": [evidence[0].evidence_id] if evidence else [],
                    }
                ],
                "limitations": [],
            }
        )


def build_fake_evaluation_client(
    dataset: GoldDataset, *, request_timeout_seconds: float, hang_seconds: float
) -> tuple[EvaluationClient, InMemoryAuditSink]:
    version_by_filename: dict[str, tuple[str, str, SourceRecord]] = {}
    for index, document in enumerate(dataset.documents):
        document_id = f"eval-doc-{index}"
        version_id = f"eval-ver-{index}"
        version_by_filename[document.filename] = (
            document_id,
            version_id,
            SourceRecord(
                document_id=document_id,
                version_id=version_id,
                filename=document.filename,
                sha256=document.sha256,
                page_count=document.pages,
            ),
        )

    evidence_by_question: dict[str, list[Evidence]] = {}
    fixtures_by_question: dict[str, _CaseFixture] = {}
    for index, case in enumerate(dataset.cases):
        bucket = SCRIPT_BUCKETS[index % len(SCRIPT_BUCKETS)]
        evidence: list[Evidence] = []
        if case.expected_result == "supported":
            pages_by_filename = case.expected_pages
        else:
            # Unsupported cases have no expected pages by dataset construction; give
            # the model a plausible but non-answering page from the first
            # authoritative filename so "bad" can exercise a false-answer result.
            pages_by_filename = {case.authoritative_filenames[0]: [1]}
        for sequence, (filename, pages) in enumerate(pages_by_filename.items()):
            document_id, version_id, _ = version_by_filename[filename]
            for page in pages:
                evidence.append(
                    Evidence(
                        evidence_id=f"{case.case_id}-ev-{sequence}-{page}",
                        text=f"Synthetic fixture text for {filename} page {page}.",
                        document_id=document_id,
                        version_id=version_id,
                        filename=filename,
                        page=page,
                        chunk_id=f"{case.case_id}-chunk-{sequence}-{page}",
                        source_sha256=version_by_filename[filename][2].sha256,
                        processing_run_id=f"{case.case_id}-run",
                        extraction_method="pdf_text",
                        generation_id="eval-active",
                    )
                )
        evidence_by_question[case.question] = evidence
        fixtures_by_question[case.question] = _CaseFixture(
            evidence=evidence,
            bucket=bucket,
            expected_result=case.expected_result,
            expected_answer_facts=case.expected_answer_facts,
        )

    registry = InMemorySourceRegistry(
        [record for _, _, record in version_by_filename.values()],
        active_generation_id="eval-active",
    )
    retriever = _StaticRetriever(evidence_by_question)
    model = _ScriptedModel(fixtures_by_question, hang_seconds=hang_seconds)
    audit_sink = InMemoryAuditSink()

    # `answering_enabled` stays at its False default deliberately: the route is
    # registered unconditionally (see `main.py`), and every collaborator below is
    # overridden, so there is no reason to let `create_app` build a real
    # `AsyncQdrantClient`/Ollama embedder that this hermetic path never uses.
    settings = Settings(_env_file=None, postgres_password="fake-model-eval")  # type: ignore[call-arg]
    app = create_app(settings, probes=[])
    app.dependency_overrides[deps.get_retriever] = lambda: retriever
    app.dependency_overrides[deps.get_answer_model] = lambda: model
    app.dependency_overrides[deps.get_source_registry] = lambda: registry
    app.dependency_overrides[deps.get_audit_sink] = lambda: audit_sink

    httpx_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://fake-model-eval",
        timeout=request_timeout_seconds,
    )
    return (
        EvaluationClient(httpx_client, request_timeout_seconds=request_timeout_seconds),
        audit_sink,
    )
