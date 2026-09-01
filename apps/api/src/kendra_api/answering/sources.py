"""Server-owned source resolution.

ADR-003 requires every retrieval candidate to resolve through PostgreSQL to an
admitted version and checksum before it can support anything. This module is that
resolution step. It is deliberately separate from retrieval so a retriever cannot
vouch for its own candidates.
"""

from __future__ import annotations

from typing import Protocol

from kendra_api.answering.models import SourceRecord
from kendra_api.connections.postgres import PostgresConnection


class SourceRegistry(Protocol):
    async def resolve(self, version_id: str) -> SourceRecord | None: ...

    async def is_active_generation(self, generation_id: str) -> bool: ...

    async def active_collections(self) -> list[str]: ...


class EmptySourceRegistry:
    """Fail-closed default. Resolves nothing, so no answer can be supported.

    This is what an unconfigured deployment gets on purpose: an API that abstains
    is correct, an API that answers from unresolvable text is not.
    """

    async def resolve(self, version_id: str) -> SourceRecord | None:  # noqa: ARG002
        return None

    async def is_active_generation(self, generation_id: str) -> bool:  # noqa: ARG002
        return False

    async def active_collections(self) -> list[str]:
        return []


class InMemorySourceRegistry:
    """Explicit record set. Used by contract tests and by any caller that has
    already resolved versions through another admitted path."""

    def __init__(self, records: list[SourceRecord], active_generation_id: str) -> None:
        self._records = {record.version_id: record for record in records}
        self._active_generation_id = active_generation_id

    @property
    def active_generation_id(self) -> str:
        return self._active_generation_id

    async def resolve(self, version_id: str) -> SourceRecord | None:
        return self._records.get(version_id)

    async def is_active_generation(self, generation_id: str) -> bool:
        return generation_id == self._active_generation_id

    async def active_collections(self) -> list[str]:
        return []


class PostgresSourceRegistry:
    """Resolves against the ingestion registry written in Milestone 9.

    Only versions in state `ready` resolve. A version still processing, or one that
    failed, is not an admitted source.

    Milestone 9 creates one index generation per immutable document version, so
    several generations are active at once. "Active generation" is therefore a
    membership test against `index_generations.state = 'active'`, not equality with
    a single id.
    """

    _SQL = """
        SELECT document_id, version_id, original_filename, sha256, page_count
        FROM document_versions
        WHERE version_id = $1 AND processing_state = 'ready'
    """

    def __init__(self, postgres: PostgresConnection) -> None:
        self._postgres = postgres

    async def resolve(self, version_id: str) -> SourceRecord | None:
        async with self._postgres.connection() as connection:
            row = await connection.fetchrow(self._SQL, version_id)
        if row is None:
            return None
        return SourceRecord(
            document_id=row["document_id"],
            version_id=row["version_id"],
            filename=row["original_filename"],
            sha256=row["sha256"],
            page_count=row["page_count"],
        )

    async def is_active_generation(self, generation_id: str) -> bool:
        async with self._postgres.connection() as connection:
            state = await connection.fetchval(
                "SELECT state FROM index_generations WHERE generation_id = $1",
                generation_id,
            )
        return state == "active"

    async def active_collections(self) -> list[str]:
        async with self._postgres.connection() as connection:
            rows = await connection.fetch(
                "SELECT qdrant_collection FROM index_generations "
                "WHERE state = 'active' AND qdrant_collection IS NOT NULL"
            )
        return [row["qdrant_collection"] for row in rows]
