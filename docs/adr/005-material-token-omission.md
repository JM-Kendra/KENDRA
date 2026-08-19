# ADR-005: Directional material-token omission gate

**Status:** Rejected. **Closed 2026-08-19 under Section 9** after the bounded
conflict-taxonomy diagnostic failed activation condition 3.1. The closure record and full
diagnostic dataset are in Section 12. `native-page-token-coverage-v1` (ADR-004) remains in
force as fail-closed containment.
**Date drafted:** 2026-08-19
**Date closed:** 2026-08-19
**Supersedes if accepted:** [ADR-004](004-extraction-completeness.md) `native-page-token-coverage-v1`
**Drafting basis:** Analysis of the failed EXP-01 rerun `20260817T111818+0800-b6036ba-repair1`

> This record was drafted **before** the diagnostic was run, and its activation condition
> was fixed at drafting time. It exists so that the decision rule is committed in advance
> of seeing results, not selected afterwards. If the diagnostic outcome does not satisfy
> Section 3, this ADR is closed as rejected and the fallback in Section 9 applies. No
> threshold in this record may be altered after diagnostic output is examined.

## 1. Context

ADR-004 adopted `native-page-token-coverage-v1`. Its EXP-01 rerun failed: 20 of 41
physical pages retained, three digital documents failing repeatably at page 1, and no
accepted representation for physical page 15 of
`RR17_2024_Procurement_Monitoring_Report.pdf` despite the native candidate containing
both required totals `175,284,574.00` and `169,021,829.87`.

The recorded conflict diagnostics were:

| Document | Docling token coverage by native | Docling digit-bearing tokens absent from native |
|---|---:|---:|
| RR 11-2024 amendments | 96.38% | 2 |
| RMC 03-2024 EOPT Act | 2.72% | 29 |
| RR17 procurement report | 28.94% | 149 |
| RR17 physical page 15 | 81.02% | 22 |

### 1.1 Suspected defect

EXP-01 asks a **directional** question: does the retained representation omit material
content visible in the original? The ADR-004 rule answers a **symmetric** question:
do the two candidates agree as token multisets?

Two consequences follow from that mismatch:

1. The gate rejects the native candidate whenever *Docling* holds digit-bearing tokens
   native lacks. Docling surplus is not evidence that native omitted anything.
2. `_comparison_tokens` returns a `collections.Counter`. Multiset subtraction cannot
   distinguish a token native **never saw** from a token native saw **fewer times**. One
   duplicated table cell scores identically to a genuinely lost value.

A layout-aware parser structurally produces surplus against a flat text-layer dump:
TableFormer replicates spanning and merged cell values across their span,
`traverse_pictures=True` emits picture-embedded text in addition to the main flow, and
layout export repeats row labels and header blocks per column group.

This diagnosis is a **hypothesis**. It is not established by the rerun evidence, and this
ADR does not assume it.

### 1.2 Unexplained observation

A 97% coverage shortfall on RMC 03-2024 is not two observers disagreeing about one
physical page. It indicates Docling emitted roughly an order of magnitude more token
occurrences than Poppler for the same page — consistent with either heavy duplication or
`export_to_text(page_no=...)` returning content beyond the requested physical page in
the pinned Docling version. This is a **separate, unresolved defect** and is treated as a
blocking precondition in Section 3, not as something the new rule may absorb.

## 2. Bounded diagnostic (prerequisite, no policy change)

`scripts/exp01_conflict_taxonomy.py` classifies every Docling digit-bearing token counted
missing from native into exactly one of:

- `absent_from_native` — native's token set does not contain it at all;
- `surplus_copies` — native contains it, with fewer occurrences than Docling.

The script imports the shipped tokenizer so its normalization is identical to
`native-page-token-coverage-v1` by construction. It is read-only over approved originals,
writes only under the gitignored `evaluation/runs/` tree, and confines token strings to
the ignored evidence file. It changes no runtime behaviour and activates no policy.

Before the classification is trusted, the raw token strings in
`conflict_taxonomy.jsonl` must be inspected for normalization artefacts — differing
thousands separators, spacing, or currency glyphs between the two parsers would cause the
same printed value to be labelled `absent_from_native` when the parsers do not in fact
disagree. Any such artefact is a tokenizer defect and must be fixed and re-diagnosed
before Section 3 is evaluated.

## 3. Activation condition (fixed at drafting time)

This ADR may be accepted **only if all four hold**:

1. **Surplus-dominant.** Across the three failing documents, every page whose only
   rejection cause was `docling_high_signal_missing_from_native` classifies as
   `surplus_copies`, with **zero** `absent_from_native` material tokens.
2. **Page 15 resolves.** Physical page 15 of the procurement report yields zero
   `absent_from_native` material tokens, and both required totals are present in the
   native candidate's token set.
