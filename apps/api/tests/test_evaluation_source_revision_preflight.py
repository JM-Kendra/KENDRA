"""Milestone 12 — source-revision preflight (`docs/incidents/INC-001-ghost-evaluation-runs.md`).

A run's citations and audit records are only trustworthy against the code that
actually served them. `check_source_revision_matches_head` refuses to run the
live evaluation tier when /api/v1/health's reported `source_revision` does not
equal `git rev-parse HEAD` at the checkout being used -- the exact gap found
when this repo's own api image was rebuilt from an uncommitted tree and kept a
stale baked revision after the real commits landed.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from kendra_api.evaluation.models import PreflightError
from kendra_api.evaluation.preflight import check_source_revision_matches_head

pytestmark = pytest.mark.milestone12


def _repo_root() -> Path:
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
    return Path(completed.stdout.strip())


def _real_head(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_matching_revision_returns_false_and_does_not_raise():
    repo_root = _repo_root()
    head = _real_head(repo_root)

    overridden = check_source_revision_matches_head(
        {"source_revision": head}, repo_root=repo_root, allow_mismatch=False
    )

    assert overridden is False


def test_mismatch_raises_preflight_error_by_default():
    repo_root = _repo_root()

    with pytest.raises(PreflightError, match="source_revision mismatch"):
        check_source_revision_matches_head(
            {"source_revision": "0" * 40}, repo_root=repo_root, allow_mismatch=False
        )


def test_mismatch_with_override_returns_true_instead_of_raising():
    repo_root = _repo_root()

    overridden = check_source_revision_matches_head(
        {"source_revision": "0" * 40}, repo_root=repo_root, allow_mismatch=True
    )

    assert overridden is True


def test_missing_or_unknown_source_revision_is_a_mismatch():
    repo_root = _repo_root()

    with pytest.raises(PreflightError, match="source_revision mismatch"):
        check_source_revision_matches_head(
            {"source_revision": None}, repo_root=repo_root, allow_mismatch=False
        )


def test_repo_root_without_a_git_checkout_fails_loudly(tmp_path):
    with pytest.raises(PreflightError, match="git rev-parse HEAD"):
        check_source_revision_matches_head(
            {"source_revision": "irrelevant"}, repo_root=tmp_path, allow_mismatch=False
        )
