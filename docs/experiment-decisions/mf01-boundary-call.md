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

## Evidence located 2026-08-20 that narrows the call

Two lookups were run against artifacts that **predate the finding**, so neither is shaped by
it. Both are reported as observations; neither decides the question.

### 1. The parent criterion is scoped to material expected facts

Registration item 5 is a compression of the EXP-01 criteria frozen in
[EXPERIMENT_PLAN.md](../EXPERIMENT_PLAN.md) at Milestone 7a, which state:

> **Pass criteria:** ... extraction/OCR changes zero **material expected facts** ...
> **Fail criteria:** ... **one material fact changed** ...
> **Metrics collected:** ... **material fact-alteration count** ...

The plan's scope is therefore not "any digit-bearing token in retained text" but the
**expected facts asserted by the gold cases**. This wording predates the ADR-007 rerun by
roughly two weeks and names no document, page, or token.

That converts the boundary call from an aesthetic judgment — *is a header number important
enough?* — into a lookup: **is `77-2024` a token of a material expected fact?**

### 2. It is. In four facts across two cases.

`77-2024` appears in `expected_answer_facts` of `KND-M5-CD-001` (facts 1 and 2) and
`KND-M5-CD-003` (facts 1 and 2) in the frozen dataset.

In `fact_scoring.json` for run `20260819T205613+0800-b1fcd79`, the normalized token `772024`
is scored `"match": "join"` in **all four**:

| Case | Fact | Token | Match type |
|---|---|---|---|
| `KND-M5-CD-001` | 1 | `772024` | `join` |
| `KND-M5-CD-001` | 2 | `772024` | `join` |
| `KND-M5-CD-003` | 1 | `772024` | `join` |
| `KND-M5-CD-003` | 2 | `772024` | `join` |

The join match succeeds because the retained page-1 token normalizes to `1772024`, which
contains `772024` as a substring. **There is no uncorrupted occurrence of this token anywhere
in the retained corpus** — these documents print their own number once, on page 1.

### 3. Consequence: the ruling and the fact count are coupled

The adjudicated total of 121 of 125 retained facts **depends on those four join matches
standing.** If item 5 is held to be engaged — or if the scorer's substring defect is simply
corrected, which `CLAUDE.md` already carries as known harness debt — the four facts lose
their `772024` support and the established total falls from 121 toward 117.

`KND-M5-CD-001` is affected even though it was adjudicated *not* defective. Its separate
`500` miss was correctly ruled numeric formatting; its dependence on `772024` is a distinct
issue and was not part of that ruling.

This coupling was not visible at adjudication time and is reported here so the reviewer is not
ruling on MF-01 in isolation while treating 121 as settled.

### 4. What genuinely remains a judgment

The lookup does not close the question, because a defensible reading survives it: the
*substance* of all four facts is retained on their cited pages. What is corrupted is the
document's naming handle, printed once on a page none of the four facts cite. A reviewer may
hold that a gold fact asserts a claim *about* a document and that the identifier is how the
case addresses it, not a value the case asserts.

Note this is the same structural condition as the
[gold-case defect](gold-case-defect-CD003-CD010.md): document identifiers appear once, on
page 1, while facts are scoped to interior pages. MF-01 is that condition plus a corruption.
The two open items are not independent and should be ruled on together.

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
