# EXP-01 - Page extraction and OCR decision

**Status:** `failed`
**Current run ID:** `20260817T111818+0800-b6036ba-repair1`
**Prior invalidated run ID:** `20260817T085707+0800-3ce70b6`
**Application Git revision:** `b6036ba1c1cbf8e06bfb690bf6a1482e466899c4`
**Authorized repair patch SHA-256:** `157182f658778df58dd60b1368dfa2a81d54ef2103da210535eb0c2fe3e5b55c`
**Frozen registration SHA-256:** `f90c588aa6ca49d19d6e0099a3f7312b13131a58b638e562d3cad056ffe4d025`
**Source-manifest SHA-256:** `a54c6fd4d69f02a68e793384553772a6370de6614dc870a03853ec13407cf82e`
**Evaluation-dataset SHA-256:** `a19ca426e1981a6e2ea90c7a205a52d21635947fb041b11e5f4965c4aed2f9f4`

## Decision

EXP-01 is failed. The original passing decision is invalidated, and the bounded repair
candidate did not produce an acceptable complete-corpus representation. EXP-03 remains
failed and blocked; Milestone 10 remains blocked.

The fail-closed repair is retained as interim containment: it is safer to reject a page
than to publish known-incomplete or materially conflicting derived text. It is not a
selected passing extraction configuration. A future repair requires a new versioned
policy, architecture change control, tests, and preregistered run.

This remains an engineering representation decision only. It does not establish source
authenticity, authority, currency, applicability, or legal/tax meaning, and it does not
change `evaluation/gold_cases.json` from `initial_expert_review_required`.

## Original-run invalidation

The decision recorded for run `20260817T085707+0800-3ce70b6` claimed 125/125 material
expected facts were retained with zero material fact loss. Newly discovered source
evidence contradicts that conclusion:

- `KND-M5-DF-013` requires physical page 15 of
  `RR17_2024_Procurement_Monitoring_Report.pdf` to retain total allotted budget
  `175,284,574.00` and total contract cost `169,021,829.87`.
- Both totals are visible in the immutable approved original and present in its native
  PDF text layer.
- Neither total is present anywhere in the prior accepted page records.
- The prior page-15 record was nevertheless marked usable with method `docling`.

The 125/125 statement was incorrect because review treated a visually inspectable
original plus a nonempty full-page extraction as evidence that every expected fact was
retained. It did not mechanically verify each expected fact against the accepted page
text. The old run and its recorded claim remain preserved under the ignored evidence
directory; this decision identifies the contradiction instead of deleting or rewriting
history.

## Root cause

Docling/TableFormer identified the dense page-15 table as a valid 11-row, 22-column
structure whose bounding box ended immediately above the visible summary row. The
summary row was absent from both structured table cells and other Docling document
items, so `export_to_text(page_no=15)` could not include it.

The Milestone 9 gate then made the design error decisive: it accepted any Docling page
with at least 40 Unicode word characters. Page 15 greatly exceeded that quantity, so
the pipeline interpreted parser success and text volume as completeness and never
invoked an independent observation or fallback.

## Repair candidate

[ADR-004](../adr/004-extraction-completeness.md) introduced the frozen
`native-page-token-coverage-v1` candidate before the rerun:

- Docling and Poppler `pdftotext -layout -nopgbrk` independently observe the same
  one-based physical page.
- Comparison uses Unicode NFKC-normalized, case-folded token multisets.
- Docling is retained only when it covers every native token occurrence.
- Otherwise the entire native page, never a merged output, may be retained only when
  it covers every Docling digit-bearing token and at least 90% of Docling token
  occurrences.
- Pages without usable native text use whole-page Tesseract under the existing
  minimum-character rule.
- Every retained whole-page block records one extraction method and a mechanically
  verifiable `pdf-page:<n>;block:whole-page;method:<method>` pointer.
- Unresolved disagreement fails closed without logging extracted content.

The exact revision, patch, file checksums, candidates, versions, model checksums,
configuration, hardware, timeouts, rubric, and decision rule were frozen in
`registration.json` before corpus processing or scoring. No post-result candidate or
weaker threshold was introduced.

## Measurements

