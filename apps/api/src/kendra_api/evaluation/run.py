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
from kendra_api.evaluation.models import CaseRunResult, GoldCase, PreflightError, RunConfig
from kendra_api.evaluation.preflight import check_api_health, check_ollama_has_models
from kendra_api.evaluation.report import apply_scored_worksheet, build_report, write_run_directory
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
        "--output-root", type=Path, default=None, help="defaults to <repo-root>/evaluation/runs/M12-gold"
    )
    parser.add_argument(
        "--scored-worksheet",
        type=Path,
        default=None,
        help="a reviewed scoring_worksheet.json; supersedes the provisional atomic-fact scores",
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

    try:
        dataset = load_and_validate_dataset(
            dataset_path=dataset_path,
            repo_root=repo_root,
            expect_dataset_sha256=args.expect_dataset_sha256,
        )
    except PreflightError as exc:
        print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
        return 1

    evaluation_run_id = f"eval-{uuid.uuid4()}"
    seed = args.seed if args.seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
    ordered_cases = list(dataset.cases)
    random.Random(seed).shuffle(ordered_cases)
    request_timeout_seconds = args.request_timeout_seconds
    if request_timeout_seconds is None:
        request_timeout_seconds = 1.0 if args.fake_model else 150.0

    ollama_client: httpx.AsyncClient | None = None
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
                health_body = await check_api_health(client.raw)
                ollama_client = httpx.AsyncClient(base_url=args.ollama_base.rstrip("/"), timeout=10.0)
                await check_ollama_has_models(
                    ollama_client,
                    answer_model=health_body.get("answer_model", ""),
                    embedding_model=health_body.get("embedding_model", ""),
                )
            except PreflightError as exc:
                print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
                await client.aclose()
                return 1

        results = [await _run_case(client, case, evaluation_run_id) for case in ordered_cases]
        await client.aclose()
    finally:
        if ollama_client is not None:
            await ollama_client.aclose()

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
    )

    report, worksheet_entries = build_report(dataset=dataset, results=results, config=config)
    if args.scored_worksheet:
        reviewed_entries = json.loads(args.scored_worksheet.read_text(encoding="utf-8"))
        report = apply_scored_worksheet(report, reviewed_entries)
        worksheet_entries = reviewed_entries

    short_sha = config.source_revision[:8] if config.source_revision != "unknown" else "unknownrev"
    run_dir = output_root / f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{short_sha}"
    write_run_directory(
        run_dir=run_dir,
        config=config,
        dataset=dataset,
        results=results,
        report=report,
        worksheet_entries=worksheet_entries,
    )

    print(f"wrote {run_dir}")
    print(
        f"acceptance_claim={report['acceptance_claim']} "
        f"attempted={report['metrics']['attempted_case_count']} "
        f"timeouts={report['timeout_count']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
