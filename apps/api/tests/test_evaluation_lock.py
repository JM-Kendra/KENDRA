"""Milestone 12 — evaluation runner lock (`docs/incidents/INC-001-ghost-evaluation-runs.md`).

Two invocations of the live gold-eval runner overlapped, unnoticed, against the
same running API and the same real `question_audit` table -- each client-side
process appeared to have failed while the container it started kept running to
completion underneath. `RunLock` exists so a second invocation refuses to start
while a first one's lock is still on disk, and so a crashed/killed run leaves a
lock behind for a human to find rather than silently allowing a concurrent one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kendra_api.evaluation.lock import RunLock, RunLockHeld
from kendra_api.evaluation.run import parse_args, _amain

pytestmark = pytest.mark.milestone12


def test_acquire_creates_a_lock_file_with_run_id_and_container_name(tmp_path):
    lock_path = tmp_path / ".lock"
    lock = RunLock.acquire(lock_path, run_id="eval-abc", container_name="kendra-eval-abc")

    assert lock_path.is_file()
    contents = json.loads(lock_path.read_text(encoding="utf-8"))
    assert contents == {"run_id": "eval-abc", "container_name": "kendra-eval-abc"}


def test_acquire_refuses_to_start_a_second_lock_at_the_same_path(tmp_path):
    lock_path = tmp_path / ".lock"
    RunLock.acquire(lock_path, run_id="eval-first", container_name="kendra-eval-first")

    with pytest.raises(RunLockHeld, match="eval-first"):
        RunLock.acquire(lock_path, run_id="eval-second", container_name="kendra-eval-second")

    # The first lock's contents are untouched by the failed second attempt.
    contents = json.loads(lock_path.read_text(encoding="utf-8"))
    assert contents["run_id"] == "eval-first"


def test_release_removes_the_lock_file(tmp_path):
    lock_path = tmp_path / ".lock"
    lock = RunLock.acquire(lock_path, run_id="eval-abc", container_name="kendra-eval-abc")
    assert lock_path.is_file()

    lock.release()

    assert not lock_path.exists()


def test_release_on_an_already_missing_lock_file_does_not_raise(tmp_path):
    lock_path = tmp_path / ".lock"
    lock = RunLock.acquire(lock_path, run_id="eval-abc", container_name="kendra-eval-abc")
    lock_path.unlink()

    lock.release()  # must not raise on a lock already gone


def test_acquire_creates_parent_directories(tmp_path):
    lock_path = tmp_path / "nested" / "runs" / ".lock"
    RunLock.acquire(lock_path, run_id="eval-abc", container_name="kendra-eval-abc")

    assert lock_path.is_file()


async def _run_fake_model_with_lock(repo_root: Path, tmp_path: Path, *, lock_path: Path):
    argv = [
        "--repo-root",
        str(repo_root),
        "--phase",
        "cold",
        "--fake-model",
        "--fake-model-hang-seconds",
        "0.1",
        "--request-timeout-seconds",
        "0.1",
        "--output-root",
        str(tmp_path),
        "--seed",
        "7",
        "--lock-path",
        str(lock_path),
    ]
    args = parse_args(argv)
    return await _amain(args)


def _repo_root() -> Path:
    import shutil
    import subprocess

    if shutil.which("git") is None:
        pytest.skip("git is not installed in this environment")
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(__file__).resolve().parent,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        pytest.skip("not running inside a git checkout")
    root = Path(completed.stdout.strip())
    if not (root / "evaluation" / "gold_cases.json").exists():
        pytest.skip("evaluation/gold_cases.json not present in this checkout")
    return root


async def test_amain_refuses_to_start_when_the_lock_already_exists(tmp_path):
    repo_root = _repo_root()
    lock_path = tmp_path / ".lock"
    RunLock.acquire(lock_path, run_id="eval-stale", container_name="kendra-eval-stale")

    exit_code = await _run_fake_model_with_lock(repo_root, tmp_path / "out", lock_path=lock_path)

    assert exit_code == 1
    # Refused before doing anything else: no run directory was created.
    assert not (tmp_path / "out").exists()
    # The stale lock is left exactly as it was -- not silently cleared.
    assert lock_path.is_file()
    assert json.loads(lock_path.read_text())["run_id"] == "eval-stale"


async def test_amain_releases_the_lock_on_a_clean_exit(tmp_path):
    repo_root = _repo_root()
    lock_path = tmp_path / ".lock"

    exit_code = await _run_fake_model_with_lock(repo_root, tmp_path / "out", lock_path=lock_path)

    assert exit_code == 0
    assert not lock_path.exists()


async def test_amain_leaves_the_lock_in_place_on_a_preflight_failure(tmp_path):
    # A bad dataset sha256 fails preflight (dataset validation) after the lock is
    # already acquired -- that is not a "clean exit", so the lock must remain.
    repo_root = _repo_root()
    lock_path = tmp_path / ".lock"
    argv = [
        "--repo-root",
        str(repo_root),
        "--phase",
        "cold",
        "--fake-model",
        "--output-root",
        str(tmp_path / "out"),
        "--expect-dataset-sha256",
        "0" * 64,
        "--lock-path",
        str(lock_path),
    ]
    args = parse_args(argv)

    exit_code = await _amain(args)

    assert exit_code == 1
    assert lock_path.is_file()
