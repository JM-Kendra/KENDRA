"""PostgreSQL registry and publication-state coordinator."""

from typing import Protocol

from kendra_api.connections.postgres import PostgresConnection
from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import (
    ChunkRecord,
    DocumentIdentity,
    ExistingVersion,
    IntakeManifest,
    PageRecord,
    ProcessingState,
    StoredVersion,
    ValidatedPdf,
)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    document_id text PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS document_versions (
    version_id text PRIMARY KEY,
    document_id text NOT NULL REFERENCES documents(document_id),
    sha256 char(64) NOT NULL UNIQUE,
    byte_length bigint NOT NULL CHECK (byte_length > 0),
    media_type text NOT NULL,
    original_filename text NOT NULL,
    safe_filename text NOT NULL,
    logical_uri text NOT NULL UNIQUE,
    manifest_uri text NOT NULL UNIQUE,
    provenance_reference text NOT NULL,
    approval_scope text NOT NULL,
    page_count integer NOT NULL CHECK (page_count > 0),
    processing_state text NOT NULL CHECK (processing_state IN ('processing','ready','failed')),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS processing_runs (
    processing_run_id text PRIMARY KEY,
    ingestion_id text NOT NULL UNIQUE,
    version_id text NOT NULL REFERENCES document_versions(version_id),
    source_sha256 char(64) NOT NULL,
    pipeline_revision text NOT NULL,
    extractor_identity text NOT NULL,
    embedding_model text NOT NULL,
    state text NOT NULL CHECK (state IN ('processing','ready','failed')),
    error_code text,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);
CREATE TABLE IF NOT EXISTS pages (
    version_id text NOT NULL REFERENCES document_versions(version_id),
    processing_run_id text NOT NULL REFERENCES processing_runs(processing_run_id),
    page_number integer NOT NULL CHECK (page_number > 0),
    text text NOT NULL,
    extraction_method text NOT NULL,
    quality_result text NOT NULL,
    docling_text_chars integer NOT NULL CHECK (docling_text_chars >= 0),
    PRIMARY KEY (processing_run_id, page_number)
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id uuid PRIMARY KEY,
    version_id text NOT NULL REFERENCES document_versions(version_id),
    source_sha256 char(64) NOT NULL,
    processing_run_id text NOT NULL REFERENCES processing_runs(processing_run_id),
    page_number integer NOT NULL,
    sequence integer NOT NULL CHECK (sequence >= 0),
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    text text NOT NULL,
    extraction_method text NOT NULL,
    content_sha256 char(64) NOT NULL,
    chunker_version text NOT NULL,
    UNIQUE (processing_run_id, page_number, sequence),
    FOREIGN KEY (processing_run_id, page_number) REFERENCES pages(processing_run_id, page_number)
);
CREATE TABLE IF NOT EXISTS index_generations (
    generation_id text PRIMARY KEY,
    processing_run_id text NOT NULL UNIQUE REFERENCES processing_runs(processing_run_id),
    qdrant_collection text,
    state text NOT NULL CHECK (state IN ('processing','active','retired','failed')),
    published_at timestamptz
);
-- Milestone 9 creates one generation per immutable document version. Multiple
-- documents must therefore remain independently active.
DROP INDEX IF EXISTS one_active_ingestion_generation;
"""


class Registry(Protocol):
    async def initialize(self) -> None: ...
    async def find_by_checksum(self, sha256: str) -> ExistingVersion | None: ...
    async def begin_processing(
        self,
        identity: DocumentIdentity,
        validated: ValidatedPdf,
        intake: IntakeManifest,
        stored: StoredVersion,
        pipeline_revision: str,
        extractor_identity: str,
        embedding_model: str,
    ) -> ExistingVersion | None: ...
    async def save_derived_records(self, pages: list[PageRecord], chunks: list[ChunkRecord]) -> None: ...
    async def mark_ready(self, identity: DocumentIdentity, qdrant_collection: str) -> None: ...
    async def mark_failed(self, identity: DocumentIdentity, error_code: str) -> None: ...


class PostgresRegistry:
    def __init__(self, postgres: PostgresConnection) -> None:
        self._postgres = postgres

    async def initialize(self) -> None:
        async with self._postgres.connection() as connection:
            await connection.execute(SCHEMA_SQL)

    async def find_by_checksum(self, sha256: str) -> ExistingVersion | None:
        async with self._postgres.connection() as connection:
            existing = await connection.fetchrow(
                "SELECT document_id, version_id, sha256, processing_state "
                "FROM document_versions WHERE sha256 = $1",
                sha256,
            )
        if not existing:
            return None
        return ExistingVersion(
            document_id=existing["document_id"],
            version_id=existing["version_id"],
            sha256=existing["sha256"],
            state=ProcessingState(existing["processing_state"]),
        )

    async def begin_processing(
        self,
        identity: DocumentIdentity,
        validated: ValidatedPdf,
        intake: IntakeManifest,
        stored: StoredVersion,
        pipeline_revision: str,
        extractor_identity: str,
        embedding_model: str,
    ) -> ExistingVersion | None:
        async with self._postgres.connection() as connection:
            async with connection.transaction():
                # Serialize the duplicate check/claim across one-off commands.
                await connection.execute("SELECT pg_advisory_xact_lock(1262834258)")
                existing = await connection.fetchrow(
                    "SELECT document_id, version_id, sha256, processing_state "
                    "FROM document_versions WHERE sha256 = $1 FOR SHARE",
                    validated.sha256,
                )
                if existing:
                    return ExistingVersion(
                        document_id=existing["document_id"],
                        version_id=existing["version_id"],
                        sha256=existing["sha256"],
                        state=ProcessingState(existing["processing_state"]),
                    )
                await connection.execute(
                    "INSERT INTO documents(document_id) VALUES($1)", identity.document_id
                )
                await connection.execute(
                    """INSERT INTO document_versions(
                        version_id, document_id, sha256, byte_length, media_type,
                        original_filename, safe_filename, logical_uri, manifest_uri,
                        provenance_reference, approval_scope, page_count, processing_state
                    ) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'processing')""",
                    identity.version_id,
                    identity.document_id,
                    validated.sha256,
                    validated.byte_length,
                    validated.media_type,
                    validated.original_filename,
                    validated.safe_filename,
                    stored.logical_uri,
                    stored.manifest_uri,
                    intake.provenance_reference,
                    intake.approval_scope,
                    validated.page_count,
                )
                await connection.execute(
                    """INSERT INTO processing_runs(
                        processing_run_id, ingestion_id, version_id, source_sha256,
                        pipeline_revision, extractor_identity, embedding_model, state
                    ) VALUES($1,$2,$3,$4,$5,$6,$7,'processing')""",
                    identity.processing_run_id,
                    identity.ingestion_id,
                    identity.version_id,
                    validated.sha256,
                    pipeline_revision,
                    extractor_identity,
                    embedding_model,
                )
                await connection.execute(
                    "INSERT INTO index_generations(generation_id, processing_run_id, state) "
                    "VALUES($1,$2,'processing')",
                    identity.generation_id,
                    identity.processing_run_id,
                )
        return None

    async def save_derived_records(
        self, pages: list[PageRecord], chunks: list[ChunkRecord]
    ) -> None:
        if not pages or not chunks:
            raise IngestionError("empty_derived_records", "no publishable chunks were produced")
        async with self._postgres.connection() as connection:
            async with connection.transaction():
                await connection.executemany(
                    """INSERT INTO pages(
                        version_id, processing_run_id, page_number, text,
                        extraction_method, quality_result, docling_text_chars
                    ) VALUES($1,$2,$3,$4,$5,$6,$7)""",
                    [
                        (
                            page.version_id,
                            page.processing_run_id,
                            page.page_number,
                            page.text,
                            page.extraction_method.value,
                            page.quality_result,
                            page.docling_text_chars,
                        )
                        for page in pages
                    ],
                )
                await connection.executemany(
                    """INSERT INTO chunks(
                        chunk_id, version_id, source_sha256, processing_run_id,
                        page_number, sequence, start_offset, end_offset, text,
                        extraction_method, content_sha256, chunker_version
                    ) VALUES($1::uuid,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)""",
                    [
                        (
                            chunk.chunk_id,
                            chunk.version_id,
                            chunk.source_sha256,
                            chunk.processing_run_id,
                            chunk.page_number,
                            chunk.sequence,
                            chunk.start_offset,
                            chunk.end_offset,
                            chunk.text,
                            chunk.extraction_method.value,
                            chunk.content_sha256,
                            chunk.chunker_version,
                        )
                        for chunk in chunks
                    ],
                )

    async def mark_ready(self, identity: DocumentIdentity, qdrant_collection: str) -> None:
        async with self._postgres.connection() as connection:
            async with connection.transaction():
                generation = await connection.execute(
                    """UPDATE index_generations
                    SET state='active', qdrant_collection=$2, published_at=now()
                    WHERE generation_id=$1 AND state='processing'""",
                    identity.generation_id,
                    qdrant_collection,
                )
                version = await connection.execute(
                    "UPDATE document_versions SET processing_state='ready' "
                    "WHERE version_id=$1 AND processing_state='processing'",
                    identity.version_id,
                )
                run = await connection.execute(
                    "UPDATE processing_runs SET state='ready', completed_at=now() "
                    "WHERE processing_run_id=$1 AND state='processing'",
                    identity.processing_run_id,
                )
                if not all(result.endswith(" 1") for result in (generation, version, run)):
                    raise IngestionError("state_transition_failure", "ready transition was rejected")

    async def mark_failed(self, identity: DocumentIdentity, error_code: str) -> None:
        async with self._postgres.connection() as connection:
            async with connection.transaction():
                await connection.execute(
                    "UPDATE index_generations SET state='failed' "
                    "WHERE generation_id=$1 AND state='processing'",
                    identity.generation_id,
                )
                await connection.execute(
                    "UPDATE document_versions SET processing_state='failed' "
                    "WHERE version_id=$1 AND processing_state='processing'",
                    identity.version_id,
                )
                await connection.execute(
                    "UPDATE processing_runs SET state='failed', error_code=$2, completed_at=now() "
                    "WHERE processing_run_id=$1 AND state='processing'",
                    identity.processing_run_id,
                    error_code,
                )
