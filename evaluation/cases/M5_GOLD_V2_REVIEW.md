# Milestone 5 gold dataset v2 — independent review and adjudication packet

**Candidate status:** `initial_expert_review_required` — not adjudicated, not approved for scored release
**Candidate dataset ID:** `kendra-bir-public-gold-v2`
**Supersedes:** `kendra-bir-public-gold-v1`
**Review scope:** all 50 cases, all 125 expected facts, every expected physical page, all unsupported boundaries, ambiguity notes, and OCR flags

## Frozen candidate identity

| Item | SHA-256 |
|---|---|
| Superseded v1 dataset | `a19ca426e1981a6e2ea90c7a205a52d21635947fb041b11e5f4965c4aed2f9f4` |
| Candidate v2 dataset | `6aace5184c6778cad8c0d1972d83c99b6d3837355064ecc88dc941d86bab8f86` |
| Approved source manifest | `a54c6fd4d69f02a68e793384553772a6370de6614dc870a03853ec13407cf82e` |

The candidate hash above identifies the exact JSON bytes before reviewer annotations. If the dataset changes, stop review, calculate a new hash, explain the change, and issue a new candidate version. Do not overwrite this identity.

## Bounded v1-to-v2 correction

No question, expected fact, result, source filename, unacceptable behavior, ambiguity note, or OCR flag changed. The candidate adds `supersedes_dataset_id`, advances the dataset ID, and corrects three page arrays:

| Case | Document | v1 pages | v2 pages | Mechanical evidence |
|---|---|---:|---:|---|
| `KND-M5-CD-003` | `RR_11_2024_Invoicing_Amendments.pdf` | `[2]` | `[1, 2]` | The issuance identifier is on physical page 1; the inventory requirement is on page 2. |
| `KND-M5-CD-003` | `RMC_77_2024_Invoicing_QA_OCR.pdf` | `[9]` | `[1, 9]` | The circular identifier is on physical page 1; Annex C, the deadline, and the no-resubmission exception are on page 9. |
| `KND-M5-CD-010` | `RMC_03_2024_EOPT_Act.pdf` | `[2]` | `[1, 2]` | The circular identifier is on physical page 1; the veto statement is on page 2. |

`RR_04_2024_Filing_Payment.pdf` remains `[1]`. Engineering inspection establishes visible location and byte identity only. It does not adjudicate tax meaning, material qualifications, the proper unsupported boundary, or whether document identity must be same-page evidence.

## Required independent reviewers

Review must be blind and independent until both worksheets are locked.

| Role | Required qualification | Name | Organization/relationship | Date | Signature or attributable approval reference |
|---|---|---|---|---|---|
| Reviewer A | BIR/tax-domain competence sufficient to judge the issuances and material qualifications |  |  |  |  |
| Reviewer B | Document/evaluation specialist competent to verify questions, atomic facts, pages, ambiguity, and unsupported boundaries |  |  |  |  |
| Adjudicator | Accountable authority empowered to resolve disagreements and approve or reject the dataset |  |  |  |  |

Reviewer B does not replace the tax-domain authority. The dataset must not be promoted if Reviewer A's qualification or the adjudicator's authority is unrecorded.

## Per-case worksheet requirements

Each reviewer independently records, for every case:

1. candidate dataset hash and case ID;
2. supported/unsupported judgment;
3. accuracy and material completeness of every expected fact;
4. material qualifications, exceptions, dates, amounts, units, labels, and source attribution;
5. whether every expected physical page supports the adjacent fact in context;
6. whether any necessary page is missing or any listed page is merely related;
7. whether the question has one reproducible scoring interpretation;
8. whether the unacceptable behavior and ambiguity notes are sufficient;
9. whether the OCR flag is correct and, for OCR material, the reading verified against the rendered original;
10. disposition: accept, revise, exclude with reason, or escalate.

Raw worksheets and rendered review aids belong under `evaluation/runs/M5-adjudication/<run-id>/`, which is ignored by Git. Preserve their hashes in the final attributable outcome.

Generate two independent, hash-bound worksheets and the adjudication log before distributing either worksheet:

```bash
python3 scripts/prepare_m5_adjudication.py evaluation/gold_cases.json \
  evaluation/runs/M5-adjudication/<run-id>
```

Give `reviewer-a.json` only to Reviewer A and `reviewer-b.json` only to Reviewer B. Do not exchange outcomes until both reviewers mark their worksheets locked and calculate their final file hashes. The adjudicator then records those hashes before resolving disagreements in `adjudication.json`.

## Mandatory boundary calls

The adjudicator must explicitly settle:

- `MF-01`: whether the OCR substitution in the circular's own header identifier is material and how it affects case-level acceptance;
- whether document identifiers may resolve across the complete named document while substantive claims remain page-scoped, or whether page 1 must be included as v2 proposes;
- every disagreement over legal/tax meaning, material qualification, unsupported scope, ambiguity, or OCR reading;
- whether any accepted correction requires v3 rather than promotion of these exact v2 bytes.

## Adjudication outcome

Complete only after both independent worksheets are locked.

| Field | Outcome |
|---|---|
| Reviewer A worksheet SHA-256 |  |
| Reviewer B worksheet SHA-256 |  |
| Disagreement log SHA-256 |  |
| Accepted/rejected/excluded case counts |  |
| Adjudicated dataset ID and SHA-256 |  |
| Decision date |  |
| Adjudicator approval reference |  |

**Current outcome:** OPEN. Candidate v2 is mechanically corrected but has not received the required human domain review or adjudication. EXP-01 must not preregister this candidate as an approved gold dataset until the outcome above is complete.
