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
) -> tuple[dict, dict]:
    score = score_run(dataset, results)
    worksheet = {
        "fact_entries": score.pop("fact_worksheet_entries"),
        "ambiguity_entries": score.pop("ambiguity_worksheet_entries"),
    }

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
        # Whether this run hit a real API at all. A --fake-model run answers every
        # case from a scripted model and says nothing about answering quality — only
        # that the reporting pipeline itself works. Surfaced prominently in
        # report.md rather than left to be inferred from answer_model=="fake-model".
        "fake_model": config.fake_model,
        "category_counts": category_counts,
        "attempted_counts": attempted_counts,
        "timeout_count": score["response_time"]["timeout_count"],
        "metrics": score,
        "acceptance_claim": False,
        "acceptance_claim_reason": _acceptance_claim_reason(scoring_reviewed=False),
    }
    return report, worksheet


def _score_fact_entries(fact_entries: list[dict]) -> tuple[dict, bool]:
    """Only entries carrying a `reviewed_label` (TP/FN/FP) participate; anything
    still `null` is treated as not yet reviewed and is excluded rather than
    guessed."""
    reviewed = [entry for entry in fact_entries if entry.get("reviewed_label")]
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
    fully_reviewed = len(reviewed) == len(fact_entries) and bool(fact_entries)
    return {
        "status": "reviewed" if fully_reviewed else "partially_reviewed",
        "matching_method": "human_review",
        "fact_true_positive": tp,
        "fact_false_negative": fn,
        "fact_false_positive": fp,
        "fact_false_positive_note": None,
        "fact_recall": recall,
        "fact_precision": precision,
        "fact_f1": f1,
    }, fully_reviewed


def _score_ambiguity_entries(ambiguity_entries: list[dict]) -> tuple[dict, bool]:
    from kendra_api.evaluation.scoring import AMBIGUITY_CATEGORIES

    reviewed = [entry for entry in ambiguity_entries if entry.get("reviewed_category")]
    counts = dict.fromkeys(AMBIGUITY_CATEGORIES, 0)
    for entry in reviewed:
        category = entry["reviewed_category"]
        if category in counts:
            counts[category] += 1
    fully_reviewed = len(reviewed) == len(ambiguity_entries) and bool(ambiguity_entries)
    return {
        "status": "reviewed" if fully_reviewed else "partially_reviewed",
        "note": None,
        "total_cases": len(ambiguity_entries),
        "reviewed_count": len(reviewed),
        "categories": counts,
    }, fully_reviewed


def apply_scored_worksheet(report: dict, worksheet: dict) -> dict:
    """Recompute headline fact and ambiguity-review metrics from a human-reviewed
    worksheet (the object `scoring_worksheet.json` writes: `fact_entries` and
    `ambiguity_entries`)."""
    fact_metrics, facts_fully_reviewed = _score_fact_entries(worksheet.get("fact_entries", []))
    ambiguity_metrics, ambiguity_fully_reviewed = _score_ambiguity_entries(
        worksheet.get("ambiguity_entries", [])
    )

    report = dict(report)
    report["metrics"] = dict(report["metrics"])
    report["metrics"]["atomic_fact_scoring"] = fact_metrics
    report["metrics"]["ambiguity_review"] = ambiguity_metrics
    report["acceptance_claim"] = False
    report["acceptance_claim_reason"] = _acceptance_claim_reason(
        scoring_reviewed=facts_fully_reviewed and ambiguity_fully_reviewed
    )
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
    ]
    if report.get("fake_model"):
        lines += [
            "> **FAKE-MODEL RUN — not a real answering result.** Every case below was "
            "answered by an in-process scripted model on a fixed right/wrong/timeout/"
            "malformed schedule, exercised through the real API and audit code path. "
            "These numbers validate that the reporting pipeline works. They say "
            "nothing about answering quality and must not be read as one.",
            "",
        ]
    lines += [
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
        "- predicted label: `supported` iff the response status was exactly "
        "`supported`; every other status — `insufficient_evidence`, "
        "`conflicting_evidence`, `source_unavailable`, `system_error`, or a client "
        "timeout — counts as predicted `unsupported` here. That is coarser than "
        "'unsupported rejection' below: a timeout counts as a correct classification "
        "on an unsupported case, but not as a safe rejection.",
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
        f"- mean: {latency['mean_ms']} ms · median: {latency['median_ms']} ms"
        f" · p90: {latency['p90_ms']} ms · max: {latency['max_ms']} ms",
        f"- timeouts: {metrics['response_time']['timeout_count']}"
        f" · failed: {metrics['response_time']['failed_count']}",
        "- 'timeouts' is a subset of 'failed', not an addition to it: 'failed' counts "
        "every case with a `system_error`/`source_unavailable` status, a client "
        "error, or a timeout — timeouts are one way a case can fail, not a separate "
        "problem count on top.",
        "",
    ]

    ambiguity = metrics.get("ambiguity_review")
    if ambiguity:
        lines += [
            f"## Ambiguous-case review ({ambiguity['status']})",
            f"- {ambiguity['reviewed_count']}/{ambiguity['total_cases']} cases reviewed",
        ]
        for category, count in ambiguity["categories"].items():
            lines.append(f"  - {category}: {count}")
        if ambiguity.get("note"):
            lines.append(f"- note: {ambiguity['note']}")
        lines.append("")

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
    worksheet: dict,
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
        json.dumps(worksheet, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    (run_dir / "failed_cases.md").write_text(render_failed_cases_markdown(results), encoding="utf-8")