| Measurement | Primary | Repeat |
|---|---:|---:|
| Approved documents attempted | 9 | 9 |
| Manifest physical pages | 41 | 41 |
| Retained page records | 20 | 20 |
| Missing page records | 21 | 21 |
| Duplicate page identities | 0 | 0 |
| Docling pages | 5 | 5 |
| Native PDF text pages | 3 | 3 |
| Tesseract pages | 12 | 12 |
| Scanned-circular pages using Tesseract | 12/12 | 12/12 |
| Documents failing on an unresolved conflict | 3 | 3 |
| Mismatches among retained repeat records | 0 | 0 |
| Source checksum changes | 0/9 | 0/9 |

Both passes failed at physical page 1 of the same documents:

- `RR_11_2024_Invoicing_Amendments.pdf`;
- `RMC_03_2024_EOPT_Act.pdf`; and
- `RR17_2024_Procurement_Monitoring_Report.pdf`.

Because extraction is document-atomic, those failures account for all 21 missing page
records. The other six documents produced 20 deterministic records. All 12 pages of
the scanned circular remained on the Tesseract path.

## Conflict diagnostics

The repair failed because Docling's layout export and Poppler's native text are not
token-multiset substitutes. Docling can repeat table cells and emit expanded layout
content, while Poppler can order or tokenize the same physical content differently.
The frozen high-signal rule therefore rejected these page-1 native fallbacks:

| Document | Docling token coverage by native | Docling digit-bearing tokens absent from native |
|---|---:|---:|
| RR 11-2024 amendments | 96.38% | 2 |
| RMC 03-2024 EOPT Act | 2.72% | 29 |
| RR17 procurement report | 28.94% | 149 |

This is safe behavior under the preregistered rule, but it is too conservative to
produce complete-corpus evidence. Changing the threshold or suppressing high-signal
differences after seeing these results would violate the candidate freeze.

## Previously omitted page-15 totals

The bounded diagnostic confirms that the native physical-page-15 candidate contains
both `175,284,574.00` and `169,021,829.87`; the prior Docling representation contains
neither. However, page 15 has only 81.02% Docling-token coverage by native and 22
Docling digit-bearing tokens absent from native. Under the frozen rule its predicted
outcome is therefore `extraction_conflict`, not `pdf_text`.

Accordingly, this run did **not** create an accepted page-15 representation or accepted
page-15 provenance for either total. The regression test proves the intended
whole-page native fallback and pointer when candidates satisfy the agreement rule, but
that synthetic proof cannot substitute for the failed corpus observation.

## Criterion results

| Preregistered criterion | Result | Evidence |
|---|---|---|
| All nine source checksums, sizes, page counts, and encryption states match before and after | Pass | Nine preflight and nine postflight observations match; original bytes are unchanged. |
| Exactly 41 contiguous unique physical pages are represented | **Fail** | 20/41 retained; 21 missing. |
| Zero missing or duplicate pages | **Fail** | 21 missing; 0 duplicate. |
| Every visible material expected fact is retained | Not scored after hard failure | Three failed documents have no accepted representation; 125-fact completeness cannot be claimed. |
| Known page-15 totals are retained with page-15 provenance | **Fail** | Both are present in native text, but the frozen rule rejects the candidate; no accepted page-15 record exists. |
| Expected-page mapping is 100% | **Fail** | 21 physical pages are absent from the accepted representation. |
| No extracted value materially differs from the original | Inconclusive | Full-corpus comparison is impossible without accepted records for 21 pages. |
| Required table/form relationships remain source-resolvable | **Fail** | The procurement document has no accepted page records, including page 15. |
| Methods and provenance are explicit | Pass for retained subset only | 20/20 retained blocks record method and whole-page pointer; corpus criterion still fails. |
| Deterministic complete repeat matches | **Fail** | The 20 retained records match, but neither pass is complete. |
| Unresolved conflicts fail closed | Pass as safety behavior | The same three documents fail with `extraction_conflict` in both passes. |
| Scanned 12-page circular uses OCR | Pass | 12/12 physical pages use Tesseract. |

The 40 supported cases and 125 material facts were not rescored after the hard
representation gate failed. Scoring only the retained subset could not meet the
preregistered every-page/every-fact rule and would risk repeating the invalid 125/125
claim. This absence is recorded as failed/inconclusive evidence, not converted into a
pass.

## Regression and backend tests

The complete API suite passed: 36 tests in 6.88 seconds. New coverage establishes:

- missing structured content triggers native whole-page fallback in an eligible case;
- both known totals appear in that accepted representation with a page-15 pointer;
- materially conflicting candidates raise `extraction_conflict`;
- physical pages remain contiguous and one-based;
- repeated extraction records are deterministic;
- a 12-page scanned fixture remains on the Tesseract path;
- source bytes remain unchanged; and
- extracted-content markers do not appear in errors or captured logs.