3. **No normalization artefacts.** Section 2 inspection finds no tokenizer-induced false
   `absent_from_native` classifications, or they are fixed and the diagnostic rerun.
4. **Page scoping confirmed.** The RMC 03-2024 occurrence-ratio anomaly in Section 1.2 is
   explained and shown to be duplication within the correct physical page, not page-scope
   leakage from `export_to_text(page_no=...)`. If it is leakage, this ADR is rejected:
   the defect is in page identity, which is a binding invariant, and no comparison rule
   may compensate for it.

If any condition fails, Section 9 applies.

## 4. Decision (conditional)

Adopt the frozen `material-token-omission-v1` policy.

1. Docling produces the layout-aware page candidate with internal OCR disabled.
2. Poppler `pdftotext -layout -nopgbrk` independently reads the same one-based physical
   page.
3. Both candidates are Unicode NFKC-normalized and case-folded with punctuation removed
   inside tokens, using the tokenizer unchanged from ADR-004.
4. A **material token** is a token containing at least one digit. This is unchanged from
   ADR-004's high-signal definition.
5. Comparison is over **distinct-token sets**, not multisets. Occurrence counts are
   recorded as diagnostics and carry no decision weight.
6. Define the **observed material set** as the union of the material token sets of both
   candidates. This is the working proxy for material content visible on the page.
   Neither candidate is treated as ground truth.
7. A candidate is **retainable** only if its material token set contains the entire
   observed material set, **and** its distinct-token set covers at least
   `KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT` of the other candidate's distinct
   tokens.
8. Preference order among retainable candidates is Docling, then native, then Tesseract.
   Docling is preferred where retainable because it preserves layout relationships that
   later chunking requires.
9. Pages without a usable native text layer use whole-page Tesseract under the existing
   minimum-character rule, evaluated against the same retainability test.
10. If no candidate is retainable, fail closed with a content-free `extraction_conflict`.
    Candidates are never merged.

The retained block remains the whole physical PDF page. Its pointer remains
`pdf-page:<one-based-number>;block:whole-page;method:<method>`. Original PDF bytes and
their checksum remain authoritative.

### 4.1 Threshold provenance

`KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT` remains **0.90**, carried over unchanged
from ADR-004. It is not re-tuned. Its denominator changes from token occurrences to
distinct tokens as a direct consequence of Section 4.5, not as a calibration choice. No
value in this record was selected by reference to rerun or diagnostic output.

### 4.2 Versioned runtime configuration

- `KENDRA_EXTRACTION_COMPLETENESS_POLICY=material-token-omission-v1`
- `KENDRA_MINIMUM_PAGE_TEXT_CHARS=40`
- `KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT=0.90`

Only the named policy is accepted by typed configuration. `native-page-token-coverage-v1`
remains a valid configuration value and remains available as containment. A threshold or
algorithm change requires a new policy version, tests, and experiment registration.

## 5. Why this is a correction and not a weakening

The change is directional, not permissive. Under `material-token-omission-v1`:

- a candidate missing **any** material token the other observer saw is still rejected;
- the page-15 Docling candidate is still rejected, because native holds two material
  tokens Docling lacks;
- unresolved disagreement still fails closed with no merge;
- what stops being fatal is a candidate holding **fewer copies** of a token both
  observers saw, which was never evidence of omission.

The rule is strictly stricter in one respect: retention now requires covering the union
of both observers' material tokens, where ADR-004 required only that the retained native
candidate cover Docling's. A page where each candidate holds material tokens the other
lacks fails under both rules.

## 6. Consequences

### Positive

- Parser representation differences no longer masquerade as source conflicts.
- The known page-15 omission is detected and the complete candidate retained, without
  synthesis or merge.
- Every retained block still carries one method and a source-resolvable pointer.
- Fail-closed behaviour on genuine disagreement is preserved.

### Negative and limitations

- Set comparison cannot detect a candidate that repeats a material value the wrong number
  of times. Repetition-sensitive facts are therefore **not** covered by this gate and
  must be caught by gold-case scoring against the original page.
- Material tokens are digit-bearing only. A materially omitted **word** — a negation, a
  scope qualifier, an exemption clause — is caught only by the 0.90 lexical floor, which
  is a coarse instrument. This is a known and accepted gap at this milestone.
- Token agreement still proves nothing about visual or layout completeness, table
  structure, or semantic correctness.
- Poppler remains a required local dependency with one subprocess per page.
- Tesseract remains derived assistance and can introduce recognition error.
- This decision validates engineering representation only. It establishes no source
  authority, currency, applicability, or legal or tax interpretation.

## 7. Regression coverage required before activation

