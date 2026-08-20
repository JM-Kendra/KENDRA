# Gold-case defect: KND-M5-CD-003 and KND-M5-CD-010

**Status:** Open. Awaiting expert review. **No change has been made to
`evaluation/gold_cases.json`**, which remains `initial_expert_review_required` with SHA-256
`a19ca426e1981a6e2ea90c7a205a52d21635947fb041b11e5f4965c4aed2f9f4`.
**Raised:** 2026-08-20, from the run `20260819T205613+0800-b1fcd79` adjudication.
**Recorded in:** [EXP-01.md](EXP-01.md), 2026-08-20 adjudication section.

This memo states observed facts and sets out options. It does not select one, does not edit
the dataset, and does not decide legal or tax meaning. Engineering review is confined to
representation fidelity.

## What was observed

Four expected facts cannot be resolved to the physical pages their cases cite. In every
instance the value **is retained in the corpus** — the case names the wrong page.

| Case | Fact | Token not on cited page | Cited page | Page where the corpus retains it |
|---|---|---|---|---|
| `KND-M5-CD-003` | RR 11-2024 inventory deadline | `11-2024` | RR 11-2024 p2 | RR 11-2024 p1 |
| `KND-M5-CD-003` | Annex C is the inventory-report format | `RMC` | RMC 77-2024 p9 | RMC 77-2024 p1 |
| `KND-M5-CD-003` | No resubmission for prior Annex D filers | `RMC` | RMC 77-2024 p9 | RMC 77-2024 p1 |
| `KND-M5-CD-010` | Micro-enterprise withholding veto | `3-2024`, `RMC` | RMC 03-2024 p2 | RMC 03-2024 p1 |

The substantive content of all four facts is present on the cited pages and was adjudicated
retained. For example, RMC 03-2024 page 2 carries the veto clause in full: "The provision of
the EOPT Act granting micro-enterprises exemption from the obligation to withhold taxes was
vetoed by the President." What is absent from page 2 is only the circular's own identifier,
which these documents print once, on page 1.

ADR-007 Section 8 recorded this class in advance and stated that no page-faithful retention
rule can satisfy it.

## What is not in question

- This is **not** an extraction defect. No page-faithful policy, present or future, can place
  a page-1 identifier onto page 2.
- `KND-M5-CD-001` was previously grouped with these two and **does not belong here**. Its
  missing `500` is numeric formatting: the cited page reads "valued at Five Hundred Pesos
  (Php 500.00) or more" and the gold fact writes `PhP 500`. It adjudicates as retained.

## Options

**Option A — correct `expected_pages`.** Add page 1 to the affected documents' entries in the
two cases, so the cited page range covers where the identifier actually appears.

*For:* fixes a genuine authoring error; preserves the page-faithful standard for every other
case; changes no criterion. *Against:* edits the evaluation dataset, so its SHA-256 changes.
That checksum is frozen in the EXP-01 registration, so this requires a dataset version bump,
a new preregistration, and a re-run. Cost is now small: extraction is deterministic and took
roughly fifteen minutes, the harness is written and checksummed, and scoring is seconds.

**Option B — document-scope resolution for identifier-class facts.** Rule that a document
identifier resolves at document scope while all other values remain page-scoped.

*For:* no dataset edit. *Against:* changes a criterion after seeing the evidence it governs,
which is the pattern the project prohibits. It would need its own ADR with an activation
condition fixed before evidence, and it weakens page-faithful resolution for a whole class of
value. Not recommended.

**Option C — mark the two cases defective and excluded.** Record them as unusable pending
authoring repair and score EXP-01 over the remaining 121 facts.

*For:* no dataset edit, no criterion change, and honest about the defect. *Against:* leaves
two cross-document cases permanently unscored, and cross-document comparison is a category
the evaluation exists to exercise. Acceptable only as an interim position.

## Recommendation

Option A. The cases are simply wrong about where the identifier is printed, and correcting an
authoring error is expert review performing its function, not a criterion being weakened after
the fact. The re-run cost that once made this expensive no longer applies.

## What an approval needs to specify

1. The exact edit, per case and per document, to `expected_pages`.
2. A dataset version bump and the new `dataset_id` or version field, so the change is
   attributable and the old checksum is not silently replaced.
3. Whether `dataset_status` stays `initial_expert_review_required`. Engineering review has no
   authority to change it, and this memo assumes it stays.
4. That a new EXP-01 registration is frozen before any re-processing or re-scoring, naming the
   new dataset checksum and superseding
   `20260819T205613+0800-b1fcd79`.

Until those are recorded, the four facts remain `unresolvable_dataset_defect` and EXP-01
remains not `passed`.
