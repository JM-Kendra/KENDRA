"""EXP-01 bounded diagnostic: classify why native fallback candidates were rejected.

This script answers exactly one question and changes no policy:

    For every Docling digit-bearing token counted as "missing from native",
    is it ABSENT from the native page entirely (a real candidate conflict),
    or merely present in FEWER copies (a parser-representation surplus)?

It is read-only over approved originals, imports the shipped tokenizer so the
comparison is identical to `native-page-token-coverage-v1` by construction, and
writes derived output only under the gitignored evaluation/runs tree. stdout
carries counts only; token strings stay in the ignored evidence file.

Run inside the ingestion image so Docling/Poppler versions match the rerun:

    docker compose --profile ingestion run --rm --entrypoint python ingest \
        /workspace/scripts/exp01_conflict_taxonomy.py \
        --intake-root /intake \
        --out /workspace/evaluation/runs/EXP-01/diagnostic-conflict-taxonomy
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from kendra_api.ingestion.extraction import (
    DoclingPageTextExtractor,
    PopplerPageTextExtractor,
    _comparison_tokens,
    _high_signal_tokens,
    _meaningful_char_count,
    compare_extractions,
)

APPROVED_CORPUS = (
    "RR_02_2024_Publication.pdf",
    "RR_03_2024_VAT_Percentage_Tax.pdf",
    "RR_04_2024_Filing_Payment.pdf",
    "RR_07_2024_Invoicing_Registration.pdf",
    "RR_11_2024_Invoicing_Amendments.pdf",
    "RMC_03_2024_EOPT_Act.pdf",
    "RMC_77_2024_Invoicing_QA_OCR.pdf",
    "RR17_2024_Procurement_Monitoring_Report.pdf",
    "Registration_Checklist_Annex_A1A3.pdf",
)


@dataclass(frozen=True, slots=True)
class TokenVerdict:
    token: str
    docling_count: int
    native_count: int
    classification: str


def classify_page(
    docling_text: str, native_text: str
) -> tuple[list[TokenVerdict], dict[str, object]]:
    """Split rejected high-signal tokens into surplus vs genuinely absent."""

    docling = _comparison_tokens(docling_text)
    native = _comparison_tokens(native_text)
    docling_missing = docling - native
    high_signal_missing = _high_signal_tokens(docling_missing)

    verdicts: list[TokenVerdict] = []
    for token in sorted(high_signal_missing):
        native_count = native.get(token, 0)
        verdicts.append(
            TokenVerdict(
                token=token,
                docling_count=docling[token],
                native_count=native_count,
                # absent  -> native never saw this value at all: real conflict signal
                # surplus -> native saw it, Docling emitted extra copies: artifact
                classification="absent_from_native" if native_count == 0 else "surplus_copies",
            )
        )

    # Set-based (de-duplicated) directional view: what would a set comparison say?
    docling_set = set(docling)
    native_set = set(native)
    docling_high_signal_absent_as_set = sorted(
        _high_signal_tokens(collections.Counter({t: 1 for t in docling_set - native_set}))
    )
    native_high_signal_absent_from_docling = sorted(
        _high_signal_tokens(collections.Counter({t: 1 for t in native_set - docling_set}))
    )

    frozen = compare_extractions(docling_text, native_text)
    summary: dict[str, object] = {
        "docling_token_occurrences": sum(docling.values()),
        "native_token_occurrences": sum(native.values()),
        "docling_distinct_tokens": len(docling_set),
        "native_distinct_tokens": len(native_set),
        # Reproduces the frozen rule's inputs for cross-checking.
        "frozen_rule_coverage": round(frozen.docling_lexical_coverage_by_native, 6),
        "frozen_rule_high_signal_missing_count": len(
            frozen.docling_high_signal_missing_from_native
        ),
        "frozen_rule_native_missing_from_docling": frozen.native_tokens_missing_from_docling,
        # The deciding distinction.
        "high_signal_absent_from_native": sum(
            1 for v in verdicts if v.classification == "absent_from_native"
        ),
        "high_signal_surplus_copies": sum(
            1 for v in verdicts if v.classification == "surplus_copies"
        ),
        # What a de-duplicated, directional rule would have seen.
        "set_view_docling_high_signal_absent_from_native": len(
            docling_high_signal_absent_as_set
        ),
        "set_view_native_high_signal_absent_from_docling": len(
            native_high_signal_absent_from_docling
        ),
    }
    return verdicts, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument(
        "--artifacts-path",
        type=Path,
        default=None,
        help="Staged Docling model directory; must match the rerun configuration.",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        help="Restrict to one filename; repeatable. Defaults to the approved corpus.",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    detail_path = args.out / "conflict_taxonomy.jsonl"
    summary_path = args.out / "conflict_taxonomy_summary.json"

    docling = DoclingPageTextExtractor(artifacts_path=args.artifacts_path)
    native = PopplerPageTextExtractor(args.timeout_seconds)

    targets = tuple(args.only) if args.only else APPROVED_CORPUS
    corpus_summary: list[dict[str, object]] = []

    with detail_path.open("w", encoding="utf-8") as detail_file:
        for filename in targets:
            path = args.intake_root / filename
            if not path.is_file():
                print(f"skip missing_file {filename}", file=sys.stderr)
                continue

            page_count = len(PdfReader(path, strict=True).pages)
            docling_pages = docling.extract_pages(path, page_count)

            for page_number, docling_text in enumerate(docling_pages, start=1):
                native_text = native.extract_page(path, page_number)
                verdicts, summary = classify_page(docling_text, native_text)
                summary |= {
                    "document": filename,
                    "page_number": page_number,
                    "docling_meaningful_chars": _meaningful_char_count(docling_text),
                    "native_meaningful_chars": _meaningful_char_count(native_text),
                }
                detail_file.write(
                    json.dumps(
                        summary
                        | {
                            "rejected_high_signal_tokens": [
                                {
                                    "token": v.token,
                                    "docling_count": v.docling_count,
                                    "native_count": v.native_count,
                                    "classification": v.classification,
                                }
                                for v in verdicts
                            ]
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
                corpus_summary.append(summary)
                # Counts only on stdout; no extracted content.
                print(
                    f"{filename} page={page_number} "
                    f"coverage={summary['frozen_rule_coverage']} "
                    f"absent={summary['high_signal_absent_from_native']} "
                    f"surplus={summary['high_signal_surplus_copies']} "
                    f"set_absent={summary['set_view_docling_high_signal_absent_from_native']}"
                )

    totals = {
        "pages_examined": len(corpus_summary),
        "pages_with_any_high_signal_absent_from_native": sum(
            1 for page in corpus_summary if page["high_signal_absent_from_native"]
        ),
        "pages_with_only_surplus_copies": sum(
            1
            for page in corpus_summary
            if not page["high_signal_absent_from_native"]
            and page["high_signal_surplus_copies"]
        ),
        "pages_clean_under_set_view": sum(
            1
            for page in corpus_summary
            if not page["set_view_docling_high_signal_absent_from_native"]
        ),
    }
    summary_path.write_text(
        json.dumps({"totals": totals, "pages": corpus_summary}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(totals, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