In addition to the ADR-004 suite, which must continue to pass unchanged:

- a candidate holding surplus copies of a material token both observers saw is retained;
- a candidate missing a material token the other observer saw is rejected;
- a page where each candidate holds material tokens the other lacks fails closed;
- page 15 fixtures retain `175,284,574.00` and `169,021,829.87` with page-15 provenance;
- the union rule is enforced against a three-candidate Docling/native/OCR fixture;
- preference order selects Docling when both Docling and native are retainable;
- physical pages remain contiguous and one-based;
- repeated extraction remains deterministic;
- the 12-page scanned circular remains wholly on the Tesseract path;
- original bytes are unmodified;
- no extracted content or secret appears in errors or captured logs.

## 8. Preregistration required before rerun

A new ignored run registration frozen before any corpus processing or scoring, recording:
prior invalidated run IDs `20260817T085707+0800-3ce70b6` and
`20260817T111818+0800-b6036ba-repair1`; current Git revision; source-manifest and
evaluation-dataset checksums; the exact retainability rule; all candidates with versions,
model checksums, and configuration; conflict and fail-closed rules; hardware and timeouts;
reviewer rubric; and start time. Criteria are those of the ADR-004 rerun, unchanged.

EXP-01 returns to `passed` only if every preregistered criterion passes over all nine
documents and all 41 physical pages, across two deterministic passes.

## 9. If the activation condition fails

This ADR is closed as **rejected**. `native-page-token-coverage-v1` remains in force as
fail-closed containment. EXP-01 remains failed, EXP-03 remains failed and blocked, and
Milestone 10 remains blocked.

An `absent_from_native`-dominant result means the two parsers genuinely disagree about
which values appear on the page. No token-level rule can resolve that. The next design
would require region-aware structured/native reconciliation with explicit per-region
provenance and no silent merge, which is a materially larger change requiring its own
architecture decision. This record does not authorize it.

A page-scope-leakage result under Section 3.4 means physical page identity is not being
preserved through Docling export, which contradicts a binding architecture invariant.
That defect must be fixed and the ADR-004 rerun repeated before any comparison rule is
reconsidered.

## 10. Alternatives considered

### Lower the 0.90 threshold and rerun under ADR-004

Rejected. The rerun already produced a 2.72% coverage observation; no threshold consistent
with a meaningful completeness gate admits it. Lowering a criterion after seeing results
also destroys the distinction between a miscalibrated rule and a rule tuned until it
passed.

### Suppress the high-signal check

Rejected. Digit-bearing tokens are the values whose loss changed the EXP-01 outcome in the
first place. Removing that check would readmit the original defect.

### Keep multiset comparison but exempt known duplication sources

Rejected. Exempting TableFormer span replication and picture traversal requires modelling
each parser's emission behaviour, which is unstable across versions and would embed
parser-specific assumptions into a provenance rule.

### Add a third independent parser

Deferred, as in ADR-004. It broadens the union of observed material tokens and would
strengthen the rule, but adds validation burden not justified until the directional rule
is shown to resolve the observed defect.

### Region-aware reconciliation now

Deferred. It is the likely eventual design and is the stated fallback direction in
Section 9, but it is disproportionate if the defect is duplication scored as conflict.
The diagnostic decides which problem is actually being solved.

## 11. Scope

This record does not change `evaluation/gold_cases.json` from
`initial_expert_review_required`. It validates representation fidelity, not legal or tax
interpretation. It implements no retrieval or question-answering behaviour. A passing
EXP-01 permits layout-aware EXP-03 work to resume but does not itself pass EXP-03 or
unblock Milestone 10.

## 12. Closure record — rejected (2026-08-19)

The Section 2 diagnostic ran on 2026-08-19 inside the pinned ingestion image
(`docling-slim==2.117.0`, `pypdf==6.6.2`, staged model artifacts at `/models/docling`)
against the three documents that failed the EXP-01 rerun. Derived evidence, including
every raw token string, is under the ignored tree:

- `evaluation/runs/EXP-01/diagnostic-conflict-taxonomy/` (procurement report)
- `evaluation/runs/EXP-01/diagnostic-conflict-taxonomy-rmc03-rr11/` (RMC 03-2024, RR 11-2024)

### 12.1 Diagnostic dataset

`coverage` is the frozen ADR-004 occurrence coverage; `absent` counts high-signal tokens
native never saw (`absent_from_native`); `surplus` counts high-signal tokens native saw in
fewer copies than Docling (`surplus_copies`).

`RR17_2024_Procurement_Monitoring_Report.pdf` (16 pages):

