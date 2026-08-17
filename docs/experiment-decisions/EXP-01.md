# EXP-01 — Page extraction and OCR decision

**Status:** `passed`
**Run ID:** `20260817T085707+0800-3ce70b6`
**Application Git revision:** `3ce70b6604484dff0e040f87aa432e255431621d`
**Source-manifest SHA-256:** `a54c6fd4d69f02a68e793384553772a6370de6614dc870a03853ec13407cf82e`
**Evaluation-dataset SHA-256:** `a19ca426e1981a6e2ea90c7a205a52d21635947fb041b11e5f4965c4aed2f9f4`

## Decision

The preregistered Docling-first extraction and page-level Tesseract fallback passed EXP-01 on the complete approved corpus. It produced a usable, contiguous, one-based record for all 41 physical pages; used Tesseract for exactly the 12-page scanned circular and no other source; preserved every material expected fact and required full-page table/form association; and reproduced the same page identities, methods, states, and text checksums.

This is an engineering decision about faithful source representation. It is not a legal or tax interpretation, does not establish that the source remains current or controlling, and does not satisfy the dataset's outstanding expert-review requirement.

## Selected extraction and OCR configuration

The selected configuration is the frozen candidate `milestone9-meaningful-chars-40-v1`, already represented by the tracked Milestone 9 implementation in `apps/api/src/kendra_api/ingestion/extraction.py` and its non-secret defaults in `apps/api/src/kendra_api/config.py`:

- Docling `2.117.0`, PDF only, OCR disabled, table structure enabled with `TableStructureV2Options` defaults, one-based `export_to_text(page_no=physical_page, traverse_pictures=true)`, and staged local artifacts only.
- Docling layout model SHA-256 `00333a43451945aaf89db8ca9c0a17e75d1537c17db60fdb91aa95f4c7929e0c` and config SHA-256 `fdea30805ce2f5666b147fca941dcdd27ad468e27d6ed21902207d3da056a97d`.
- TableFormer v2 model SHA-256 `8a640f1e6d4c69769e8bb968bfe29596559817bf165441e1dd5c69186663aa25` and config SHA-256 `86475d3ca5e2cf73a50c9919b8ee26412524e09699bc4a7c41be40afae77cc9b`.
- Quality gate: use Docling when the Unicode word-character count is at least 40; accept a page as blank only when it has neither content-stream bytes nor XObjects; otherwise require Tesseract.
- Tesseract `5.3.0`, language `eng`, Poppler `pdftoppm 22.12.0`, 300 DPI, and a 300-second timeout for each rendering/OCR subprocess.
- Maximum PDF size 50 MiB and maximum page count 500.
- CPU-only Docker execution, concurrency one, no experiment-time network, eight allocated CPUs, and 8,321,798,144 allocated memory bytes.

No new tracked extraction configuration is introduced by this decision because EXP-03 failed and the acceptance request permits tracked configuration changes only when both experiments pass.

## Measurements

| Measurement | Result |
|---|---:|
| Approved sources verified | 9/9 |
| Manifest physical pages | 41 |
| Primary page records | 41 |
| Repeat page records | 41 |
| Missing pages | 0 |
| Duplicate page identities | 0 |
| Usable / blank / failed states | 41 / 0 / 0 |
| Docling / Tesseract pages | 29 / 12 |
| Scanned-circular pages using Tesseract | 12/12 |
| Other pages using Tesseract | 0 |
| Required document/page pairs inspected | 23/23 |
| Supported cases reviewed | 40/40 |
| Material expected facts reviewed | 125/125 |
| Material fact changes | 0 |
| Repeat identity/method/state mismatches | 0 |
| Repeat text-checksum mismatches | 0 |
| Primary summed document time | 759.59 seconds |
| Repeat summed document time | 1,697.95 seconds |
| Peak container RSS | 3,380,120 KiB |

All 41 originals were rendered. The 23 distinct physical pages referenced by supported gold cases were visually compared with the extracted page evidence.

## Criterion results

