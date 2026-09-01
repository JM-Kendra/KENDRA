"""Gold-dataset loading, reusing `scripts/validate_gold_cases.py` mechanical checks.

That script is a standalone repo-root tool, not part of the installed package, so it
is loaded dynamically from its known location relative to the repository root rather
than duplicated here. Duplicating its ~200 lines of mechanical validation would risk
the two drifting apart; this way there is exactly one place that decides whether the
tracked dataset is mechanically well-formed.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from kendra_api.evaluation.models import GoldCase, GoldDataset, GoldDocument, PreflightError

_VALIDATOR_RELATIVE_PATH = Path("scripts") / "validate_gold_cases.py"


def _load_validator_module(repo_root: Path) -> ModuleType:
    validator_path = repo_root / _VALIDATOR_RELATIVE_PATH
    if not validator_path.is_file():
        raise PreflightError(
            f"cannot find {validator_path}; run from the repository root "
            "or pass --repo-root"
        )
    spec = importlib.util.spec_from_file_location("kendra_validate_gold_cases", validator_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise PreflightError(f"cannot load validator module from {validator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_and_validate_dataset(
    *, dataset_path: Path, repo_root: Path, expect_dataset_sha256: str
) -> GoldDataset:
    validator = _load_validator_module(repo_root)

    try:
        raw = validator.load_json(dataset_path)
        validator.require_exact_keys(raw, validator.EXPECTED_TOP_LEVEL_KEYS, "dataset")
        documents_by_filename = validator.validate_documents(raw)
        validator.validate_cases(raw, documents_by_filename)
    except validator.ValidationError as exc:
        raise PreflightError(f"gold dataset failed mechanical validation: {exc}") from None

    actual_sha256 = validator.sha256_file(dataset_path)
    if actual_sha256 != expect_dataset_sha256:
        raise PreflightError(
            "gold dataset sha256 mismatch: "
            f"expected {expect_dataset_sha256}, found {actual_sha256}"
        )

    documents = [
        GoldDocument(
            filename=doc["filename"],
            sha256=doc["sha256"],
            pages=doc["pages"],
            format_class=doc["format_class"],
        )
        for doc in raw["documents"]
    ]
    cases = [
        GoldCase(
            case_id=case["case_id"],
            category=case["category"],
            question=case["question"],
            expected_result=case["expected_result"],
            expected_answer_facts=list(case["expected_answer_facts"]),
            authoritative_filenames=list(case["authoritative_filenames"]),
            expected_pages={k: list(v) for k, v in case["expected_pages"].items()},
            unacceptable_answer_behavior=case["unacceptable_answer_behavior"],
            ambiguity_notes=case["ambiguity_notes"],
            ocr_required=case["ocr_required"],
        )
        for case in raw["cases"]
    ]
    return GoldDataset(
        dataset_id=raw["dataset_id"],
        dataset_status=raw["dataset_status"],
        dataset_sha256=actual_sha256,
        documents=documents,
        cases=cases,
    )
