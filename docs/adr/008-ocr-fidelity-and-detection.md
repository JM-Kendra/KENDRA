# ADR-008: OCR-page fidelity scope and second-observer detection

**Status:** Proposed. **Not accepted and not activated.**
**Date drafted:** 2026-08-20
**Builds on:** [ADR-007](007-native-primary-detection.md) `native-primary-detection-v1`, active
**Active policy while this is proposed:** ADR-007, unchanged in every respect

> **Disclosure.** This record was drafted **with the run
> `20260819T205613+0800-b1fcd79` adjudication in hand**, including finding MF-01 and the
> SF-01 measurement. That ordering is stated plainly because it matters: the rule below must
> not be a rule written to accommodate one token whose nature was already known. The design
> is general, special-cases no document, page, or token, and would have been written
> identically had SF-01 surfaced a different OCR defect. MF-01 is the first application of the
> rule, not its justification.

> **Gating.** This record proposes a design and is argued on design reasoning. It defines
> **no activation condition of its own.** The empirical gate is EXP-01's existing
> preregistered criteria, unchanged. ADR-005 and ADR-006 each failed on a bespoke gate that
> was stricter than, and measured something other than, the policy it gated. ADR-007 declined
> to repeat that pattern and so does this record. In particular it fixes **no numeric
> disagreement threshold**, because no such number can be chosen honestly before the
> two-observer disagreement population has ever been measured, and choosing one afterwards
> would be tuning a gate to its own evidence.

## 1. What the run established

Two findings from the 2026-08-20 adjudication motivate this record. Both are recorded in
`docs/experiment-decisions/EXP-01.md` and in the run's `fact_adjudication.json`.

**SF-01, the structural defect.** ADR-007 retains a page and then checks it against a
non-retaining Docling detector at document scope. On an image-only page the detector, with
internal OCR disabled per ADR-007 Section 2.2, observes nothing. Measured directly:

| Document | Class | Detector characters | Detector material tokens |
|---|---|---:|---:|
| `RMC_77_2024_Invoicing_QA_OCR.pdf` | scanned, no text layer | 686 | **0** |
| `RR_11_2024_Invoicing_Amendments.pdf` | digital | 9,463 | 20 |

The containment check is therefore **vacuous for every OCR-retained page**: an empty observed
set is contained in anything. That is 12 of 41 physical pages with no completeness or fidelity
detection of any kind. The check does not merely perform poorly there; it cannot fail there.

**MF-01, the first observed consequence.** Physical page 1 of the scanned circular is retained
as `REVENUE MEMORANDUM CiRCULAR NO. (177-2024`. The rendered original reads
`REVENUE MEMORANDUM CIRCULAR NO. 077-2024`. A digit-bearing material token in the retained
representation differs from the original, inside the blind region, and nothing in the active
policy could have surfaced it.

## 2. The two questions this record answers

1. **Scope.** The EXP-01 decision rule requires that "no extracted value materially differs
   from the original." Applied literally to every token, no OCR engine can ever satisfy it, so
   the rule as read would permanently exclude any corpus containing scans. Applied loosely, it
   excuses exactly the defect class MF-01 belongs to. Neither reading is usable.
2. **Detection.** Whatever the scope, a defect that cannot be observed cannot be governed.
   ADR-007 Section 8 already carries prose-omission detection as an open item. SF-01 shows
   substitution detection is equally absent and that the gap covers every OCR page.

## 3. Decision

Adopt `ocr-second-observer-v1`. ADR-007 is incorporated by reference and **unchanged** for
every native-retained page: native-primary retention, Docling as non-retaining detector,
document-scope material-token containment, whole-page blocks, and the existing pointers. No
threshold in ADR-007 is re-tuned and no page changes its retention method because of this
record.

### 3.1 Fidelity scope for decision-rule item 5

"No extracted value materially differs from the original" governs any value on which **a gold
expected fact, a citation, or a required table or form relationship depends**. Names, dates,
amounts, thresholds, negations, conditions, exceptions and list membership are in scope
wherever a dependent artefact rests on them.

Document furniture — running headers, received stamps, routing marks, page ornaments and the
document's own printed control number — is **out of scope for item 5** but is **never out of
scope for detection**. It must be observed, and any disagreement must be recorded and
reported. It may not be silently accepted, and it may not be silently discarded.

This scoping is a definition, not a relaxation. It narrows what fails a run; it widens what
must be seen. Under it, MF-01 is a reported fidelity defect in furniture rather than an item-5
failure — and it is reportable only because Section 3.2 makes it observable.

### 3.2 Second-observer detection on image-only pages

For every physical page retained by OCR, a **second independent OCR observation** is produced
from the same page image by a different engine or a materially different configuration than
the retaining observer. The second observer never contributes retained text, never resolves a
citation, and its page attribution is never recorded, exactly as Docling's is not under
ADR-007.

Comparison is over distinct material-token sets at page scope. Page scope is sound here, and
unsound for the native path, because both observers read the same rendered page image rather
than two different structural interpretations of a document.

Disagreements are classified, not merely counted:

- a material token seen by both observers is **corroborated**;
- a material token seen by exactly one is a **single-observer token** and is **recorded as a
  fidelity exception** against that page;