| Preregistered criterion | Result | Evidence |
|---|---|---|
| All nine checksums and page counts match | Pass | `source_preflight.json` records exact checksum, byte-size, page-count, and encryption checks. |
| Exactly 41 contiguous records; zero missing or duplicate pages | Pass | 41 primary and 41 repeat records; zero missing and duplicate identities. |
| All 12 scanned pages trigger OCR | Pass | Every page of `RMC_77_2024_Invoicing_QA_OCR.pdf` used Tesseract. |
| No undeclared OCR use | Pass | The other 29 pages used Docling. |
| Explicit state for every nonblank page | Pass | All 41 pages are explicitly `usable`; no blank or failed state was inferred. |
| Expected-page mapping is 100% | Pass | All 23 distinct required document/page pairs for all 40 supported cases were present and inspected. |
| Zero material expected-fact changes | Pass | 125/125 facts were compared for names, dates, amounts, thresholds, negation, conditions, exceptions, and list membership; zero meaning-changing differences were found. |
| Required table/form context remains interpretable | Pass | At full-page scope, the required row/header/value and form-section/item associations were reviewable against rendered originals. |
| Selected run repeats identities, methods, and states | Pass | Zero identity/method/state mismatch; text checksums also matched. |

## Independent Milestone 9 ingestion review

No material defect was found that made the approved-corpus EXP-01 or EXP-03 execution unsafe. The review covered filename/path confinement, symlinks and storage-root escape, PDF validation and limits, immutable byte preservation, duplicate/concurrent behavior, PostgreSQL transactions, Qdrant partial failures, page identity, chunk boundaries, OCR, logs, network boundaries, and Git exclusions. The complete backend suite passed before experimentation.

Two non-blocking operational limitations remain visible in the reviewed revision:

1. `IngestionPipeline.ingest()` returns any checksum match as a duplicate, including a version already in `failed` state (`apps/api/src/kendra_api/ingestion/pipeline.py`, duplicate return at lines 58–70). Recovery therefore needs an explicit future administrative/retry design; replaying the same file does not automatically retry it.
2. `QdrantGenerationStore.discard()` suppresses deletion errors (`apps/api/src/kendra_api/ingestion/vector_store.py`, lines 73–77). A failed cleanup can leave an inactive orphan collection. The registry's active pointer is not published in that failure path, so this did not expose a partial generation or invalidate these experiments, but operational cleanup/alerting remains future work.

These findings do not authorize expansion into question answering.

## Discrepancies and limitations

- Docling's full-page representation of several dense tables contains extreme fixed-width Markdown padding and repeated cell text. The required facts and table associations remain interpretable at full-page scope, so this is not an EXP-01 fact or page failure. It is a downstream chunk-context risk and was evaluated independently in EXP-03.
- Tesseract introduced cosmetic recognition noise in stamps, headers, punctuation, and capitalization. No required amount, date, threshold, negation, condition, list member, question/answer boundary, or page attribution changed.
- `evaluation/gold_cases.json` remains `initial_expert_review_required`. This review checked representation fidelity only. Source authenticity, authority, currency, applicability, and legal/tax meaning remain outside this decision.
- The experiment used the registered workstation and pinned local artifacts. Results are not automatically generalized to different Docling/Tesseract/model/runtime versions.

## Evidence

Generated evidence is ignored by Git under:

`evaluation/runs/EXP-01/20260817T085707+0800-3ce70b6/`

Principal artifacts are `registration.json`, `registration.sha256`, `harness-registration.json`, `repeat-harness-registration.json`, `source_preflight.json`, `pages_primary.jsonl`, `pages_repeat.jsonl`, `timings_primary.jsonl`, `timings_repeat.jsonl`, `extraction_summary.json`, `reviewer_worksheet.json`, `evidence_manifest.json`, and `rendered-originals/`.

## Consequences

- The selected extraction/OCR configuration is accepted for these four approved format strata at the evaluated revision.
- The table-padding discrepancy must not be assumed safe for retrieval-sized character chunks.
- EXP-01 alone does not unblock EXP-02 or Milestone 10. EXP-03 must also pass.
- No PDF, extracted text, OCR output, rendering, or experiment-run artifact belongs in Git.
