"""PostgreSQL connection seam and readiness probe."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Connection

from kendra_api.config import Settings
from kendra_api.readiness import ProbeResult


class PostgresConnection:
    name = "postgres"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Connection]:
        connection = await asyncpg.connect(
            dsn=self._settings.postgres_dsn,
            timeout=self._settings.readiness_timeout_seconds,
        )
        try:
            yield connection
        finally:
            await connection.close(timeout=self._settings.readiness_timeout_seconds)

    async def check(self) -> ProbeResult:
        try:
            async with self.connection() as connection:
                ready = await connection.fetchval("SELECT 1") == 1
        except Exception:
            return ProbeResult(self.name, False, "unreachable")
        return ProbeResult(self.name, ready, "reachable" if ready else "unreachable")
