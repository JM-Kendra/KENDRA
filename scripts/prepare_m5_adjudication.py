#!/usr/bin/env python3
"""Create two independent Milestone 5 reviewer worksheets and an adjudication log."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_DATASET_ID = "kendra-bir-public-gold-v2"
EXPECTED_DATASET_SHA256 = "6aace5184c6778cad8c0d1972d83c99b6d3837355064ecc88dc941d86bab8f86"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def review_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "question": case["question"],
        "candidate_expected_result": case["expected_result"],
        "candidate_expected_answer_facts": case["expected_answer_facts"],
        "candidate_authoritative_filenames": case["authoritative_filenames"],
        "candidate_expected_pages": case["expected_pages"],
        "candidate_unacceptable_answer_behavior": case["unacceptable_answer_behavior"],
        "candidate_ambiguity_notes": case["ambiguity_notes"],
        "candidate_ocr_required": case["ocr_required"],
        "review": {
            "source_bytes_verified": None,
            "expected_result": "pending",
            "facts": [
                {
                    "fact": fact,
                    "accurate": None,
                    "materially_complete": None,
                    "supported_pages": [],
                    "notes": "",
                }
                for fact in case["expected_answer_facts"]
            ],
            "pages_support_claims_in_context": None,
            "missing_required_pages": [],
            "listed_but_nonsupporting_pages": [],
            "unsupported_boundary_correct": None,
            "one_reproducible_interpretation": None,
            "unacceptable_behavior_sufficient": None,
            "ambiguity_notes_sufficient": None,
            "ocr_flag_correct": None,
            "ocr_verified_against_rendered_original": None,
            "material_qualifications_or_exceptions": "",
            "proposed_correction": "",
            "disposition": "pending",
            "reviewer_notes": "",
        },
    }


def reviewer_worksheet(dataset: dict[str, Any], role: str) -> dict[str, Any]:
    qualification = (
        "BIR/tax-domain competence sufficient to judge the issuances and material qualifications"
        if role == "A"
        else "Document/evaluation competence sufficient to verify facts, pages, ambiguity, and unsupported boundaries"
    )
    return {
        "schema_version": 1,
        "worksheet_type": "independent_m5_gold_review",
        "reviewer_role": role,
        "required_qualification": qualification,
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "source_manifest_sha256": dataset["source_manifest_sha256"],
        "independence_attestation": {
            "reviewer_name": "",
            "organization_or_relationship": "",
            "qualification_basis": "",
            "reviewed_without_access_to_other_reviewer_outcomes": None,
            "review_date": "",
            "signature_or_attributable_approval_reference": "",
        },
        "cases": [review_case(case) for case in dataset["cases"]],
        "completion": {
            "all_50_cases_reviewed": None,
            "all_125_facts_reviewed": None,
            "all_pages_reviewed_against_rendered_originals": None,
            "worksheet_locked": None,
            "worksheet_locked_sha256": "",
        },
    }


def adjudication_log(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "worksheet_type": "m5_gold_adjudication",
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "source_manifest_sha256": dataset["source_manifest_sha256"],
        "reviewer_a_locked_worksheet_sha256": "",
        "reviewer_b_locked_worksheet_sha256": "",
        "adjudicator": {
            "name": "",
            "authority_basis": "",
            "decision_date": "",
            "signature_or_attributable_approval_reference": "",
        },
        "mandatory_boundary_calls": {
            "mf_01_materiality_and_effect": "pending",
            "document_identifier_page_scope": "pending",
            "sf_01_independent_observer_is_separate_gate": True,
        },
        "cases": [
            {
                "case_id": case["case_id"],
                "reviewers_agree": None,
                "disagreement": "",
                "evidence_considered": [],
                "adjudicated_disposition": "pending",
                "adjudicated_correction": "",
                "rationale": "",
            }
            for case in dataset["cases"]
        ],
        "outcome": {
            "accepted_cases": None,
            "rejected_cases": None,
            "excluded_cases": None,
            "revised_cases": None,
            "promoted_dataset_id": "",
            "promoted_dataset_sha256": "",
            "status": "open",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output_dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        dataset_bytes = args.dataset.read_bytes()
        dataset = json.loads(dataset_bytes)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot load dataset: {exc}", file=sys.stderr)
        return 1
    if not isinstance(dataset, dict):
        print("FAIL: dataset top-level value must be an object", file=sys.stderr)
        return 1

    dataset_hash = sha256_bytes(dataset_bytes)
    if dataset.get("dataset_id") != EXPECTED_DATASET_ID or dataset_hash != EXPECTED_DATASET_SHA256:
        print(
            "FAIL: worksheet generator is frozen to candidate "
            f"{EXPECTED_DATASET_ID} / {EXPECTED_DATASET_SHA256}; found "
            f"{dataset.get('dataset_id')} / {dataset_hash}",
            file=sys.stderr,
        )
        return 1
    if dataset.get("dataset_status") != "initial_expert_review_required":
        print("FAIL: candidate must still require expert review", file=sys.stderr)
        return 1
    if args.output_dir.exists():
        if not args.output_dir.is_dir():
            print(f"FAIL: output path is not a directory: {args.output_dir}", file=sys.stderr)
            return 1
        if any(args.output_dir.iterdir()):
            print(f"FAIL: refusing to overwrite non-empty output directory {args.output_dir}", file=sys.stderr)
            return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "reviewer-a.json": reviewer_worksheet(dataset, "A"),
        "reviewer-b.json": reviewer_worksheet(dataset, "B"),
        "adjudication.json": adjudication_log(dataset),
    }
    artifact_hashes: dict[str, str] = {}
    for filename, artifact in artifacts.items():
        content = canonical_bytes(artifact)
        (args.output_dir / filename).write_bytes(content)
        artifact_hashes[filename] = sha256_bytes(content)

    packet_manifest = {
        "schema_version": 1,
        "packet_type": "m5_gold_v2_independent_review",
        "dataset_id": EXPECTED_DATASET_ID,
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "source_manifest_sha256": dataset["source_manifest_sha256"],
        "artifacts": artifact_hashes,
        "status": "awaiting_independent_review",
    }
    manifest_content = canonical_bytes(packet_manifest)
    (args.output_dir / "packet-manifest.json").write_bytes(manifest_content)
    print(
        f"PASS: created independent review packet at {args.output_dir}; "
        f"packet_manifest_sha256={sha256_bytes(manifest_content)}; status=awaiting_independent_review"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
