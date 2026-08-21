"""Two-stage grounding contract (ADR-003).

Order matters and is enforced here:

  retrieve -> admit through server records -> ask the model -> validate -> build
  citations

Every branch that cannot complete that chain returns a typed non-supported status.
There is no path from model prose to a user-visible answer that skips admission.
"""

from __future__ import annotations

import inspect
import json
import uuid
from dataclasses import dataclass

from kendra_api.answering.citations import CitationResolver
from kendra_api.answering.models import (
    EXACT_UNSUPPORTED_ANSWER,
    MODEL_STATUSES,
    AnswerResponse,
    Citation,
    Claim,
    Evidence,
    SourceRecord,
)
from kendra_api.answering.model_client import AnswerModel
from kendra_api.answering.retrieval import Retriever
from kendra_api.answering.sources import SourceRegistry

MAX_CLAIMS = 20
MAX_CLAIM_CHARS = 2_000


@dataclass(frozen=True, slots=True)
class AnswerOutcome:
    http_status: int
    response: AnswerResponse


async def _maybe_await(value):
    """Retriever and model implementations may be sync or async."""
    if inspect.isawaitable(value):
        return await value
    return value


def _unsupported(request_id: str) -> AnswerOutcome:
    return AnswerOutcome(
        200,
        AnswerResponse(
            request_id=request_id,
            status="insufficient_evidence",
            answer=EXACT_UNSUPPORTED_ANSWER,
            claims=[],
            citations=[],
            limitations=[],
        ),
    )


def _typed_failure(request_id: str, status: str, http_status: int) -> AnswerOutcome:
    # No generated prose, no source or query content — a correlation id only.
    return AnswerOutcome(
        http_status,
        AnswerResponse(
            request_id=request_id,
            status=status,  # type: ignore[arg-type]
            answer="",
            claims=[],
            citations=[],
            limitations=[],
        ),
    )


async def _admit(
    evidence: list[Evidence], registry: SourceRegistry
) -> tuple[list[tuple[Evidence, SourceRecord]], bool]:
    """Resolve candidates against server records.

    Returns admitted pairs and whether any candidate named a version the registry
    could not resolve at all — that is a missing original, not mere irrelevance.
    """
    admitted: list[tuple[Evidence, SourceRecord]] = []
    unresolved_source = False

    for item in evidence:
        record = await _maybe_await(registry.resolve(item.version_id))
        if record is None:
            unresolved_source = True
            continue
        if not await _maybe_await(registry.is_active_generation(item.generation_id)):
            continue  # stale, orphaned, or cross-generation
        if item.source_sha256 != record.sha256:
            continue  # checksum-invalid
        if not isinstance(item.page, int) or item.page < 1 or item.page > record.page_count:
            continue  # page identity is one-based and must exist in the original
        admitted.append((item, record))

    return admitted, unresolved_source


def _parse_model_output(raw: object) -> dict | None:
    """Return a structurally valid payload, or None. Invalid prose is discarded."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    status = payload.get("status")
    if status not in MODEL_STATUSES:
        return None
    claims = payload.get("claims")
    if not isinstance(claims, list):
        return None
    limitations = payload.get("limitations", [])
    if not isinstance(limitations, list):
        return None
    return payload


def _clean_limitations(payload: dict) -> list[str]:
    return [
        item[:MAX_CLAIM_CHARS]
        for item in payload.get("limitations", [])
        if isinstance(item, str)
    ][:MAX_CLAIMS]


async def answer_question(
    *,
    question: str,
    collection_id: str,
    retriever: Retriever,
    model: AnswerModel,
    registry: SourceRegistry,
    pipeline_git_revision: str,
) -> AnswerOutcome:
    request_id = f"req-{uuid.uuid4()}"

    try:
        evidence = await _maybe_await(retriever.retrieve(question, collection_id))
    except Exception:
        return _typed_failure(request_id, "system_error", 500)

    if not evidence:
        # Step 9: no candidate satisfies the rule. The model is never consulted,
        # so it cannot be tempted to fill the gap.
        return _unsupported(request_id)

    try:
        admitted, unresolved_source = await _admit(list(evidence), registry)
    except Exception:
        return _typed_failure(request_id, "system_error", 500)

    if not admitted:
        if unresolved_source:
            # Section 7.4: never present derived text when the original is missing.
            return _typed_failure(request_id, "source_unavailable", 503)
        return _unsupported(request_id)

    admitted_by_id = {item.evidence_id: (item, record) for item, record in admitted}

    try:
        raw = await _maybe_await(model.generate(question, [item for item, _ in admitted]))
    except Exception:
        return _typed_failure(request_id, "system_error", 500)

    payload = _parse_model_output(raw)
    if payload is None:
        return _typed_failure(request_id, "system_error", 500)

    status = payload["status"]

    if status == "insufficient_evidence":
        return _unsupported(request_id)

    resolver = CitationResolver(pipeline_git_revision)

    if status == "conflicting_evidence":
        # Present the competing admitted pages without deciding which controls.
        citations = [
            resolver.build(f"citation-{index + 1}", "", item, record)
            for index, (item, record) in enumerate(admitted)
        ]
        return AnswerOutcome(
            200,
            AnswerResponse(
                request_id=request_id,
                status="conflicting_evidence",
                answer="",
                claims=[],
                citations=citations,
                limitations=_clean_limitations(payload),
            ),
        )

    # status == "supported": every material claim must carry admitted evidence.
    raw_claims = payload["claims"]
    if not raw_claims or len(raw_claims) > MAX_CLAIMS:
        return _unsupported(request_id)

    claims: list[Claim] = []
    citations: list[Citation] = []

    for index, raw_claim in enumerate(raw_claims):
        if not isinstance(raw_claim, dict):
            return _unsupported(request_id)
        text = raw_claim.get("text")
        if not isinstance(text, str) or not text.strip():
            return _unsupported(request_id)
        evidence_ids = raw_claim.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            # An uncited material claim fails the contract.
            return _unsupported(request_id)

        claim_id = f"claim-{index + 1}"
        citation_ids: list[str] = []
        for evidence_id in evidence_ids:
            if not isinstance(evidence_id, str) or evidence_id not in admitted_by_id:
                # Unknown ID: discard the whole response rather than part of it.
                return _unsupported(request_id)
            item, record = admitted_by_id[evidence_id]
            citation_id = f"citation-{len(citations) + 1}"
            citations.append(resolver.build(citation_id, claim_id, item, record))
            citation_ids.append(citation_id)

        # Only `text` and `evidence_ids` are read. Any other key the model emitted —
        # filename, page, checksum, revision — is dropped here and never echoed.
        claims.append(
            Claim(claim_id=claim_id, text=text[:MAX_CLAIM_CHARS], citation_ids=citation_ids)
        )

    return AnswerOutcome(
        200,
        AnswerResponse(
            request_id=request_id,
            status="supported",
            answer=" ".join(claim.text for claim in claims),
            claims=claims,
            citations=citations,
            limitations=_clean_limitations(payload),
        ),
    )
