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


async def test_amain_refuses_to_start_when_the_lock_already_exists(tmp_path, repo_root):
    lock_path = tmp_path / ".lock"
    RunLock.acquire(lock_path, run_id="eval-stale", container_name="kendra-eval-stale")

    exit_code = await _run_fake_model_with_lock(repo_root, tmp_path / "out", lock_path=lock_path)

    assert exit_code == 1
    # Refused before doing anything else: no run directory was created.
    assert not (tmp_path / "out").exists()
    # The stale lock is left exactly as it was -- not silently cleared.
    assert lock_path.is_file()
    assert json.loads(lock_path.read_text())["run_id"] == "eval-stale"


async def test_amain_releases_the_lock_on_a_clean_exit(tmp_path, repo_root):
    lock_path = tmp_path / ".lock"

    exit_code = await _run_fake_model_with_lock(repo_root, tmp_path / "out", lock_path=lock_path)

    assert exit_code == 0
    assert not lock_path.exists()


async def test_amain_never_acquires_the_lock_on_a_preflight_failure(tmp_path, repo_root):
    # Milestone 13 follow-up: a bad dataset sha256 fails preflight (dataset
    # validation), which now runs entirely before the lock is acquired -- a
    # failure here never touched a live run, so it must not leave anything
    # for a human to find and manually clear. This replaces a prior version
    # of this test that asserted the lock *remained* on this same scenario,
    # which was the bug docs/DOST_DEMO.md's recovery drill exposed: a runner
    # retry after an unrelated preflight failure had to manually confirm and
    # remove a stale lock that never protected an in-flight run.
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
    assert not lock_path.exists()


async def test_amain_leaves_the_lock_in_place_on_a_genuine_mid_run_failure(tmp_path, repo_root):
    # docs/incidents/INC-001-ghost-evaluation-runs.md: once a run has actually
    # begun (preflight passed, lock acquired, cases in flight), a crash or a
    # killed process must leave the lock in place on purpose so the failure
    # is loud, not silent. This must not regress even after Milestone 13's
    # reordering moved preflight ahead of lock acquisition. Simulated here
    # with a --scored-worksheet path that does not exist: preflight and the
    # entire case-asking loop complete successfully (the lock is acquired and
    # would normally be released next), but loading the worksheet afterward
    # raises before lock.release() is ever reached.
    lock_path = tmp_path / ".lock"
    missing_worksheet = tmp_path / "does-not-exist.json"
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
        str(tmp_path / "out"),
        "--seed",
        "7",
        "--lock-path",
        str(lock_path),
        "--scored-worksheet",
        str(missing_worksheet),
    ]
    args = parse_args(argv)

    with pytest.raises(FileNotFoundError):
        await _amain(args)

    assert lock_path.is_file()