These tests validate implementation behavior, not corpus acceptance.

## Limitations and next decision

- Token-multiset agreement cannot by itself distinguish harmless parser representation
  differences from a material source conflict.
- A future design likely needs region-aware structured/native reconciliation or another
  independently validated representation, with explicit per-region provenance and no
  silent merge. This result does not authorize a particular approach.
- No retrieval or question-answering behavior was implemented or evaluated.
- The original PDF remains the only authority; all extracted text and diagnostics are
  ignored derived evidence.
- EXP-03 may **not** resume from this result. It remains failed and blocked pending a
  future passing EXP-01 extraction configuration.

## Bounded conflict-taxonomy diagnostic and ADR-005 rejection (2026-08-19)

[ADR-005](../adr/005-material-token-omission.md) proposed a directional distinct-token
gate (`material-token-omission-v1`) with a four-part activation condition fixed at
drafting time, before its Section 2 diagnostic was run. The diagnostic
(`scripts/exp01_conflict_taxonomy.py`, pinned ingestion image, `docling-slim==2.117.0`)
classified every Docling digit-bearing token counted missing from native on the three
failing documents as either `absent_from_native` (native never saw it) or
`surplus_copies` (native saw it in fewer copies).

Results, with per-page detail recorded in ADR-005 Section 12:

- Of 844 rejected high-signal token classifications across the three documents, 843 are
  `surplus_copies` and one is `absent_from_native`: a bare digit `3` on physical page 1
  of `RR_11_2024_Invoicing_Amendments.pdf` (Docling count 2, native count 0). Inspection
  confirmed it is not a normalization artefact — native page 1 has no standalone `3`
  token under the shipped tokenizer.
- Procurement physical page 15 classified entirely as `surplus_copies`, and both known
  totals are present in the native candidate's token set, once each.
- The RMC 03-2024 2.72%-coverage anomaly is duplication within the correct physical
  page, not `export_to_text(page_no=...)` page-scope leakage: Docling's page-1 distinct
  tokens are a strict subset of native page 1's and include none of the 104 tokens
  unique to native page 2. The duplication magnitude — 13,592 Docling token occurrences
  against 394 native, ~34.5×, from a smaller distinct vocabulary — remains unexplained
  and is carried as an open item.

ADR-005's activation condition 3.1 required **zero** `absent_from_native` material
tokens. The single RR 11-2024 token fails it. Conditions 3.2 and 3.3 passed; 3.4 passed
on the leakage question. Per ADR-005 Section 9, the ADR is **closed as rejected**, and
the precommitted zero threshold was not revisited after seeing the output.

Consequences:

- `native-page-token-coverage-v1` (ADR-004) remains in force as fail-closed containment.
- **EXP-01 remains failed. EXP-03 remains failed and blocked. Milestone 10 remains
  blocked.**
- The pre-written ADR-005 Section 7 regression file
  `apps/api/tests/test_ingestion_material_token_omission.py`, committed before the
  diagnostic so its content could not be shaped by the result, is deleted together with
  the rejection record per its own instruction. The backend suite returns to its 36-test
  passing baseline.
- The next design direction — region-aware structured/native reconciliation with
  per-region provenance — requires its own ADR with a precommitted activation condition.

## Evidence

The original invalidated evidence remains ignored under:

`evaluation/runs/EXP-01/20260817T085707+0800-3ce70b6/`

The new ignored evidence is under:

`evaluation/runs/EXP-01/20260817T111818+0800-b6036ba-repair1/`

The 2026-08-19 conflict-taxonomy diagnostic evidence is under:

`evaluation/runs/EXP-01/diagnostic-conflict-taxonomy/` and
`evaluation/runs/EXP-01/diagnostic-conflict-taxonomy-rmc03-rr11/`

(`conflict_taxonomy.jsonl` with raw token strings, `conflict_taxonomy_summary.json`).

Principal artifacts of the rerun are `registration.json`, `registration.sha256`,
`source_preflight_before.json`, `source_preflight_after.json`,
`pages_primary.jsonl`, `pages_repeat.jsonl`, `timings_primary.jsonl`,
`timings_repeat.jsonl`, `extraction_summary.json`, `conflict_diagnostics.json`,
`known_totals_diagnostic.json`, `reviewer_worksheet.json`, and
`evidence_manifest.json`.
