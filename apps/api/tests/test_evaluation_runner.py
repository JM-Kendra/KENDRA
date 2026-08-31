"""Milestone 12 — evaluation runner, hermetic tier (Section 6, Mac/Claude Code).

Exercises `--fake-model` end to end: dataset validation, all 50 gold cases through a
real `create_app()` instance over an in-process ASGI transport, and the full report
pipeline. No Postgres, Qdrant, or Ollama is contacted.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path

import pytest

from kendra_api.evaluation.dataset import load_and_validate_dataset
from kendra_api.evaluation.models import CaseRunResult, PreflightError
from kendra_api.evaluation.report import apply_scored_worksheet
from kendra_api.evaluation.run import DEFAULT_DATASET_SHA256, parse_args, _amain
from kendra_api.evaluation.scoring import score_run

pytestmark = pytest.mark.milestone12

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "evaluation" / "gold_cases.json"


async def _run_fake_model(tmp_path: Path, *, seed: int = 7, scored_worksheet: Path | None = None):
    argv = [
        "--repo-root",
        str(REPO_ROOT),
        "--phase",
        "cold",
        "--fake-model",
        "--fake-model-hang-seconds",
        "0.3",
        "--request-timeout-seconds",
        "0.1",
        "--output-root",
        str(tmp_path),
        "--seed",
        str(seed),
    ]
    if scored_worksheet is not None:
        argv += ["--scored-worksheet", str(scored_worksheet)]
    args = parse_args(argv)
    exit_code = await _amain(args)
    assert exit_code == 0
    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    return run_dirs[0]


async def test_fake_model_run_produces_a_complete_run_directory(tmp_path):
    run_dir = await _run_fake_model(tmp_path)

    expected_files = {
        "run_config.json",
        "cases.jsonl",
        "report.json",
        "report.md",
        "scoring_worksheet.json",
        "failed_cases.md",
    }
    assert {path.name for path in run_dir.iterdir()} == expected_files

    cases = [json.loads(line) for line in (run_dir / "cases.jsonl").read_text().splitlines()]
    assert len(cases) == 50
    assert {case["case_id"] for case in cases} == {
        json.loads(DATASET_PATH.read_text())["cases"][i]["case_id"] for i in range(50)
    }


async def test_every_aggregate_in_report_json_recomputes_from_cases_jsonl(tmp_path):
    run_dir = await _run_fake_model(tmp_path)

    dataset = load_and_validate_dataset(
        dataset_path=DATASET_PATH, repo_root=REPO_ROOT, expect_dataset_sha256=DEFAULT_DATASET_SHA256
    )
    cases_lines = (run_dir / "cases.jsonl").read_text().splitlines()
    results = [CaseRunResult(**json.loads(line)) for line in cases_lines]

    recomputed = score_run(dataset, results)
    recomputed.pop("fact_worksheet_entries")

    report = json.loads((run_dir / "report.json").read_text())
    assert report["metrics"] == recomputed


async def test_fake_model_run_exercises_every_scripted_bucket(tmp_path):
    run_dir = await _run_fake_model(tmp_path)
    cases = [json.loads(line) for line in (run_dir / "cases.jsonl").read_text().splitlines()]

    statuses = {case["response_status"] for case in cases}
    timed_out = [case for case in cases if case["timed_out"]]
    # good -> a real status; bad -> "supported" (possibly wrongly); malformed ->
    # "system_error"; timeout -> timed_out=True. All four must appear across 50 cases.
    assert "system_error" in statuses
    assert timed_out, "the scripted timeout bucket never produced a client-side timeout"


async def test_report_is_provisional_and_never_claims_acceptance(tmp_path):
    run_dir = await _run_fake_model(tmp_path)
    report = json.loads((run_dir / "report.json").read_text())

    assert report["acceptance_claim"] is False
    assert report["acceptance_claim_reason"]
    assert report["metrics"]["atomic_fact_scoring"]["status"] == "provisional"
    assert report["metrics"]["atomic_fact_scoring"]["fact_false_positive"] is None


async def test_scored_worksheet_overrides_provisional_fact_scores(tmp_path):
    first_run_dir = await _run_fake_model(tmp_path / "first", seed=7)
    worksheet = json.loads((first_run_dir / "scoring_worksheet.json").read_text())
    assert worksheet, "expected at least one supported case to produce worksheet entries"

    for entry in worksheet:
        entry["reviewed_label"] = entry["provisional_label"]
    reviewed_path = tmp_path / "reviewed_worksheet.json"
    reviewed_path.write_text(json.dumps(worksheet))

    second_run_dir = await _run_fake_model(tmp_path / "second", seed=7, scored_worksheet=reviewed_path)
    report = json.loads((second_run_dir / "report.json").read_text())

    facts = report["metrics"]["atomic_fact_scoring"]
    assert facts["status"] == "reviewed"
    assert facts["fact_false_positive"] == 0
    assert facts["fact_precision"] == 1.0
    assert report["acceptance_claim"] is False


async def test_dataset_sha256_mismatch_fails_preflight_loudly():
    with pytest.raises(PreflightError, match="sha256 mismatch"):
        load_and_validate_dataset(
            dataset_path=DATASET_PATH, repo_root=REPO_ROOT, expect_dataset_sha256="0" * 64
        )


def test_evaluation_run_directory_is_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "evaluation/runs/M12-gold/x/report.json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "evaluation/runs/M12-gold/x/report.json"
