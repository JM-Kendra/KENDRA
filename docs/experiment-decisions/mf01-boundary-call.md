# MF-01: OCR digit substitution in a document's own header number

**Status:** Open. Awaiting the authorized reviewer's ruling. **No criterion has been changed,
no record altered, and no ruling is made here.**
**Raised:** 2026-08-20, from the run `20260819T205613+0800-b1fcd79` adjudication.
**Recorded in:** [EXP-01.md](EXP-01.md), "New material finding, MF-01".
**Companion open item:** [gold-case-defect-CD003-CD010.md](gold-case-defect-CD003-CD010.md).

This memo states the observation, quotes the governing criterion verbatim, and sets out the
two available readings with their downstream consequences. It does not select one. Selecting
one is a criterion-boundary call reserved to the authorized reviewer.

## What was observed

Physical page 1 of `RMC_77_2024_Invoicing_QA_OCR.pdf`, an OCR-retained page:

| | Text |
|---|---|
| Rendered original | `REVENUE MEMORANDUM CIRCULAR NO. 077-2024` |
| Retained representation | `REVENUE MEMORANDUM CiRCULAR NO. (177-2024` |

Two distinct corruptions are present. `CIRCULAR` → `CiRCULAR` is a non-material case
substitution in a non-digit token. `077-2024` → `(177-2024` is a **digit-bearing material
token whose value differs from the original**: a leading `0` has been read as `(1`.

Two further suspicious readings on the same document were checked against the rendered
original and are **not** defects: page 11's `RA 11796` and page 9's `Annex E`/`Annex F`
appear that way in the source itself and were faithfully retained.

## The governing criterion, quoted exactly

From the frozen registration `20260819T205613+0800-b1fcd79`, field `/decision_rule`:

> Pass only if all source checksums match; exactly 41 contiguous unique pages are
> represented; every visible material expected fact is retained; page mapping is 100 percent;
> **no extracted value materially differs from the original**; required table/form
> relationships remain source-resolvable; methods and provenance are explicit; repeated
> results match; and there are zero unresolved conflicts. Any missing observation is
> inconclusive; any explicit criterion failure is failed.

The emphasised clause is item 5. Note the asymmetry the rule sets up: a *missing observation*
is inconclusive, but an *explicit criterion failure* is **failed**. If item 5 is held to cover
this token, EXP-01 does not become more inconclusive — it becomes explicitly failed.

## Why this is genuinely a boundary call

The frozen rule does not define "extracted value." Both readings below are available on the
text as written, which is precisely why it was left undecided rather than resolved by the
adjudicating session.

### Reading A — item 5 is violated; EXP-01 is explicitly failed

- The token is digit-bearing and material under the project's own definition of a material
  token (detection rule 2: "a token containing at least one digit").
- It is not a marginal value. It is the document's own identifier — the value by which every
  human reader, every citation in correspondence, and every gold case names this document.
- Invariant 2 requires a citation to resolve to a stable document identifier. Under Milestone
  10 the retained excerpt is displayed to the reviewer adjacent to the claim. A reviewer
  reading an excerpt headed `NO. (177-2024` sees a document number that does not exist,
  contradicting the filename-derived citation shown beside it.
- A rule that exempts the header number from "extracted value" has to name a principled scope
  for item 5 that excludes it, and no such scope is written in the frozen rule.

### Reading B — item 5 is not engaged; the finding is recorded but not disqualifying

- Citation identity does not depend on it. Documents resolve by filename and registry
  checksum, never by parsing a number out of OCR text, so no citation misresolves.
- Item 5's evident purpose is to protect *values under test* — amounts, dates, deadlines,
  thresholds, rates — against silent corruption. The header number is document chrome, not a
  value any gold case asserts.
- No expected fact is lost. The adjudication established 121 of 125 facts retained; MF-01
  touches none of them.
- OCR at the character level is known-lossy and the project already accepts whole-page
  Tesseract for sub-floor pages. Reading A, applied consistently, arguably fails any OCR page
  bearing any digit misread, which may make the OCR path unusable by construction.

## The consequence that applies under either reading

**MF-01 was not caught by the scorer.** It escaped because the fact scorer's join-match rule
can match a digit-bearing token as a substring of a corrupted one: `77-2024` matched inside
`(177-2024`. It was found by manual comparison against the rendered original, not by the
harness.

Combined with **SF-01** — the ADR-007 containment detector yields zero material tokens across
all 12 pages of this document, so no omission or substitution on any OCR page is mechanically
detectable — this means:

> The observed count of MF-01-class substitutions is **one**, but the measured count is
> **unmeasured**. Neither the detector nor the scorer can establish that MF-01 is unique.
> 12 of 41 physical pages currently have no substitution detection of any kind.

A Reading B ruling therefore disposes of *this token* but not of *this class*. It should not
be recorded as evidence that OCR substitution is absent or rare, because nothing in the
current harness could have shown otherwise. ADR-008 is the proposed vehicle for closing SF-01
and remains **proposed, not accepted**.

## What an approval needs to specify

1. The ruling: item 5 engaged (Reading A) or not engaged (Reading B).
2. If Reading B, the **principled scope of "extracted value"** that excludes a header
   identifier — written as a general rule, not as an exception for this token, and applicable
   to documents not yet examined.
3. Whether the ruling is recorded as a clarification of the existing frozen rule or requires a
   new preregistration. A clarification that narrows item 5 after seeing the token it governs
   is a criterion change under the project's own prohibition and needs an ADR with an
   activation condition fixed before evidence.
4. Whether SF-01 closure (ADR-008 acceptance) is a precondition of the ruling taking effect,
   given that the class rate is unmeasured.
5. That the ruling is attributable and dated, so the EXP-01 standing section can cite it.

## Interaction with the other open blocker

The gold-case defect memo recommends Option A, which requires a dataset version bump, a new
EXP-01 preregistration, and a re-run. If that is approved, the MF-01 ruling should be settled
**before** the new registration is frozen, so the re-run is scored under a decision rule whose
item 5 scope is already fixed. Settling them in the other order would mean interpreting item 5
with the new results already visible.

Until both are recorded, EXP-01 remains not `passed`, EXP-03 remains blocked, and Milestone 10
remains blocked.
