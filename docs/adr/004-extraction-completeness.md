# ADR-004: Independent PDF extraction completeness gate

**Status:** Accepted only as fail-closed interim containment; EXP-01 candidate failed
**Date:** 2026-08-17
**Acceptance basis:** Owner-authorized bounded extraction repair after contradictory source evidence invalidated the first EXP-01 result

## Context

The first EXP-01 run accepted a Docling page when its exported text contained at least 40 Unicode word characters. On physical page 15 of `RR17_2024_Procurement_Monitoring_Report.pdf`, Docling/TableFormer produced a structurally valid table that ended above the visible summary row. The exported page therefore omitted the ongoing-procurement totals `175,284,574.00` and `169,021,829.87`, although both values remained present in the immutable original and its native PDF text layer.

A parser success and a minimum text quantity do not prove page completeness. The architecture needs an independent local observation while retaining the original bytes and physical page as authority.

## Decision

Adopt the frozen `native-page-token-coverage-v1` policy:

1. Docling continues to produce the layout-aware page candidate with internal OCR disabled.
2. Poppler `pdftotext -layout -nopgbrk` independently reads the same one-based physical page.
3. Both candidates are Unicode NFKC-normalized and compared as case-folded token multisets with punctuation removed inside tokens.
4. Docling is retained only when it covers every native token occurrence.
5. If native text contains material tokens absent from Docling, retain the entire native page block only when it covers every Docling digit-bearing token and at least 90% of Docling token occurrences. Record `pdf_text` as the method. Do not merge candidates.
6. If the native layer is unusable, use whole-page Tesseract OCR under the existing minimum-character rule. When Docling itself was usable, require the same high-signal and 90% agreement rule before retaining OCR.
7. If candidates materially conflict, or OCR cannot recover a nonblank page, fail the ingestion with a content-free error. Do not publish derived records.

The retained extraction block is the whole physical PDF page. Its mechanically verifiable pointer is `pdf-page:<one-based-number>;block:whole-page;method:<method>`. Chunks inherit that page identity and extraction method. Original PDF bytes and their checksum remain authoritative.

The versioned runtime configuration is:

- `KENDRA_EXTRACTION_COMPLETENESS_POLICY=native-page-token-coverage-v1`
- `KENDRA_MINIMUM_PAGE_TEXT_CHARS=40`
- `KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT=0.90`

Only the named policy is accepted by typed configuration. A threshold or algorithm change requires a new policy version, tests, and experiment registration.

## Consequences

### Positive

- Docling success alone can no longer establish completeness.
- The known page-15 omission deterministically selects the complete native page without synthesizing or merging text.
- Every retained page block has one method and a source-resolvable physical-page pointer.
- Conflicts and unrecoverable pages fail closed before derived records are published.
- The scanned no-text-layer stratum continues to use Tesseract.

### Negative and limitations

- Poppler becomes a required local extraction dependency and adds one page-level subprocess per page.
- Token agreement detects textual omissions but does not prove visual/layout completeness or semantic correctness.
- A complete native text layer can preserve text while representing columns less explicitly than Docling. Full-page source resolution and later layout-aware chunking remain necessary.
- Tesseract remains derived assistance and can introduce recognition error.
- This decision validates engineering representation only. It does not establish source authority, currency, applicability, or legal/tax interpretation.

## EXP-01 rerun outcome

The frozen `native-page-token-coverage-v1` candidate failed run
`20260817T111818+0800-b6036ba-repair1`. It safely rejected unresolved Docling/native
differences in three digital documents, leaving only 20 of 41 physical pages retained.
The native page-15 candidate contained both previously omitted totals, but the same
conflict rule rejected that candidate; it therefore did not become an accepted page
representation. The policy remains useful as conservative containment because it
prevents publication of known-incomplete or unresolved text, but it is not an accepted
EXP-01 extraction configuration. A future candidate requires a new architecture
decision and preregistration; this ADR does not authorize threshold weakening or
post-result merging.

## Alternatives considered

### Keep the 40-character Docling gate

Rejected because it already accepted a page with a material visible row missing.

### Merge missing native lines into Docling output

Rejected because inferred alignment can silently combine conflicting candidates and obscure block provenance.

### OCR every page

Rejected because a usable native text layer is more direct, deterministic, and less error-prone for digital PDFs.

### Add another layout parser

Deferred. The native layer supplies the smallest independent completeness detector for the observed defect. Another parser would add a broader architecture and validation burden.

## Validation required

- regression coverage for the page-15 row, both omitted totals, page pointer, conflict failure, contiguous numbering, deterministic repeat, OCR behavior, immutable originals, and content-free errors;
- a frozen EXP-01 registration before complete-corpus processing or scoring;
- two complete 9-document/41-page extraction passes with matching identities, methods, source pointers, and text checksums;
- source-page review of every gold fact and required table/form relationship; and
- EXP-03 remains blocked until the repaired EXP-01 passes. A passing EXP-01 permits layout-aware EXP-03 work to resume but does not itself pass EXP-03 or unblock Milestone 10.
