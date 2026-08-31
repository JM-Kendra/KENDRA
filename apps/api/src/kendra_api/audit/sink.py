"""Audit persistence seam and the append-only Postgres hash chain.

`AuditSink` mirrors the `Registry` protocol pattern in `ingestion/registry.py`: a
small typed seam so hermetic tests use `InMemoryAuditSink` instead of a live
database, the way Milestone 10 tests use `InMemorySourceRegistry`.

The hash chain: each record's `record_hash` is the SHA-256 of the canonical JSON of
the record (its own hash excluded, since it doesn't exist yet) plus the previous
record's hash. `question_audit` starts from a fixed genesis hash. A Postgres trigger
rejects `UPDATE` and `DELETE` outright, so the only way to falsify history is to break
the hash chain, which a verification pass over the table will always detect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Protocol

from kendra_api.audit.models import AuditRecord, CitedSource
from kendra_api.connections.postgres import PostgresConnection

GENESIS_HASH = "0" * 64

# Distinct from the ingestion registry's advisory lock key (1262834258) so the two
# serialization domains never collide.
_AUDIT_CHAIN_LOCK_KEY = 1262834259

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS question_audit (
    sequence bigserial PRIMARY KEY,
    record_id uuid NOT NULL UNIQUE,
    request_id text NOT NULL,
    timestamp_utc timestamptz NOT NULL,
    question text NOT NULL,
    mode text NOT NULL CHECK (mode IN ('answer','retrieval_only','evaluation')),
    collection_id text NOT NULL,
    selected_document_ids jsonb,
    status text NOT NULL,
    supported boolean NOT NULL,
    duration_ms integer NOT NULL CHECK (duration_ms >= 0),
    cited jsonb NOT NULL,
    source_revision text NOT NULL,
    source_revision_dirty boolean NOT NULL,
    answer_model text NOT NULL,
    embedding_model text NOT NULL,
    error_category text CHECK (
        error_category IS NULL OR error_category IN (
            'timeout','model_unavailable','retrieval_unavailable',
            'registry_unresolved','validation_failed','internal'
        )
    ),
    evaluation_run_id text,
    record_hash char(64) NOT NULL,
    previous_record_hash char(64) NOT NULL
);
CREATE OR REPLACE FUNCTION question_audit_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'question_audit is append-only: % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS question_audit_no_update ON question_audit;
CREATE TRIGGER question_audit_no_update
    BEFORE UPDATE ON question_audit
    FOR EACH ROW EXECUTE FUNCTION question_audit_append_only();
DROP TRIGGER IF EXISTS question_audit_no_delete ON question_audit;
CREATE TRIGGER question_audit_no_delete
    BEFORE DELETE ON question_audit
    FOR EACH ROW EXECUTE FUNCTION question_audit_append_only();
-- TRUNCATE bypasses row-level triggers entirely in Postgres; it needs its own
-- statement-level trigger (TRUNCATE triggers cannot be FOR EACH ROW).
DROP TRIGGER IF EXISTS question_audit_no_truncate ON question_audit;
CREATE TRIGGER question_audit_no_truncate
    BEFORE TRUNCATE ON question_audit
    FOR EACH STATEMENT EXECUTE FUNCTION question_audit_append_only();
"""


def _canonical_json(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )


def compute_record_hash(record: AuditRecord, previous_record_hash: str) -> str:
    payload = asdict(record)
    payload["previous_record_hash"] = previous_record_hash
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


@dataclass(frozen=True, slots=True)
class ChainVerificationResult:
    ok: bool
    record_count: int
    first_bad_sequence: int | None
    detail: str | None


def _verify_sequence(
    entries: list[tuple[AuditRecord, str, str]],
) -> ChainVerificationResult:
    """Shared verification core. `entries` is (record, record_hash,
    previous_record_hash) in ascending write order — one place recomputes the chain
    so `InMemoryAuditSink` and `PostgresAuditSink` cannot silently diverge on what
    "verified" means."""
    expected_previous = GENESIS_HASH
    for position, (record, record_hash, previous_record_hash) in enumerate(entries, start=1):
        if previous_record_hash != expected_previous:
            return ChainVerificationResult(
                False, len(entries), position, f"chain link broken before record {position}"
            )
        if compute_record_hash(record, previous_record_hash) != record_hash:
            return ChainVerificationResult(
                False, len(entries), position, f"record_hash does not match its contents at record {position}"
            )
        expected_previous = record_hash
    return ChainVerificationResult(True, len(entries), None, None)


