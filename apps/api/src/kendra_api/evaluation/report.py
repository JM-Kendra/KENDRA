"""Run-directory output: `run_config.json`, `cases.jsonl`, `report.json`, `report.md`,
`scoring_worksheet.json`, `failed_cases.md`.

Every number in `report.json["metrics"]` must be recomputable from the per-case
records preserved in the same directory's `cases.jsonl` (Section 2.5, "No aggregate
without cases") — `score_run` is the single function that produces those metrics from
exactly that input, so recomputation is just calling it again.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from kendra_api.evaluation.models import CaseRunResult, GoldDataset, RunConfig
from kendra_api.evaluation.scoring import score_run

OPEN_GATES = [
    "dataset_status is 'initial_expert_review_required', not an approved gold set",
    "Milestone 10 answering is an unaccepted prototype (docs/milestones/M12_STATUS.md)",
    "EXP-01 is inconclusive/failed and EXP-03 remains blocked",
    "atomic-fact and citation scoring are provisional pending a human-reviewed "
    "scoring_worksheet.json (--scored-worksheet)",
]


def _acceptance_claim_reason(scoring_reviewed: bool) -> str:
    gates = list(OPEN_GATES)
    if scoring_reviewed:
        gates = [gate for gate in gates if not gate.startswith("atomic-fact")]
    return "; ".join(gates)


def build_report(
    *,
    dataset: GoldDataset,
    results: list[CaseRunResult],
    config: RunConfig,
) -> tuple[dict, list[dict]]:
    score = score_run(dataset, results)
    worksheet_entries = score.pop("fact_worksheet_entries")

    category_counts: dict[str, int] = {}
    attempted_counts: dict[str, int] = {"supported": 0, "unsupported": 0}
    for case in dataset.cases:
        category_counts[case.category] = category_counts.get(case.category, 0) + 1
    for result in results:
        attempted_counts[result.expected_result] = attempted_counts.get(result.expected_result, 0) + 1

    report = {
        "dataset_id": dataset.dataset_id,
        "dataset_sha256": dataset.dataset_sha256,
        "dataset_status": dataset.dataset_status,
        "source_revision": config.source_revision,
        "source_revision_dirty": config.source_revision_dirty,
        "answer_model": config.answer_model,
        "embedding_model": config.embedding_model,
        "retrieval_top_k": config.retrieval_top_k,
        "retrieval_score_threshold": config.retrieval_score_threshold,
        "seed": config.seed,
        "phase": config.phase,
        "timestamp_utc": config.timestamp_utc,
        "evaluation_run_id": config.evaluation_run_id,
        "category_counts": category_counts,
        "attempted_counts": attempted_counts,
        "timeout_count": score["response_time"]["timeout_count"],
        "metrics": score,
        "acceptance_claim": False,
        "acceptance_claim_reason": _acceptance_claim_reason(scoring_reviewed=False),
    }
    return report, worksheet_entries


def apply_scored_worksheet(report: dict, worksheet_entries: list[dict]) -> dict:
    """Recompute headline fact metrics from a human-reviewed worksheet.

    Only entries carrying a `reviewed_label` (TP/FN/FP) participate; anything still
    `null` is treated as not yet reviewed and is excluded rather than guessed.
    """
    reviewed = [entry for entry in worksheet_entries if entry.get("reviewed_label")]
    tp = sum(1 for entry in reviewed if entry["reviewed_label"] == "TP")
    fn = sum(1 for entry in reviewed if entry["reviewed_label"] == "FN")
    fp = sum(1 for entry in reviewed if entry["reviewed_label"] == "FP")
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    fully_reviewed = len(reviewed) == len(worksheet_entries) and bool(worksheet_entries)

    report = dict(report)
    report["metrics"] = dict(report["metrics"])
    report["metrics"]["atomic_fact_scoring"] = {
        "status": "reviewed" if fully_reviewed else "partially_reviewed",
        "matching_method": "human_review",
        "fact_true_positive": tp,
        "fact_false_negative": fn,
        "fact_false_positive": fp,
        "fact_false_positive_note": None,
        "fact_recall": recall,
        "fact_precision": precision,
        "fact_f1": f1,
    }
    report["acceptance_claim"] = False
    report["acceptance_claim_reason"] = _acceptance_claim_reason(scoring_reviewed=fully_reviewed)
    return report


def render_report_markdown(report: dict) -> str:
    metrics = report["metrics"]
    classification = metrics["classification"]
    facts = metrics["atomic_fact_scoring"]
    citations = metrics["citation_scoring"]
    rejection = metrics["unsupported_rejection"]
    latency = metrics["response_time"]["overall"]

    lines = [
        f"# Milestone 12 gold evaluation — {report['phase']} run",
        "",
        f"- dataset: `{report['dataset_id']}` sha256 `{report['dataset_sha256']}`"
        f" (status: `{report['dataset_status']}`)",
        f"- source revision: `{report['source_revision']}`"
        f"{' (dirty)' if report['source_revision_dirty'] else ''}",
        f"- answer model: `{report['answer_model']}` · embedding model: `{report['embedding_model']}`",
        f"- seed: `{report['seed']}` · timestamp: `{report['timestamp_utc']}`",
        f"- evaluation_run_id: `{report['evaluation_run_id']}`",
        "",
        f"**acceptance_claim: {report['acceptance_claim']}** — {report['acceptance_claim_reason']}",
        "",
        "## Category and attempted counts",
        f"- categories: {report['category_counts']}",
        f"- attempted: {report['attempted_counts']}",
        "",
        "## Classification (supported vs. unsupported)",
        f"- accuracy: {classification['accuracy']}",
        f"- precision: {classification['supported_precision']} · recall:"
        f" {classification['supported_recall']} · F1: {classification['supported_f1']}",
        f"- TP {classification['true_positive']} / FN {classification['false_negative']}"
        f" / FP {classification['false_positive']} / TN {classification['true_negative']}",
        "",
        f"## Atomic-fact scoring ({facts['status']})",
        f"- matching method: {facts['matching_method']}",
        f"- TP {facts['fact_true_positive']} / FN {facts['fact_false_negative']}"
        f" / FP {facts['fact_false_positive']}",
        f"- recall: {facts['fact_recall']} · precision: {facts['fact_precision']}"
        f" · F1: {facts['fact_f1']}",
    ]
    if facts.get("fact_false_positive_note"):
        lines.append(f"- note: {facts['fact_false_positive_note']}")
    lines += [
        "",
        f"## Citation scoring ({citations['status']})",
        f"- citation precision (approx.): {citations['citation_precision_approx']}",
        f"- correct-page citation rate (approx.): {citations['correct_page_citation_rate_approx']}",
        f"- note: {citations['note']}",
        "",
        "## Unsupported rejection",
        f"- unsupported rejection rate: {rejection['unsupported_rejection_rate']}"
        f" ({rejection['safe_rejections']}/{rejection['attempted']})",
        f"- unsupported false-answer rate: {rejection['unsupported_false_answer_rate']}"
        f" ({rejection['false_answers']}/{rejection['attempted']})",
        "",
        "## Response time (overall)",
        f"- median: {latency['median_ms']} ms · p90: {latency['p90_ms']} ms"
        f" · max: {latency['max_ms']} ms",
        f"- timeouts: {metrics['response_time']['timeout_count']}"
        f" · failed: {metrics['response_time']['failed_count']}",
        "",
    ]
    return "\n".join(lines)


def render_failed_cases_markdown(results: list[CaseRunResult]) -> str:
    failed = [
        result
        for result in results
        if result.timed_out or result.error or result.response_status in {"system_error", "source_unavailable"}
    ]
    lines = ["# Failed and timed-out cases", ""]
    if not failed:
        lines.append("None.")
        return "\n".join(lines)
    for result in failed:
        lines.append(
            f"- `{result.case_id}` status=`{result.response_status}` "
            f"http={result.http_status} timed_out={result.timed_out} "
            f"error={result.error!r} duration_ms={result.duration_ms}"
        )
    return "\n".join(lines)


def write_run_directory(
    *,
    run_dir: Path,
    config: RunConfig,
    dataset: GoldDataset,
    results: list[CaseRunResult],
    report: dict,
    worksheet_entries: list[dict],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "run_config.json").write_text(
        json.dumps(dataclasses.asdict(config), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    with (run_dir / "cases.jsonl").open("w", encoding="utf-8") as stream:
        for result in results:
            stream.write(json.dumps(dataclasses.asdict(result), sort_keys=True, default=str) + "\n")
    (run_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    (run_dir / "report.md").write_text(render_report_markdown(report), encoding="utf-8")
    (run_dir / "scoring_worksheet.json").write_text(
        json.dumps(worksheet_entries, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    (run_dir / "failed_cases.md").write_text(render_failed_cases_markdown(results), encoding="utf-8")
