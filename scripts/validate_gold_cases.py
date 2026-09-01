#!/usr/bin/env python3
"""Validate the tracked Milestone 5 gold dataset against its approval manifest.

This validator is deliberately limited to mechanical facts. It cannot approve tax or
legal meaning, decide materiality, or replace the independent review required by the
evaluation method.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_CATEGORIES = {
    "direct_factual": 20,
    "list_or_table": 10,
    "cross_document_comparison": 10,
    "deliberately_unsupported": 10,
}
EXPECTED_RESULTS = {"supported": 40, "unsupported": 10}
EXPECTED_DOCUMENTS = 9
EXPECTED_PAGES = 41
EXPECTED_CASES = 50
EXPECTED_FACTS = 125
EXPECTED_OCR_CASES = 14
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "dataset_id",
    "supersedes_dataset_id",
    "dataset_status",
    "source_collection",
    "source_manifest_filename",
    "source_manifest_sha256",
    "source_approval_scope",
    "page_numbering",
    "documents",
    "cases",
}
PREFIX_BY_CATEGORY = {
    "direct_factual": "DF",
    "list_or_table": "LT",
    "cross_document_comparison": "CD",
    "deliberately_unsupported": "UN",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CASE_ID_RE = re.compile(r"^KND-M5-(DF|LT|CD|UN)-(\d{3})$")


class ValidationError(Exception):
    """Raised when a mechanical dataset invariant is violated."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"top-level JSON value in {path} must be an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ValidationError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_exact_keys(value: dict[str, Any], keys: set[str], location: str) -> None:
    missing = keys - value.keys()
    extra = value.keys() - keys
    require(not missing, f"{location} is missing keys: {sorted(missing)}")
    require(not extra, f"{location} has unexpected keys: {sorted(extra)}")


