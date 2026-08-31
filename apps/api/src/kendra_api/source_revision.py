"""Single source-revision resolution path.

Consumed by the API at startup (audit, citations, health), by the ingestion CLI, and
by the evaluation runner indirectly (it reads the resolved value back from the API's
own `/api/v1/health` response rather than re-resolving it locally).

Resolution order:

1. `KENDRA_SOURCE_REVISION` env var, if set (must be a full 40-character lowercase
   commit id; an invalid value is a configuration error, not a silent fallback).
2. `git rev-parse HEAD`, if a `.git` directory is reachable from the working directory.
3. `"unknown"` — reported as such rather than as a fabricated all-zero OID.

`KENDRA_SOURCE_REVISION_DIRTY`, if set, overrides the dirty flag outright (the API
container is read-only with no `.git` mounted, so it cannot compute this itself and
must be told). Otherwise the flag is computed from `git status --porcelain` when the
revision was resolved via git, and is `False` when resolved via the env var or left
`"unknown"` — neither of those paths can be evaluated for local working-tree state.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_HEX40_RE = re.compile(r"\A[0-9a-f]{40}\Z")
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


@dataclass(frozen=True, slots=True)
class SourceRevision:
    revision: str
    dirty: bool


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in _TRUE_VALUES


def _git_rev_parse_head(cwd: Path) -> str | None:
    try:
        completed = subprocess.run(  # noqa: S603, S607
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    candidate = completed.stdout.strip().lower()
    return candidate if _HEX40_RE.match(candidate) else None


def _git_is_dirty(cwd: Path) -> bool:
    try:
        completed = subprocess.run(  # noqa: S603, S607
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(completed.stdout.strip())


def resolve_source_revision(*, cwd: Path | str | None = None) -> SourceRevision:
    working_dir = Path(cwd) if cwd is not None else Path.cwd()

    raw_dirty_override = os.environ.get("KENDRA_SOURCE_REVISION_DIRTY")
    dirty_override = _parse_bool(raw_dirty_override) if raw_dirty_override is not None else None

    env_revision = os.environ.get("KENDRA_SOURCE_REVISION")
    if env_revision:
        normalized = env_revision.strip().lower()
        if not _HEX40_RE.match(normalized):
            raise ValueError(
                "KENDRA_SOURCE_REVISION must be a full 40-character lowercase commit id"
            )
        return SourceRevision(normalized, dirty_override if dirty_override is not None else False)

    git_revision = _git_rev_parse_head(working_dir)
    if git_revision is not None:
        dirty = dirty_override if dirty_override is not None else _git_is_dirty(working_dir)
        return SourceRevision(git_revision, dirty)

    return SourceRevision("unknown", dirty_override if dirty_override is not None else False)
