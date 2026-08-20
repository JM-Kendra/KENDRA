#!/usr/bin/env python3
"""Inventory every digit-bearing token on OCR-retained pages for reviewer comparison.

Purpose
-------
SF-01 records that ADR-007's containment detector yields zero material tokens across
every OCR-retained page, so no omission or substitution on those pages is mechanically
detectable. MF-01 is one substitution found by manual comparison. The class rate is
therefore observed=1 but measured=unknown.

This script converts "unmeasured" into a bounded manual task. It lists every
digit-bearing token the OCR path retained, with its surface form and source line, so a
reviewer can check each against the rendered original page.

What this script is NOT
-----------------------
It applies no correctness judgment and runs no second observer. It does not re-OCR, does
not compare engines, and does not flag any token as suspicious. Detecting substitution
mechanically is ADR-008's subject and ADR-008 is proposed, not accepted; pre-empting it
here with an ad-hoc detector would produce the evidence that decides its own acceptance.

It changes no policy, no criterion, and no evaluation data. It is read-only over existing
run evidence.

Output goes under evaluation/runs/ which is gitignored. Do not commit its output.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
import unicodedata

# ADR-004 tokenizer, copied verbatim from
# apps/api/src/kendra_api/ingestion/extraction.py so the inventory uses the same
# material-token definition the policy and scorer use.
_TOKEN_PATTERN = re.compile(r"\w+(?:[.,:/-]\w+)*", flags=re.UNICODE)


def _normalize(token: str) -> str:
    return re.sub(r"[^\w]", "", token, flags=re.UNICODE)


def _tokens_with_surface(text: str) -> list[tuple[str, str]]:
    """Return (normalized, surface) pairs using the ADR-004 tokenizer.

    The surface form is retained deliberately: normalization strips punctuation, so a
    corrupted `(177-2024` normalizes to `1772024` and the corruption becomes invisible.
    The reviewer compares surface forms against the page.
    """
    normalized_text = unicodedata.normalize("NFKC", text)
    pairs: list[tuple[str, str]] = []
    for match in _TOKEN_PATTERN.finditer(normalized_text.casefold()):
        surface = normalized_text[match.start() : match.end()]
        norm = _normalize(match.group())
        if norm:
            pairs.append((norm, surface))
    return pairs


def _is_material(normalized: str) -> bool:
    return any(character.isdigit() for character in normalized)


def _gold_fact_tokens(gold_path: pathlib.Path) -> set[str]:
    """Normalized digit-bearing tokens asserted by any expected fact in the gold set."""
    data = json.loads(gold_path.read_text(encoding="utf-8"))
    tokens: set[str] = set()
    for case in data.get("cases", []):
        for fact in case.get("expected_answer_facts", []) or []:
            for norm, _surface in _tokens_with_surface(fact):
                if _is_material(norm):
                    tokens.add(norm)
    return tokens


def build(run_dir: pathlib.Path, gold_path: pathlib.Path, out_dir: pathlib.Path) -> dict:
    pages = [
        json.loads(line)
        for line in (run_dir / "pages_primary.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    repeat = {
        (r["filename"], r["physical_page"]): r
        for r in (
            json.loads(line)
            for line in (run_dir / "pages_repeat.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }

    gold_tokens = _gold_fact_tokens(gold_path)
    ocr_pages = [p for p in pages if p["method"] == "tesseract"]
    ocr_pages.sort(key=lambda p: (p["filename"], p["physical_page"]))

    entries = []
    per_page_counts: dict[str, int] = {}
    determinism_mismatches = []

    for page in ocr_pages:
        key = (page["filename"], page["physical_page"])
        twin = repeat.get(key)
        if twin is None or twin.get("text_sha256") != page.get("text_sha256"):
            determinism_mismatches.append(
                {"filename": key[0], "physical_page": key[1]}
            )

        seen_on_page: collections.Counter[str] = collections.Counter()
        for line_number, line in enumerate(page["text"].splitlines(), start=1):
            for norm, surface in _tokens_with_surface(line):
                if not _is_material(norm):
                    continue
                seen_on_page[norm] += 1
                entries.append(
                    {
                        "filename": page["filename"],
                        "physical_page": page["physical_page"],
                        "source_pointer": page["source_pointer"],
                        "line": line_number,
                        "surface_form": surface,
                        "normalized": norm,
                        "line_context": line.strip(),
                        "asserted_by_a_gold_fact": norm in gold_tokens,
                        "reviewer_verdict": "",
                        "reviewer_note": "",
                    }
                )
        label = f"{page['filename']} p{page['physical_page']}"
        per_page_counts[label] = sum(seen_on_page.values())

    out_dir.mkdir(parents=True, exist_ok=True)
    worksheet = {
        "purpose": "Manual comparison of OCR-retained digit-bearing tokens against rendered originals.",
        "run_id": run_dir.name,
        "verdict_vocabulary": ["faithful", "substitution", "unreadable_in_original"],
        "instructions": (
            "Open the rendered original at the stated physical page. For each row compare "
            "surface_form against the page. Record faithful, substitution, or "
            "unreadable_in_original in reviewer_verdict. Do not alter any other field."
        ),
        "caveats": [
            "Rows are an inventory, not findings. No token here is asserted to be wrong.",
            "asserted_by_a_gold_fact is a lookup against the frozen dataset and carries no "
            "correctness implication.",
            "Do NOT use asserted_by_a_gold_fact to prioritise. The lookup matches the "
            "RETAINED token, so a token corrupted by OCR can never match a gold token and "
            "systematically reads false. The known MF-01 substitution reads false for exactly "
            "this reason. Corruptions are concentrated in the rows the flag marks false.",
            "Absence of a token cannot be seen here. This inventory measures substitution "
            "in retained text only, not omission.",
        ],
        "totals": {
            "ocr_pages": len(ocr_pages),
            "token_occurrences": len(entries),
            "distinct_normalized_tokens": len({e["normalized"] for e in entries}),
            "occurrences_asserted_by_a_gold_fact": sum(
                1 for e in entries if e["asserted_by_a_gold_fact"]
            ),
        },
        "per_page_token_counts": per_page_counts,
        "determinism_mismatches": determinism_mismatches,
        "rows": entries,
    }
    (out_dir / "worksheet.json").write_text(
        json.dumps(worksheet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# OCR digit-bearing token inventory — reviewer worksheet",
        "",
        f"Run `{run_dir.name}`. {len(ocr_pages)} OCR-retained pages, "
        f"{len(entries)} token occurrences, "
        f"{len({e['normalized'] for e in entries})} distinct.",
        "",
        "Compare `surface form` against the rendered original at the stated page.",
        "Verdict vocabulary: `faithful`, `substitution`, `unreadable_in_original`.",
        "",
        "This is an inventory, not a list of findings. No token below is asserted to be wrong.",
        "",
    ]
    current = None
    for entry in entries:
        label = f"{entry['filename']} — physical page {entry['physical_page']}"
        if label != current:
            current = label
            lines += ["", f"## {label}", "", "| line | surface form | in a gold fact | verdict |", "|---|---|---|---|"]
        star = "yes" if entry["asserted_by_a_gold_fact"] else ""
        lines.append(f"| {entry['line']} | `{entry['surface_form']}` | {star} |  |")
    (out_dir / "worksheet.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return worksheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=pathlib.Path)
    parser.add_argument(
        "--gold", type=pathlib.Path, default=pathlib.Path("evaluation/gold_cases.json")
    )
    parser.add_argument("--out-dir", required=True, type=pathlib.Path)
    args = parser.parse_args()

    result = build(args.run_dir, args.gold, args.out_dir)
    totals = result["totals"]
    print(f"OCR pages inventoried:            {totals['ocr_pages']}")
    print(f"Digit-bearing token occurrences:  {totals['token_occurrences']}")
    print(f"Distinct normalized tokens:       {totals['distinct_normalized_tokens']}")
    print(f"Occurrences in a gold fact:       {totals['occurrences_asserted_by_a_gold_fact']}")
    if result["determinism_mismatches"]:
        print(f"DETERMINISM MISMATCHES: {len(result['determinism_mismatches'])}")
    else:
        print("Determinism: primary and repeat text hashes agree on every OCR page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
