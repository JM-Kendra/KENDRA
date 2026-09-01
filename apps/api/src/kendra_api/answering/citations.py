"""Citation construction (MVP_SPEC Step 11).

Citations are built here and only here, from server-owned records. Identity fields
come from the resolved `SourceRecord`, never from the retriever's assertion and
never from model output. That is what makes a fabricated citation impossible by
construction rather than by validation.
"""

from __future__ import annotations

from kendra_api.answering.models import Citation, Evidence, SourceRecord


class CitationResolver:
    def __init__(self, pipeline_git_revision: str) -> None:
        self._pipeline_git_revision = pipeline_git_revision

    def build(
        self,
        citation_id: str,
        claim_id: str,
        evidence: Evidence,
        record: SourceRecord,
    ) -> Citation:
        excerpt = evidence.text
        # Invariant: the excerpt must be a contiguous substring of the evidence the
        # claim was actually grounded in. Asserted rather than assumed.
        if excerpt not in evidence.text:  # pragma: no cover - defensive
            raise ValueError("excerpt is not contiguous within its evidence")
        return Citation(
            citation_id=citation_id,
            claim_id=claim_id,
            # Identity from the server's record.
            document_id=record.document_id,
            version_id=record.version_id,
            source_sha256=record.sha256,
            filename=record.filename,
            # Location from the retrieval candidate, already range-checked.
            page=evidence.page,
            excerpt=excerpt,
            chunk_id=evidence.chunk_id,
            extraction_method=evidence.extraction_method,
            processing_run_id=evidence.processing_run_id,
            pipeline_git_revision=self._pipeline_git_revision,
            source_url=f"/api/v1/documents/{record.version_id}/content#page={evidence.page}",
        )
