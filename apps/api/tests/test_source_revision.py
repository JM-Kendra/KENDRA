"""Milestone 12 — single source-revision resolution path (Section 4)."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from kendra_api.source_revision import resolve_source_revision

pytestmark = pytest.mark.milestone12


def _real_commit_or_skip() -> str:
    """Several tests below validate `resolve_source_revision()`'s git fallback
    against the actual enclosing checkout, so they need a real `git` binary and a
    real `.git` at the current working directory. Neither is available inside the
    containerized `docker build --target test` image, whose build context is
    `apps/api` alone and carries no `.git`. Skip cleanly there instead of crashing
    collection for the whole file."""
    if shutil.which("git") is None:
        pytest.skip("git is not installed in this environment", allow_module_level=True)
    completed = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    if completed.returncode != 0:
        pytest.skip("not running inside a git checkout", allow_module_level=True)
    return completed.stdout.strip()


REAL_COMMIT = _real_commit_or_skip()


def test_env_override_takes_precedence(monkeypatch):
    monkeypatch.setenv("KENDRA_SOURCE_REVISION", "a" * 40)
    monkeypatch.delenv("KENDRA_SOURCE_REVISION_DIRTY", raising=False)
    result = resolve_source_revision()
    assert result.revision == "a" * 40
    assert result.dirty is False


def test_env_override_is_case_and_whitespace_normalized(monkeypatch):
    monkeypatch.setenv("KENDRA_SOURCE_REVISION", f"  {'B' * 40}  ")
    monkeypatch.delenv("KENDRA_SOURCE_REVISION_DIRTY", raising=False)
    result = resolve_source_revision()
    assert result.revision == "b" * 40


def test_env_override_rejects_a_value_that_is_not_40_hex_chars(monkeypatch):
    monkeypatch.setenv("KENDRA_SOURCE_REVISION", "not-a-commit-id")
    with pytest.raises(ValueError, match="KENDRA_SOURCE_REVISION"):
        resolve_source_revision()


def test_the_literal_unknown_does_not_crash_but_falls_through(monkeypatch):
    """Regression: docker-compose.yml defaults the container's env var to the
    literal "unknown" when the operator forgets to export a real revision. That
    must degrade to the honest unknown/git fallback, not raise and crash the API
    at startup — found by external review before the live Ubuntu run."""
    monkeypatch.setenv("KENDRA_SOURCE_REVISION", "unknown")
    monkeypatch.delenv("KENDRA_SOURCE_REVISION_DIRTY", raising=False)
    result = resolve_source_revision()
    assert result.revision == REAL_COMMIT
    assert isinstance(result.dirty, bool)


def test_the_literal_unknown_is_case_insensitive_and_whitespace_tolerant(monkeypatch):
    monkeypatch.setenv("KENDRA_SOURCE_REVISION", "  Unknown  ")
    monkeypatch.delenv("KENDRA_SOURCE_REVISION_DIRTY", raising=False)
    result = resolve_source_revision()
    assert result.revision == REAL_COMMIT


def test_empty_string_env_var_also_falls_through(monkeypatch):
    """docker-compose's `${VAR:-default}` substitutes on unset OR empty, so an
    explicitly-empty env var must behave the same as an unset one."""
    monkeypatch.setenv("KENDRA_SOURCE_REVISION", "")
    monkeypatch.delenv("KENDRA_SOURCE_REVISION_DIRTY", raising=False)
    result = resolve_source_revision()
    assert result.revision == REAL_COMMIT


def test_dirty_env_override_applies_even_with_a_revision_override(monkeypatch):
    monkeypatch.setenv("KENDRA_SOURCE_REVISION", "c" * 40)
    monkeypatch.setenv("KENDRA_SOURCE_REVISION_DIRTY", "true")
    result = resolve_source_revision()
    assert result.dirty is True


def test_falls_back_to_git_rev_parse_head_within_a_repo(monkeypatch, tmp_path):
    monkeypatch.delenv("KENDRA_SOURCE_REVISION", raising=False)
    monkeypatch.delenv("KENDRA_SOURCE_REVISION_DIRTY", raising=False)
    result = resolve_source_revision()
    assert result.revision == REAL_COMMIT
    assert isinstance(result.dirty, bool)


def test_falls_back_to_unknown_outside_any_git_repo(monkeypatch, tmp_path):
    monkeypatch.delenv("KENDRA_SOURCE_REVISION", raising=False)
    monkeypatch.delenv("KENDRA_SOURCE_REVISION_DIRTY", raising=False)
    outside_git = tmp_path / "no-git-here"
    outside_git.mkdir()
    result = resolve_source_revision(cwd=outside_git)
    assert result.revision == "unknown"
    assert result.dirty is False


def test_unknown_revision_honors_a_dirty_override(monkeypatch, tmp_path):
    monkeypatch.delenv("KENDRA_SOURCE_REVISION", raising=False)
    monkeypatch.setenv("KENDRA_SOURCE_REVISION_DIRTY", "1")
    outside_git = tmp_path / "no-git-here"
    outside_git.mkdir()
    result = resolve_source_revision(cwd=outside_git)
    assert result.revision == "unknown"
    assert result.dirty is True