class AuditSink(Protocol):
    async def initialize(self) -> None: ...

    async def write(self, record: AuditRecord) -> None: ...


class InMemoryAuditSink:
    """Hermetic sink. Keeps the same hash-chain contract as Postgres."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []
        self.record_hashes: list[str] = []
        self.previous_record_hashes: list[str] = []
        self._last_hash = GENESIS_HASH

    async def initialize(self) -> None:
        return None

    async def write(self, record: AuditRecord) -> None:
        previous = self._last_hash
        record_hash = compute_record_hash(record, previous)
        self.records.append(record)
        self.record_hashes.append(record_hash)
        self.previous_record_hashes.append(previous)
        self._last_hash = record_hash

    def verify_chain(self) -> ChainVerificationResult:
        entries = list(zip(self.records, self.record_hashes, self.previous_record_hashes))
        return _verify_sequence(entries)


class PostgresAuditSink:
    def __init__(self, postgres: PostgresConnection) -> None:
        self._postgres = postgres

    async def initialize(self) -> None:
        async with self._postgres.connection() as connection:
            await connection.execute(SCHEMA_SQL)

    async def write(self, record: AuditRecord) -> None:
        async with self._postgres.connection() as connection:
            async with connection.transaction():
                await connection.execute(
                    "SELECT pg_advisory_xact_lock($1)", _AUDIT_CHAIN_LOCK_KEY
                )
                previous_record_hash = (
                    await connection.fetchval(
                        "SELECT record_hash FROM question_audit ORDER BY sequence DESC LIMIT 1"
                    )
                    or GENESIS_HASH
                )
                record_hash = compute_record_hash(record, previous_record_hash)
                await connection.execute(
                    """INSERT INTO question_audit(
                        record_id, request_id, timestamp_utc, question, mode, collection_id,
                        selected_document_ids, status, supported, duration_ms, cited,
                        source_revision, source_revision_dirty, answer_model, embedding_model,
                        error_category, evaluation_run_id, record_hash, previous_record_hash
                    ) VALUES (
                        $1::uuid,$2,$3,$4,$5,$6,$7::jsonb,$8,$9,$10,$11::jsonb,
                        $12,$13,$14,$15,$16,$17,$18,$19
                    )""",
                    record.record_id,
                    record.request_id,
                    record.timestamp_utc,
                    record.question,
                    record.mode,
                    record.collection_id,
                    (
                        json.dumps(record.selected_document_ids)
                        if record.selected_document_ids is not None
                        else None
                    ),
                    record.status,
                    record.supported,
                    record.duration_ms,
                    json.dumps([asdict(item) for item in record.cited]),
                    record.source_revision,
                    record.source_revision_dirty,
                    record.answer_model,
                    record.embedding_model,
                    record.error_category,
                    record.evaluation_run_id,
                    record_hash,
                    previous_record_hash,
                )

    async def verify_chain(self) -> ChainVerificationResult:
        async with self._postgres.connection() as connection:
            rows = await connection.fetch(
                """SELECT record_id, request_id, timestamp_utc, question, mode,
                    collection_id, selected_document_ids, status, supported,
                    duration_ms, cited, source_revision, source_revision_dirty,
                    answer_model, embedding_model, error_category, evaluation_run_id,
                    record_hash, previous_record_hash
                FROM question_audit ORDER BY sequence ASC"""
            )
        entries: list[tuple[AuditRecord, str, str]] = []
        for row in rows:
            record = AuditRecord(
                record_id=str(row["record_id"]),
                request_id=row["request_id"],
                timestamp_utc=row["timestamp_utc"],
                question=row["question"],
                mode=row["mode"],
                collection_id=row["collection_id"],
                selected_document_ids=(
                    json.loads(row["selected_document_ids"])
                    if row["selected_document_ids"] is not None
                    else None
                ),
                status=row["status"],
                supported=row["supported"],
                duration_ms=row["duration_ms"],
                cited=[CitedSource(**item) for item in json.loads(row["cited"])],
                source_revision=row["source_revision"],
                source_revision_dirty=row["source_revision_dirty"],
                answer_model=row["answer_model"],
                embedding_model=row["embedding_model"],
                error_category=row["error_category"],
                evaluation_run_id=row["evaluation_run_id"],
            )
            entries.append((record, row["record_hash"], row["previous_record_hash"]))
        return _verify_sequence(entries)
