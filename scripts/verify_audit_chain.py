#!/usr/bin/env python3
"""Verify the `question_audit` hash chain against the live database.

Append-only is enforced by a Postgres trigger against `UPDATE`/`DELETE`/`TRUNCATE`,
but that only stops the application role — the database owner (or anyone who can
`ALTER TABLE ... DISABLE TRIGGER`) can still tamper with rows directly. This script
is the actual detection mechanism: it recomputes every record's hash from its
contents and confirms the chain links unbroken from genesis to the latest row.
See `docs/milestones/M12_STATUS.md` for the role-separation limitation this doesn't
close (that's an M14 item).

    python scripts/verify_audit_chain.py
"""

from __future__ import annotations

import asyncio
import sys

from kendra_api.audit.sink import PostgresAuditSink
from kendra_api.config import Settings
from kendra_api.connections.postgres import PostgresConnection


async def _amain() -> int:
    settings = Settings()  # type: ignore[call-arg]
    sink = PostgresAuditSink(PostgresConnection(settings))
    result = await sink.verify_chain()

    if result.ok:
        print(f"PASS: {result.record_count} records, chain verified from genesis")
        return 0

    print(
        f"FAIL: {result.detail} (record {result.first_bad_sequence} of "
        f"{result.record_count})",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    return asyncio.run(_amain())


if __name__ == "__main__":
    raise SystemExit(main())
