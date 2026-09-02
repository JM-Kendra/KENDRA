"""Shared fixtures for tests that need a real, on-disk Git repository.

`test_evaluation_lock.py` and `test_evaluation_source_revision_preflight.py`
exercise code that shells out to `git rev-parse HEAD` / `--show-toplevel`, and
the lock tests additionally load the real gold-dataset validator dynamically
from `<repo_root>/scripts/validate_gold_cases.py`
(`kendra_api.evaluation.dataset`). Both files used to resolve this by walking
up from wherever this test file happened to live on disk, which only worked
when pytest ran against a live repository checkout -- e.g. the bind-mounted
`eval-runner` flow, where this file's on-disk location genuinely sits inside
the real checkout, with `evaluation/` and `scripts/` right there too. It never
worked inside `docker build --target test`'s isolated image, which copies in
no `.git`, `scripts/`, or `evaluation/` at all.

The `repo_root` fixture below tries that real-checkout path first (unchanged
behavior for the bind-mounted flow), and only falls back to building a
throwaway repository fresh in `tmp_path` when no real checkout is reachable --
using the real `scripts/validate_gold_cases.py` and `evaluation/gold_cases.json`
baked into this test image at `tests/fixtures/gold_dataset/` for exactly that
case (see `apps/api/Dockerfile`'s `test` stage, pulled in via a named
`fixtures` build context). This way both flows exercise the same tests: the
bind-mounted flow against the real checkout it's already mounting, the
hermetic image against a throwaway stand-in built from the same real files.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "gold_dataset"


def _run_git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _real_checkout_root() -> Path | None:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(__file__).resolve().parent,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    root = Path(completed.stdout.strip())
    if not (root / "evaluation" / "gold_cases.json").is_file():
        return None
    return root


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git is not installed in this environment")

    real_root = _real_checkout_root()
    if real_root is not None:
        return real_root

    if not (_FIXTURE_ROOT / "evaluation" / "gold_cases.json").is_file():
        pytest.skip(
            "neither a real git checkout nor the baked gold_dataset fixture is available"
        )

    root = tmp_path / "repo"
    shutil.copytree(_FIXTURE_ROOT, root)
    _run_git("init", "-q", cwd=root)
    _run_git("config", "user.email", "test@example.invalid", cwd=root)
    _run_git("config", "user.name", "kendra-test", cwd=root)
    _run_git("add", "-A", cwd=root)
    _run_git("commit", "-q", "-m", "throwaway fixture repo", cwd=root)
    return root
