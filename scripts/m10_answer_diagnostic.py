#!/usr/bin/env python3
"""Run all 50 gold questions against the Milestone 10 answering surface.

**This is a DIAGNOSTIC, not a preregistered run.** EXP-05 is not frozen, so this
cannot fill its `A0_PROSE_BASELINE` column and must never be retro-fitted as
evidence for or against ADR-010. It exists to show whether the single failure
observed on 2026-08-21 is isolated or a pattern, before design effort is spent.

It changes no policy and writes nothing into the repository: output lands under
`evaluation/runs/`, which is ignored.

Usage (inside the API image, on the compose network):
    python scripts/m10_answer_diagnostic.py --out /out --cases /cases.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

from kendra_api.answering.models import EXACT_UNSUPPORTED_ANSWER
from kendra_api.config import Settings
from kendra_api.main import create_app


def _summarize(records: list[dict]) -> dict:
    by_stratum: dict[str, dict[str, int]] = {}
    for record in records:
        bucket = by_stratum.setdefault(record["category"], {})
        bucket[record["status"]] = bucket.get(record["status"], 0) + 1

    unsupported = [r for r in records if r["expected_result"] == "unsupported"]
    exact = [
        r
        for r in unsupported
        if r["answer"] == EXACT_UNSUPPORTED_ANSWER
        and not r["claims"]
        and not r["citations"]
    ]
    supported = [r for r in records if r["status"] == "supported"]

    span_violations = []
    citation_violations = []
    for record in supported:
        excerpts = {c["citation_id"]: c["excerpt"] for c in record["citations"]}
        for claim in record["claims"]:
            cited = [excerpts.get(cid, "") for cid in claim["citation_ids"]]
            if not any(claim["text"] in excerpt for excerpt in cited):
                span_violations.append((record["case_id"], claim["claim_id"]))
            for cid in claim["citation_ids"]:
                if claim["text"] not in excerpts.get(cid, ""):
                    citation_violations.append((record["case_id"], cid))

    return {
        "cases": len(records),
        "by_stratum": by_stratum,
        "unsupported_total": len(unsupported),
        "unsupported_exact_sentence": len(exact),
        "unsupported_violations": [
            r["case_id"] for r in unsupported if r not in exact
        ],
        "supported_total": len(supported),
        "span_containment_violations": span_violations,
        "citation_precision_violations": citation_violations,
        "cross_document_supported": [
            r["case_id"]
            for r in supported
            if r["category"] == "cross_document_comparison"
        ],
        "single_document_cross_cases": [
            r["case_id"]
            for r in supported
            if r["category"] == "cross_document_comparison"
            and len({c["filename"] for c in r["citations"]}) < 2
        ],
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--collection", default="kendra-bir-public-gold-v1")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))["cases"]

    app = create_app(Settings(), probes=[])  # type: ignore[call-arg]
    records: list[dict] = []

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://diagnostic",
        timeout=900,
    ) as client:
        for index, case in enumerate(cases, start=1):
            started = time.monotonic()
            try:
                response = await client.post(
                    "/api/v1/questions",
                    json={
                        "question": case["question"],
                        "collection_id": args.collection,
                    },
                )
                body = response.json()
                http_status = response.status_code
                error = None
            except Exception as exc:  # recorded, never silently dropped
                body = {"status": "harness_error", "answer": "", "claims": [], "citations": []}
                http_status = 0
                error = type(exc).__name__

            record = {
                "case_id": case["case_id"],
                "category": case["category"],
                "expected_result": case["expected_result"],
                "ocr_required": case.get("ocr_required", False),
                "http_status": http_status,
                "status": body.get("status", "missing"),
                "answer": body.get("answer", ""),
                "claims": body.get("claims", []),
                "citations": body.get("citations", []),
                "limitations": body.get("limitations", []),
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "harness_error": error,
            }
            records.append(record)
            print(
                f"[{index:2d}/{len(cases)}] {record['case_id']:<16} "
                f"{record['category']:<26} -> {record['status']} "
                f"({record['elapsed_seconds']}s)",
                flush=True,
            )

    (out / "responses.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )
    summary = _summarize(records)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
