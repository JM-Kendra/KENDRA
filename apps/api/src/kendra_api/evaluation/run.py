"""Milestone 12 gold-set evaluation runner.

    python -m kendra_api.evaluation.run --phase cold
    python -m kendra_api.evaluation.run --phase warm
    python -m kendra_api.evaluation.run --phase cold --fake-model   # hermetic

Preflight, in order (Section 5): validate the dataset (`scripts/validate_gold_cases.py`
logic), check its sha256, confirm the API is ready and answering-enabled, confirm the
answer and embedding models are present in Ollama, and record the resolved model
names and source revision from the API's own `/api/v1/health` response rather than
from local config. Any failure exits non-zero with one clear line (Section 2.6) —
this runner never produces a report of 50 "unsupported" results against a system
that was never actually ready.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx

from kendra_api.evaluation.client import EvaluationClient, http_evaluation_client
from kendra_api.evaluation.dataset import load_and_validate_dataset
from kendra_api.evaluation.fake_model import build_fake_evaluation_client
from kendra_api.evaluation.lock import RunLock, RunLockHeld
from kendra_api.evaluation.models import CaseRunResult, GoldCase, PreflightError, RunConfig
from kendra_api.evaluation.preflight import (
    check_api_health,
    check_ollama_has_models,
    check_source_revision_matches_head,
)
from kendra_api.evaluation.report import (
    append_case_result,
    apply_scored_worksheet,
    build_report,
    finalize_run_directory,
    initialize_run_directory,
)
from kendra_api.evaluation.scoring import predicted_label

# `evaluation/gold_cases.json`, dataset `kendra-bir-public-gold-v2`, per M12_BRIEF.md
# Section 0. The dataset itself is tracked and reviewable; this is a known-good
# checksum of it, not a secret, and being wrong here is exactly what the check exists
# to catch.
DEFAULT_DATASET_SHA256 = "6aace5184c6778cad8c0d1972d83c99b6d3837355064ecc88dc941d86bab8f86"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--dataset", type=Path, default=None, help="defaults to <repo-root>/evaluation/gold_cases.json"
    )
    parser.add_argument("--expect-dataset-sha256", default=DEFAULT_DATASET_SHA256)
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--ollama-base", default="http://127.0.0.1:11434")
    parser.add_argument("--phase", choices=["cold", "warm"], required=True)
    parser.add_argument(
        "--seed", type=int, default=None, help="defaults to a random seed, recorded in run_config.json"
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=float,
        default=None,
        help="default: 150s live, 1s with --fake-model (the scripted timeout bucket hangs 2.5s)",
    )
    parser.add_argument(
        "--fake-model",
        action="store_true",
        help="fully hermetic in-process run against a scripted model; skips live preflight",
    )
    parser.add_argument("--fake-model-hang-seconds", type=float, default=2.5)
    parser.add_argument(
        "--allow-unknown-revision",
        action="store_true",
        help=(
            "skip the preflight gate that otherwise refuses to run when "
            "/api/v1/health reports source_revision='unknown' or "
            "source_revision_dirty=true (invariant 2)"
        ),
    )
    parser.add_argument(
        "--allow-revision-mismatch",
        action="store_true",
        help=(
            "override the preflight gate that otherwise refuses to run when "
            "/api/v1/health's source_revision does not equal 'git rev-parse HEAD' "
            "at --repo-root (docs/incidents/INC-001-ghost-evaluation-runs.md); "
            "recorded as source_revision_mismatch_overridden in the run's report, "
            "not silently accepted"
        ),
    )
    parser.add_argument(
        "--lock-path",
        type=Path,
        default=None,
        help=(
            "run-lock file path; refuses to start if it already exists, removed "
            "on a clean exit only. Defaults to <repo-root>/evaluation/runs/.lock"
        ),
    )
    parser.add_argument(
        "--container-name",
        default=None,
        help="recorded in the lock file; defaults to kendra-eval-<evaluation-run-id>",
    )
    parser.add_argument(
        "--output-root", type=Path, default=None, help="defaults to <repo-root>/evaluation/runs/M12-gold"
    )
    parser.add_argument(
        "--scored-worksheet",
        type=Path,
        default=None,
        help=(
            "a reviewed scoring_worksheet.json ({fact_entries, ambiguity_entries}); "
            "supersedes the provisional atomic-fact and ambiguity-review scores"
        ),
    )
    return parser.parse_args(argv)


async def _run_case(client: EvaluationClient, case: GoldCase, evaluation_run_id: str) -> CaseRunResult:
    result = await client.ask(
        question=case.question, collection_id="default", evaluation_run_id=evaluation_run_id
    )
    response_status = "timeout" if result.timed_out else result.body.get("status", "system_error")
    return CaseRunResult(
        case_id=case.case_id,
        category=case.category,
        ocr_required=case.ocr_required,
        expected_result=case.expected_result,
        predicted_label=predicted_label(response_status),
        http_status=result.http_status,
        response_status=response_status,
        answer=result.body.get("answer", ""),
        citations=result.body.get("citations", []),
        request_id=result.body.get("request_id"),
        timed_out=result.timed_out,
        error=result.error,
        duration_ms=result.duration_ms,
        evaluation_run_id=evaluation_run_id,
    )


async def _amain(args: argparse.Namespace) -> int:
    repo_root = args.repo_root
    dataset_path = args.dataset or (repo_root / "evaluation" / "gold_cases.json")
    output_root = args.output_root or (repo_root / "evaluation" / "runs" / "M12-gold")

    # Lock acquired before anything else, including dataset validation --
    # docs/incidents/INC-001-ghost-evaluation-runs.md: two invocations of this
    # same runner overlapped, unnoticed, against the same live API and the same
    # question_audit table. A second invocation must refuse to start, loudly,
    # the moment it's attempted -- not after doing other work first.
    evaluation_run_id = f"eval-{uuid.uuid4()}"
    lock_path = args.lock_path or (repo_root / "evaluation" / "runs" / ".lock")
    container_name = args.container_name or f"kendra-eval-{evaluation_run_id}"
    try:
        lock = RunLock.acquire(lock_path, run_id=evaluation_run_id, container_name=container_name)
    except RunLockHeld as exc:
        print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
        return 1

    try:
        dataset = load_and_validate_dataset(
            dataset_path=dataset_path,
            repo_root=repo_root,
            expect_dataset_sha256=args.expect_dataset_sha256,
        )
    except PreflightError as exc:
        print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
        return 1

    seed = args.seed if args.seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
    ordered_cases = list(dataset.cases)
    random.Random(seed).shuffle(ordered_cases)
    request_timeout_seconds = args.request_timeout_seconds
    if request_timeout_seconds is None:
        request_timeout_seconds = 1.0 if args.fake_model else 150.0

    ollama_client: httpx.AsyncClient | None = None
    revision_mismatch_overridden = False
    try:
        if args.fake_model:
            client, _audit_sink = build_fake_evaluation_client(
                dataset,
                request_timeout_seconds=request_timeout_seconds,
                hang_seconds=args.fake_model_hang_seconds,
            )
            health_body = {
                "source_revision": "fake-model-eval",
                "source_revision_dirty": False,
                "answer_model": "fake-model",
                "embedding_model": "fake-model",
                "retrieval_top_k": None,
                "retrieval_score_threshold": None,
            }
        else:
            client = http_evaluation_client(args.api_base, timeout_seconds=request_timeout_seconds)
            try:
                health_body = await check_api_health(
                    client.raw, allow_unknown_revision=args.allow_unknown_revision
                )
                ollama_client = httpx.AsyncClient(base_url=args.ollama_base.rstrip("/"), timeout=10.0)
                await check_ollama_has_models(
                    ollama_client,
                    answer_model=health_body.get("answer_model", ""),
                    embedding_model=health_body.get("embedding_model", ""),
                )
                revision_mismatch_overridden = check_source_revision_matches_head(
                    health_body,
                    repo_root=repo_root,
                    allow_mismatch=args.allow_revision_mismatch,
                )
            except PreflightError as exc:
                print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
                await client.aclose()
                return 1

        timestamp = datetime.now(UTC)
        config = RunConfig(
            dataset_path=str(dataset_path),
            dataset_sha256=dataset.dataset_sha256,
            dataset_status=dataset.dataset_status,
            source_revision=health_body.get("source_revision") or "unknown",
            source_revision_dirty=bool(health_body.get("source_revision_dirty", False)),
            answer_model=health_body.get("answer_model") or "unknown",
            embedding_model=health_body.get("embedding_model") or "unknown",
            retrieval_top_k=health_body.get("retrieval_top_k"),
            retrieval_score_threshold=health_body.get("retrieval_score_threshold"),
            seed=seed,
            phase=args.phase,
            api_base="in-process-fake-model" if args.fake_model else args.api_base,
            fake_model=args.fake_model,
            evaluation_run_id=evaluation_run_id,
            timestamp_utc=timestamp.isoformat(),
            source_revision_mismatch_overridden=revision_mismatch_overridden,
        )
        short_sha = config.source_revision[:8] if config.source_revision != "unknown" else "unknownrev"
        run_dir = output_root / f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{short_sha}"
        # Written now, before the first case is asked -- not batched to the end.
        # docs/incidents/INC-001-ghost-evaluation-runs.md: a run (or an unnoticed
        # duplicate of one) that only produces output at completion is invisible
        # to anyone checking the host-mounted directory while it's in progress.
        initialize_run_directory(run_dir=run_dir, config=config)

        results: list[CaseRunResult] = []
        for case in ordered_cases:
            result = await _run_case(client, case, evaluation_run_id)
            append_case_result(run_dir=run_dir, result=result)
            results.append(result)

        await client.aclose()
    finally:
        if ollama_client is not None:
            await ollama_client.aclose()

    report, worksheet = build_report(dataset=dataset, results=results, config=config)
    if args.scored_worksheet:
        reviewed_worksheet = json.loads(args.scored_worksheet.read_text(encoding="utf-8"))
        report = apply_scored_worksheet(report, reviewed_worksheet)
        worksheet = reviewed_worksheet

    finalize_run_directory(
        run_dir=run_dir, dataset=dataset, results=results, report=report, worksheet=worksheet
    )

    print(f"wrote {run_dir}")
    print(
        f"acceptance_claim={report['acceptance_claim']} "
        f"attempted={report['metrics']['attempted_case_count']} "
        f"timeouts={report['timeout_count']}"
    )
    # Clean exit only -- a crash or a killed process leaves the lock in place on
    # purpose, so the next invocation's acquire() surfaces exactly the failure
    # this module exists to catch.
    lock.release()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