| Page | Coverage | absent | surplus |
|---:|---:|---:|---:|
| 1 | 0.289414 | 0 | 149 |
| 2 | 1.0 | 0 | 0 |
| 3 | 0.269490 | 0 | 116 |
| 4 | 1.0 | 0 | 0 |
| 5 | 0.289697 | 0 | 115 |
| 6 | 1.0 | 0 | 0 |
| 7 | 0.320780 | 0 | 107 |
| 8 | 1.0 | 0 | 0 |
| 9 | 0.160311 | 0 | 120 |
| 10 | 1.0 | 0 | 0 |
| 11 | 0.318067 | 0 | 106 |
| 12 | 1.0 | 0 | 0 |
| 13 | 0.398362 | 0 | 78 |
| 14 | 1.0 | 0 | 0 |
| 15 | 0.810207 | 0 | 22 |
| 16 | 0.765517 | 0 | 0 |

`RMC_03_2024_EOPT_Act.pdf` (2 pages), with token occurrence counts:

| Page | Coverage | absent | surplus | Docling occurrences | Native occurrences | Docling distinct | Native distinct |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.027222 | 0 | 29 | 13,592 | 394 | 188 | 208 |
| 2 | 1.0 | 0 | 0 | 237 | 237 | 131 | 131 |

`RR_11_2024_Invoicing_Amendments.pdf` (3 pages):

| Page | Coverage | absent | surplus |
|---:|---:|---:|---:|
| 1 | 0.963830 | 1 | 1 |
| 2 | 0.929787 | 0 | 0 |
| 3 | 1.0 | 0 | 0 |

Recorded per-page coverages match the rerun's conflict diagnostics exactly (28.94%,
2.72%, 96.38%, and 81.02% for procurement page 15), confirming the diagnostic reproduced
the frozen comparison.

### 12.2 Condition evaluation

1. **Section 3.1 — FAILED.** Physical page 1 of `RR_11_2024_Invoicing_Amendments.pdf`
   carries one `absent_from_native` material token: the bare digit `3` (normalized form),
   Docling count 2, native count 0. The condition requires zero across all pages whose
   rejection cause was `docling_high_signal_missing_from_native`; this page's coverage of
   0.963830 exceeded the 0.90 floor, so the two high-signal missing tokens were its only
   rejection cause, and it is in scope. The result is not `absent_from_native`-dominant —
   it is a single token against 843 surplus classifications corpus-wide — but the
   precommitted condition is zero, and it may not be weakened after seeing the output.
2. **Section 3.2 — passed.** Procurement physical page 15 has zero `absent_from_native`
   material tokens (all 22 rejected tokens are `surplus_copies`), and both required
   totals are present in the native candidate's token set, once each
   (`175,284,574.00` → `17528457400`; `169,021,829.87` → `16902182987`), with no
   fragment tokens indicating separator splitting.
3. **Section 3.3 — passed.** Raw-token inspection found no tokenizer-induced false
   `absent_from_native` labels. The single absent token is not a normalization artefact:
   native page 1 of RR 11-2024 contains no standalone `3` token at all (its only
   digit-3-bearing tokens are `13` and `237`), so no thousands-separator, spacing, or
   currency-glyph variant explains the label. Whether Docling's bare `3` is a parser
   emission artefact (for example a marker or numbering emission) or content Poppler
   drops is unresolved; either way the parsers genuinely differ on this page's token
   sets, and the precommitted rule treats that as failure.
4. **Section 3.4 — passed on the leakage question; magnitude unexplained.** RMC 03-2024
   is a two-page document, so page 2 is the only possible leak source. Docling's page-1
   distinct-token set (188 tokens) is a strict subset of native page 1's (208), and it
   contains zero of the 104 distinct tokens that appear only on native page 2. The 2.72%
   anomaly is therefore duplication within the correct physical page, not
   `export_to_text(page_no=...)` leakage. **Open item:** the duplication magnitude —
   Docling emitted 13,592 token occurrences against native's 394, a factor of ~34.5 from
   a smaller distinct vocabulary — is documented but not root-caused. Any future
   extraction design must explain it before trusting Docling occurrence counts on this
   document.

### 12.3 Consequence (Section 9 applied)

- This ADR is **rejected**. `material-token-omission-v1` is not implemented.
- `native-page-token-coverage-v1` (ADR-004) remains in force as fail-closed containment.
- **EXP-01 remains failed. EXP-03 remains failed and blocked. Milestone 10 remains
  blocked.**
- The pre-written Section 7 regression file
  `apps/api/tests/test_ingestion_material_token_omission.py` is deleted together with
  this record, per its own instruction, rather than relaxed. The backend suite returns
  to its 36-test passing baseline.
- The next design direction under Section 9 — region-aware structured/native
  reconciliation with explicit per-region provenance — requires its own architecture
  decision with a precommitted activation condition. This record does not authorize it.
