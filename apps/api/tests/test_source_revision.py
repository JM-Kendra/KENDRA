"""Milestone 12 — single source-revision resolution path (Section 4)."""

from __future__ import annotations

import subprocess

import pytest

from kendra_api.source_revision import resolve_source_revision

pytestmark = pytest.mark.milestone12

REAL_COMMIT = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()


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