def validate_documents(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    documents = dataset.get("documents")
    require(isinstance(documents, list), "documents must be an array")
    require(len(documents) == EXPECTED_DOCUMENTS, "dataset must contain exactly 9 documents")

    by_filename: dict[str, dict[str, Any]] = {}
    for index, document in enumerate(documents):
        location = f"documents[{index}]"
        require(isinstance(document, dict), f"{location} must be an object")
        require_exact_keys(document, {"filename", "sha256", "pages", "format_class"}, location)
        filename = document["filename"]
        require(isinstance(filename, str) and filename.endswith(".pdf"), f"{location}.filename must name a PDF")
        require(filename not in by_filename, f"duplicate document filename: {filename}")
        require(isinstance(document["sha256"], str) and SHA256_RE.fullmatch(document["sha256"]) is not None, f"{location}.sha256 must be lowercase SHA-256")
        require(type(document["pages"]) is int and document["pages"] > 0, f"{location}.pages must be a positive integer")
        require(isinstance(document["format_class"], str) and document["format_class"], f"{location}.format_class must be non-empty")
        by_filename[filename] = document

    require(sum(document["pages"] for document in documents) == EXPECTED_PAGES, "document page total must equal 41")
    return by_filename


def validate_cases(dataset: dict[str, Any], documents: dict[str, dict[str, Any]]) -> tuple[int, Counter[str], Counter[str]]:
    cases = dataset.get("cases")
    require(isinstance(cases, list), "cases must be an array")
    require(len(cases) == EXPECTED_CASES, "dataset must contain exactly 50 cases")

    required_keys = {
        "case_id",
        "category",
        "question",
        "expected_result",
        "expected_answer_facts",
        "authoritative_filenames",
        "expected_pages",
        "unacceptable_answer_behavior",
        "ambiguity_notes",
        "ocr_required",
    }
    case_ids: set[str] = set()
    questions: set[str] = set()
    category_counts: Counter[str] = Counter()
    result_counts: Counter[str] = Counter()
    fact_count = 0
    ocr_count = 0
    cases_by_id: dict[str, dict[str, Any]] = {}

    for index, case in enumerate(cases):
        location = f"cases[{index}]"
        require(isinstance(case, dict), f"{location} must be an object")
        require_exact_keys(case, required_keys, location)

        case_id = case["case_id"]
        require(isinstance(case_id, str) and CASE_ID_RE.fullmatch(case_id) is not None, f"{location}.case_id has an invalid format")
        require(case_id not in case_ids, f"duplicate case_id: {case_id}")
        case_ids.add(case_id)
        cases_by_id[case_id] = case

        question = case["question"]
        require(isinstance(question, str) and question.strip(), f"{case_id}.question must be non-empty")
        require(question not in questions, f"duplicate question in {case_id}")
        questions.add(question)

        category = case["category"]
        require(category in EXPECTED_CATEGORIES, f"{case_id}.category is not registered")
        match = CASE_ID_RE.fullmatch(case_id)
        require(match is not None and match.group(1) == PREFIX_BY_CATEGORY[category], f"{case_id} prefix does not match category {category}")
        category_counts[category] += 1

        expected_result = case["expected_result"]
        require(expected_result in EXPECTED_RESULTS, f"{case_id}.expected_result is invalid")
        result_counts[expected_result] += 1

        facts = case["expected_answer_facts"]
        require(isinstance(facts, list) and all(isinstance(fact, str) and fact.strip() for fact in facts), f"{case_id}.expected_answer_facts must contain non-empty strings")
        require(len(facts) == len(set(facts)), f"{case_id} contains duplicate expected facts")
        fact_count += len(facts)

        filenames = case["authoritative_filenames"]
        require(isinstance(filenames, list) and filenames, f"{case_id}.authoritative_filenames must be non-empty")
        require(len(filenames) == len(set(filenames)), f"{case_id} contains duplicate authoritative filenames")
        require(all(filename in documents for filename in filenames), f"{case_id} references a document outside the dataset")

        expected_pages = case["expected_pages"]
        require(isinstance(expected_pages, dict), f"{case_id}.expected_pages must be an object")
        if expected_result == "supported":
            require(bool(facts), f"{case_id} is supported but has no expected facts")
            require(set(expected_pages) == set(filenames), f"{case_id}.expected_pages keys must exactly match authoritative_filenames")
            for filename, pages in expected_pages.items():
                require(isinstance(pages, list) and pages, f"{case_id} must identify at least one page for {filename}")
                require(all(type(page) is int for page in pages), f"{case_id} page numbers must be integers")
                require(pages == sorted(set(pages)), f"{case_id} pages for {filename} must be sorted and unique")
                require(all(1 <= page <= documents[filename]["pages"] for page in pages), f"{case_id} contains an out-of-range page for {filename}")
        else:
            require(not facts, f"{case_id} is unsupported but contains expected facts")
            require(not expected_pages, f"{case_id} is unsupported but contains expected pages")

        require(isinstance(case["unacceptable_answer_behavior"], str) and case["unacceptable_answer_behavior"].strip(), f"{case_id}.unacceptable_answer_behavior must be non-empty")
        require(isinstance(case["ambiguity_notes"], str) and case["ambiguity_notes"].strip(), f"{case_id}.ambiguity_notes must be non-empty")
        require(type(case["ocr_required"]) is bool, f"{case_id}.ocr_required must be boolean")
        ocr_count += int(case["ocr_required"])

    require(dict(category_counts) == EXPECTED_CATEGORIES, f"category counts differ: {dict(category_counts)}")
    require(dict(result_counts) == EXPECTED_RESULTS, f"result counts differ: {dict(result_counts)}")
    expected_case_ids = {
        f"KND-M5-{PREFIX_BY_CATEGORY[category]}-{number:03d}"
        for category, count in EXPECTED_CATEGORIES.items()
        for number in range(1, count + 1)
    }
    require(case_ids == expected_case_ids, "case IDs are not the complete registered category sequences")
    require(fact_count == EXPECTED_FACTS, f"expected fact total must equal 125, found {fact_count}")
    require(ocr_count == EXPECTED_OCR_CASES, f"OCR-required case total must equal 14, found {ocr_count}")

    require(cases_by_id["KND-M5-CD-003"]["expected_pages"] == {
        "RR_11_2024_Invoicing_Amendments.pdf": [1, 2],
        "RMC_77_2024_Invoicing_QA_OCR.pdf": [1, 9],
    }, "KND-M5-CD-003 does not contain the adjudication-ready v2 page correction")
    require(cases_by_id["KND-M5-CD-010"]["expected_pages"] == {
        "RMC_03_2024_EOPT_Act.pdf": [1, 2],
        "RR_04_2024_Filing_Payment.pdf": [1],
    }, "KND-M5-CD-010 does not contain the adjudication-ready v2 page correction")
    return fact_count, category_counts, result_counts


def validate_manifest(dataset: dict[str, Any], documents: dict[str, dict[str, Any]], manifest_path: Path) -> None:
    expected_hash = dataset.get("source_manifest_sha256")
    require(isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash) is not None, "source_manifest_sha256 must be lowercase SHA-256")
    actual_hash = sha256_file(manifest_path)
    require(actual_hash == expected_hash, f"approval manifest checksum mismatch: expected {expected_hash}, found {actual_hash}")

    manifest = load_json(manifest_path)
    require(manifest.get("approval_status") == "approved", "approval manifest is not approved")
    require(manifest.get("document_count") == EXPECTED_DOCUMENTS, "approval manifest document_count must equal 9")
    require(manifest.get("page_count") == EXPECTED_PAGES, "approval manifest page_count must equal 41")
    entries = manifest.get("documents")
    require(isinstance(entries, list) and len(entries) == EXPECTED_DOCUMENTS, "approval manifest must contain exactly 9 document entries")
    manifest_documents = {entry.get("filename"): entry for entry in entries if isinstance(entry, dict)}
    require(set(manifest_documents) == set(documents), "approval manifest filenames differ from dataset filenames")
    for filename, dataset_document in documents.items():
        entry = manifest_documents[filename]
        require(entry.get("sha256") == dataset_document["sha256"], f"approval manifest checksum differs for {filename}")
        require(entry.get("pages") == dataset_document["pages"], f"approval manifest page count differs for {filename}")
        require(entry.get("format_class") == dataset_document["format_class"], f"approval manifest format class differs for {filename}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="path to evaluation/gold_cases.json")
    parser.add_argument("--manifest", type=Path, help="path to the local approved APPROVAL_MANIFEST.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        dataset = load_json(args.dataset)
        require_exact_keys(dataset, EXPECTED_TOP_LEVEL_KEYS, "dataset")
        require(dataset.get("schema_version") == 1, "schema_version must equal 1")
        require(dataset.get("dataset_id") == "kendra-bir-public-gold-v2", "dataset_id must identify v2")
        require(dataset.get("supersedes_dataset_id") == "kendra-bir-public-gold-v1", "v2 must identify the superseded v1 dataset")
        require(dataset.get("dataset_status") == "initial_expert_review_required", "mechanical validation must not promote the dataset")
        require(dataset.get("source_manifest_filename") == "APPROVAL_MANIFEST.json", "source_manifest_filename is unexpected")
        require(dataset.get("source_approval_scope") == "Local Kendra AI development and evaluation only", "source approval scope is unexpected")
        require(dataset.get("page_numbering") == "One-based physical PDF page numbers", "page-numbering convention is unexpected")
        documents = validate_documents(dataset)
        fact_count, category_counts, result_counts = validate_cases(dataset, documents)
        if args.manifest:
            validate_manifest(dataset, documents, args.manifest)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(
        "PASS: mechanical gold-dataset validation only; "
        f"dataset_sha256={sha256_file(args.dataset)}; "
        f"documents={len(documents)}; pages={sum(item['pages'] for item in documents.values())}; "
        f"cases={sum(category_counts.values())}; facts={fact_count}; "
        f"supported={result_counts['supported']}; unsupported={result_counts['unsupported']}; "
        f"manifest_checked={'yes' if args.manifest else 'no'}; "
        "expert_adjudication=required"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
