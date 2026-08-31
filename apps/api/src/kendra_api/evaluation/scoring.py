"""Scoring per `docs/EVALUATION_METHOD.md`.

Classification (supported vs. unsupported), latency, and the two rejection-rate
metrics are fully mechanical and computed directly. Atomic-fact and citation
correctness require judging *meaning* ("review meaning, not exact wording"; "the
cited page supports the adjacent claim in context") — the method says so explicitly.
Those are computed here as clearly labeled provisional approximations (normalized
substring / token-overlap matching) and are superseded by `--scored-worksheet` once a
human has reviewed `scoring_worksheet.json`. Fact false positives are never
automatically claimed: inventing a false-positive detector would be worse than
reporting the count as unavailable pending review.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field
from typing import Literal

from kendra_api.evaluation.models import CaseRunResult, GoldCase, GoldDataset

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_FACT_MATCH_METHOD = "normalized_substring_or_token_overlap>=0.8"

# EVALUATION_METHOD.md, "Ambiguous cases": the four categories a report must
# segment ambiguous-case results into. Every gold case carries non-empty
# `ambiguity_notes` (there is no boolean "is this case ambiguous" flag in the
# dataset), and which of these four applies to a given answer requires reading it —
# there is no mechanical proxy, so this is never auto-assigned.
AMBIGUITY_CATEGORIES: tuple[str, ...] = (
    "correctly_clarified_or_bounded",
    "answer_correct_under_allowed_interpretation",
    "silently_resolved_with_material_risk",
    "non_scorable_case_needs_revision",
)


def _normalize_tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _fact_appears_in_answer(fact: str, answer: str) -> bool:
    fact_tokens = _normalize_tokens(fact)
    if not fact_tokens:
        return False
    if " ".join(fact_tokens) in " ".join(_normalize_tokens(answer)):
        return True
    answer_tokens = set(_normalize_tokens(answer))
    overlap = sum(1 for token in fact_tokens if token in answer_tokens)
    return (overlap / len(fact_tokens)) >= 0.8


def predicted_label(response_status: str) -> Literal["supported", "unsupported"]:
    return "supported" if response_status == "supported" else "unsupported"


@dataclass
class ConfusionMatrix:
    tp: int = 0
    fn: int = 0
    fp: int = 0
    tn: int = 0

    def accumulate(self, expected: str, predicted: str) -> None:
        if expected == "supported" and predicted == "supported":
            self.tp += 1
        elif expected == "supported" and predicted == "unsupported":
            self.fn += 1
        elif expected == "unsupported" and predicted == "supported":
            self.fp += 1
        else:
            self.tn += 1

    def as_dict(self) -> dict:
        total = self.tp + self.fn + self.fp + self.tn
        precision = self.tp / (self.tp + self.fp) if (self.tp + self.fp) else None
        recall = self.tp / (self.tp + self.fn) if (self.tp + self.fn) else None
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision is not None and recall is not None and (precision + recall) > 0
            else None
        )
        accuracy = (self.tp + self.tn) / total if total else None
        return {
            "true_positive": self.tp,
            "false_negative": self.fn,
            "false_positive": self.fp,
            "true_negative": self.tn,
            "accuracy": accuracy,
            "supported_precision": precision,
            "supported_recall": recall,
            "supported_f1": f1,
        }


def _latency_stats(durations_ms: list[int]) -> dict:
    if not durations_ms:
        return {"mean_ms": None, "median_ms": None, "p90_ms": None, "max_ms": None, "count": 0}
    ordered = sorted(durations_ms)
    p90_index = min(len(ordered) - 1, max(0, round(0.9 * (len(ordered) - 1))))
    return {
        "mean_ms": statistics.mean(ordered),
        "median_ms": statistics.median(ordered),
        "p90_ms": ordered[p90_index],
        "max_ms": ordered[-1],
        "count": len(ordered),
    }


def score_run(dataset: GoldDataset, results: list[CaseRunResult]) -> dict:
    cases_by_id: dict[str, GoldCase] = {case.case_id: case for case in dataset.cases}

    confusion = ConfusionMatrix()
    fact_tp = 0
    fact_fn = 0
    attempted_supported = 0
    correct_page_cases = 0
    total_citations = 0
    page_correct_citations = 0
    safe_rejections = 0
    unsupported_attempted = 0
    false_answers = 0
    timeouts = 0
    failed = 0

    by_category: dict[str, ConfusionMatrix] = {}
    by_ocr: dict[bool, ConfusionMatrix] = {}
    latency_all: list[int] = []
    latency_by_category: dict[str, list[int]] = {}
    latency_by_ocr: dict[bool, list[int]] = {}

    fact_entries: list[dict] = []
    ambiguity_entries: list[dict] = []

    for result in results:
        case = cases_by_id[result.case_id]
        ambiguity_entries.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "expected_result": case.expected_result,
                "ambiguity_notes": case.ambiguity_notes,
                "response_status": result.response_status,
                "model_answer": result.answer,
                "reviewed_category": None,
            }
        )
        latency_all.append(result.duration_ms)
        latency_by_category.setdefault(case.category, []).append(result.duration_ms)
        latency_by_ocr.setdefault(case.ocr_required, []).append(result.duration_ms)

        if result.timed_out:
            timeouts += 1
        if result.response_status in {"system_error", "source_unavailable"} or result.error:
            failed += 1

        predicted = result.predicted_label
        confusion.accumulate(case.expected_result, predicted)
        by_category.setdefault(case.category, ConfusionMatrix()).accumulate(
            case.expected_result, predicted
        )
        by_ocr.setdefault(case.ocr_required, ConfusionMatrix()).accumulate(
            case.expected_result, predicted
        )

        if case.expected_result == "unsupported":
            unsupported_attempted += 1
            # Only a clean `insufficient_evidence` counts as a safe rejection: our
            # contract guarantees that path returns the fixed unsupported sentence
            # with zero claims, so it cannot itself be a guess. A timeout or
            # system_error does not identify the missing evidence and so does not
            # count (EVALUATION_METHOD.md, Unsupported rejection rate).
            if result.response_status == "insufficient_evidence":
                safe_rejections += 1
            if result.response_status == "supported":
                false_answers += 1

        if case.expected_result == "supported":
            attempted_supported += 1
            for fact in case.expected_answer_facts:
                matched = _fact_appears_in_answer(fact, result.answer)
                fact_entries.append(
                    {
                        "case_id": case.case_id,
                        "fact": fact,
                        "provisional_label": "TP" if matched else "FN",
                        "matched_method": _FACT_MATCH_METHOD,
                        "model_answer": result.answer,
                        "reviewed_label": None,
                    }
                )
                if matched:
                    fact_tp += 1
                else:
                    fact_fn += 1

            expected_pages = case.expected_pages
            any_correct_page = False
            for citation in result.citations:
                total_citations += 1
                allowed_pages = expected_pages.get(citation.get("filename", ""), [])
                if citation.get("page") in allowed_pages:
                    page_correct_citations += 1
                    any_correct_page = True
            if any_correct_page:
                correct_page_cases += 1

    fact_recall = fact_tp / (fact_tp + fact_fn) if (fact_tp + fact_fn) else None

    return {
        "classification": confusion.as_dict(),
        "classification_by_category": {
            category: matrix.as_dict() for category, matrix in by_category.items()
        },
        "classification_by_ocr_required": {
            ("ocr_required" if key else "non_ocr"): matrix.as_dict()
            for key, matrix in by_ocr.items()
        },
        "atomic_fact_scoring": {
            "status": "provisional",
            "matching_method": _FACT_MATCH_METHOD,
            "fact_true_positive": fact_tp,
            "fact_false_negative": fact_fn,
            "fact_false_positive": None,
            "fact_false_positive_note": (
                "false positives require human judgment and are not detected "
                "automatically; see scoring_worksheet.json"
            ),
            "fact_recall": fact_recall,
            "fact_precision": None,
            "fact_f1": None,
        },
        "citation_scoring": {
            "status": "provisional_page_level_approximation",
            "note": (
                "approximates citation correctness and correct-page citation rate at "
                "page granularity only; the method's fact-to-citation association "
                "requires human review"
            ),
            "citation_precision_approx": (
                page_correct_citations / total_citations if total_citations else None
            ),
            "correct_page_citation_rate_approx": (
                correct_page_cases / attempted_supported if attempted_supported else None
            ),
        },
        "unsupported_rejection": {
            "unsupported_rejection_rate": (
                safe_rejections / unsupported_attempted if unsupported_attempted else None
            ),
            "unsupported_false_answer_rate": (
                false_answers / unsupported_attempted if unsupported_attempted else None
            ),
            "attempted": unsupported_attempted,
            "safe_rejections": safe_rejections,
            "false_answers": false_answers,
        },
        "response_time": {
            "overall": _latency_stats(latency_all),
            "by_category": {
                category: _latency_stats(values) for category, values in latency_by_category.items()
            },
            "by_ocr_required": {
                ("ocr_required" if key else "non_ocr"): _latency_stats(values)
                for key, values in latency_by_ocr.items()
            },
            "timeout_count": timeouts,
            "failed_count": failed,
        },
        "ambiguity_review": {
            "status": "pending_review",
            "note": (
                "which of the four categories applies requires reading each answer "
                "against its case's ambiguity_notes; not auto-assigned. See "
                "scoring_worksheet.json's ambiguity_entries and --scored-worksheet."
            ),
            "total_cases": len(results),
            "reviewed_count": 0,
            "categories": dict.fromkeys(AMBIGUITY_CATEGORIES, 0),
        },
        "attempted_case_count": len(results),
        "fact_worksheet_entries": fact_entries,
        "ambiguity_worksheet_entries": ambiguity_entries,
    }
