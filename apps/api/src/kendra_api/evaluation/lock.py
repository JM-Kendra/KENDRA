"""Run-lock: one evaluation runner invocation at a time.

`docs/incidents/INC-001-ghost-evaluation-runs.md` recorded two live gold-eval
invocations that overlapped, unnoticed, against the same running API and the
same real `question_audit` table -- each client-side process appeared to have
failed (a killed foreground timeout) while the container it had started kept
running to completion underneath. This lock exists to make that specific
failure mode loud instead of silent: a second invocation refuses to start
while a first one's lock file is still on disk.

The lock lives at one fixed path (`evaluation/runs/.lock` by default), not one
per run-id -- serializing the runner as a whole is the point; two runs under
different run-ids overlapping is exactly what happened.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


class RunLockHeld(Exception):
    """Raised when a lock file already exists at the target path."""


@dataclass(frozen=True, slots=True)
class RunLock:
    path: Path
    run_id: str
    container_name: str

    @classmethod
    def acquire(cls, lock_path: Path, *, run_id: str, container_name: str) -> "RunLock":
        """Atomically creates `lock_path`, failing if it already exists.

        `O_CREAT | O_EXCL` makes the existence check and the creation a single
        kernel operation -- no separate `.exists()` check that a concurrent
        invocation could race between checking and creating."""
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            existing = lock_path.read_text(encoding="utf-8")
            raise RunLockHeld(
                f"a run lock already exists at {lock_path}: {existing.strip()} "
                "-- refusing to start a second evaluation run. If the run named "
                "there is confirmed dead (not just slow), remove the lock file "
                "by hand before retrying."
            ) from None
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"run_id": run_id, "container_name": container_name}, stream)
        return cls(path=lock_path, run_id=run_id, container_name=container_name)

    def release(self) -> None:
        """Removes the lock file. Called only on a clean (successful) exit --
        a crash or a killed process is meant to leave the lock in place, so the
        next invocation's `acquire()` surfaces exactly the failure this module
        exists to catch, rather than silently starting a second run."""
        self.path.unlink(missing_ok=True)