- a fidelity exception touching an in-scope value under Section 3.1 **fails the page closed**
  with a content-free `ocr_fidelity_conflict`;
- a fidelity exception touching furniture is **retained and reported**, never suppressed.

### 3.3 Why this is not ADR-006 again

ADR-006 proposed an adjudication register and was rejected because its bounded-population
condition failed. This record does not revive that register, sets no population ceiling, and
requires no per-token human verdict for retention to proceed. The distinction is that ADR-006
made adjudication a **precondition of retention**; here classification is a **product of
retention**, recorded alongside the page. A furniture exception does not block a run and does
not need a ruling. Only an in-scope exception fails, and it fails closed automatically.

### 3.4 Runtime configuration

`KENDRA_EXTRACTION_COMPLETENESS_POLICY=ocr-second-observer-v1` selects the policy. The second
observer's engine identity, configuration and version are recorded in the tool identity string
and frozen in any preregistration that uses it. No page may be retained under this policy
without a recorded second observation or a recorded, content-free reason why the page has
none.

## 4. What this costs

A second OCR pass over every image-only page. On the approved corpus that is 12 of 41 pages,
and the observed Tesseract page cost makes the added wall-clock cost minor against a run that
already takes minutes. The cost is paid only on OCR pages; native pages are untouched.

It also produces a class of output the project does not have today: a per-page fidelity
exception list for scanned documents. That list will be non-empty. That is the point — it is
the difference between a corpus whose OCR defects are known and one whose OCR defects are
undetectable.

## 5. Consequences

### Positive

- The blind region closes. Every retained page, native or OCR, has an independent observer.
- MF-01's defect class becomes visible rather than fortuitous. It was found by a human reading
  a rendered page during adjudication; under this policy it is produced mechanically.
- Item 5 becomes applicable to scanned corpora without either excusing real loss or demanding
  an unachievable exact match.
- Fail-closed behaviour is preserved and sharpened: it now triggers on the values that matter.

### Negative and limitations

- **Correlated blindness.** Two OCR engines can make the same error on the same glyph. Two
  observers reduce undetected substitution; they do not eliminate it. This record does not
  claim OCR correctness, only observability.
- **Dependence on the scope boundary.** Section 3.1 rests on knowing which values a gold fact
  or citation depends on. That mapping exists for the current gold set; a corpus without one
  would have to treat every material token as in scope, which is the strict reading and would
  be unusable. Extending beyond the evaluation corpus needs its own record.
- **Furniture is a judgement class.** "Running header" and "control number" are recognisable,
  but the boundary will have edge cases. Section 3.2 mitigates by reporting rather than
  discarding, so a misclassification is visible in the exception list.
- **Prose omission on OCR pages remains open.** Material tokens are digit-bearing by the
  ADR-004 definition. A dropped non-digit clause is still undetected, on OCR and native paths
  alike. ADR-007 Section 8 carries this and this record does not close it.
- No mechanism here improves OCR accuracy. Repairing MF-01 itself, if the reviewer wants it
  repaired, is a separate question about OCR configuration, not about detection.

## 6. Regression coverage required before activation

Written before any run under this policy, so their content cannot be shaped by its output:

- an image-only page whose two observers agree produces zero fidelity exceptions;
- a material token seen only by the retaining observer is recorded as a fidelity exception;
- a material token seen only by the second observer is recorded as a fidelity exception;
- a fidelity exception on an in-scope value fails the page closed with `ocr_fidelity_conflict`;
- a fidelity exception on furniture retains the page and appears in the exception list;
- an OCR page with no recorded second observation fails closed;
- the error carries a code only and no extracted content;
- a native-retained page is unaffected: no second OCR observation is attempted and ADR-007
  containment governs unchanged;
- the second observer's text never appears in a retained record, a pointer, or a citation;
- page identity remains one-based and contiguous across both observers;
- two deterministic passes produce identical exception lists.

## 7. Preregistration

Before any corpus processing or scoring under this policy: a new ignored run registration
frozen with the current Git revision, source-manifest and evaluation-dataset checksums, both
observers' engine identities, versions and configurations, the Section 3.1 scope mapping in
force, fail-closed rules, hardware, timeouts, reviewer rubric, and start time.

Criteria are EXP-01's existing preregistered criteria, unchanged. EXP-01 returns to `passed`
only if every one passes over all nine documents and all 41 physical pages across two
deterministic passes.

## 8. Scope

This record does not change `evaluation/gold_cases.json` from
`initial_expert_review_required`, and it does not resolve the `KND-M5-CD-003` and
`KND-M5-CD-010` page-scoping defect, which is a dataset question addressed separately. It
validates representation fidelity, not legal or tax interpretation. It implements no retrieval
or question-answering behaviour. A passing EXP-01 under this policy permits layout-aware
EXP-03 work to resume but does not itself pass EXP-03 or unblock Milestone 10.

## 9. If this is rejected

ADR-007 remains in force with SF-01 unremediated and recorded, MF-01 remains an open reported
defect, and any claim that the corpus representation is verified must continue to exclude the
12 OCR-retained pages explicitly.
