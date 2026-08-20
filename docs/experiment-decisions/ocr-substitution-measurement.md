# OCR substitution measurement — SF-01 blind region

**Status:** Complete. Reported as observation. **No ruling is made here and no criterion is
changed.**
**Measured:** 2026-08-20 by the authorized evaluator, single observer, manual comparison
against rendered originals.
**Subject:** the 12 OCR-retained pages of `RMC_77_2024_Invoicing_QA_OCR.pdf`.
**Source run:** `20260819T205613+0800-b1fcd79`.
**Evidence:** `evaluation/runs/EXP-01/diagnostic-ocr-token-inventory/` (gitignored).
**Instrument:** `scripts/exp01_ocr_token_inventory.py`, `scripts/exp01_ocr_worksheet_html.py`.

## Why this was measured

[MF-01](mf01-boundary-call.md) recorded one OCR digit substitution. SF-01 recorded that
ADR-007's containment detector yields zero material tokens across every OCR page, so no
substitution on those pages is mechanically detectable. The class rate was therefore
observed=1 and measured=unknown, and the MF-01 ruling would have been made without it.

Every digit-bearing token the OCR path retained was inventoried and compared by hand against
the rendered original. This measures **substitution in retained text only**. A token OCR
dropped entirely leaves no row and remains undetectable; that gap is unchanged.

## Result

| Verdict | Occurrences | Share |
|---|---:|---:|
| Faithful | 262 | 85.6% |
| **Substitution** | **27** | **8.8%** |
| Original unreadable | 17 | 5.6% |
| **Total** | **306** | |

20 distinct normalized tokens are affected by substitution.

| Physical page | Substitutions / tokens |
|---|---|
| 1 | 3 / 19 |
| 3 | 3 / 27 |
| 6 | **13 / 41** |
| 7 | 1 / 21 |
| 9 | 3 / 22 |
| 11 | 3 / 44 |
| 12 | 1 / 15 |

Pages 2, 4, 5, 8 and 10 are clean. Seven of twelve pages carry at least one substitution.

## Method controls

- **Positive control passed.** The reviewer independently marked page 1 line 12
  (`177-2024`) as a substitution without being told which row it was. MF-01 was re-found by
  the sweep rather than assumed.
- **No verdict was revised.** Five progressive exports show monotonic growth with zero
  changes to any verdict already recorded, so no row was re-judged after later rows were seen.
- **A third option was available and used.** `unreadable_in_original` was recorded 17 times,
  so "cannot tell" did not collapse into either "faithful" or "substitution."
- **Rows were not prioritised by gold relevance.** The worksheet warned against it, for the
  reason given below.

## Two results that must not be misread

**1. Zero of the 27 substitutions fall on a token asserted by a gold fact.** This is not
evidence that they are harmless. A corrupted token cannot match a gold token by construction,
so this figure is forced to zero and carries no information about impact. It is reported only
to forestall the inference.

**2. Substitutions cluster in figure and table regions rather than distributing evenly.**
Page 6's thirteen occurrences fall almost entirely inside a reproduced sample invoice, where
currency amounts lost decimal separators and digits. Five pages are entirely clean. The defect
is regional degradation, not uniform character error.

## What this establishes and what it does not

**Established.** SF-01 is demonstrated rather than hypothetical. Twenty-seven digit
corruptions exist inside a region where the active policy's detector is by measurement
incapable of reporting any of them. MF-01 is not an isolated token; it is one instance at a
rate of roughly one in eleven.

**Not established.** Whether decision-rule item 5 is engaged. That remains the reviewer's
criterion-boundary call, unchanged. This memo supplies the rate the ruling was previously
going to be made without.

**Worth noting before ruling.** The two available readings of item 5 no longer diverge as
cleanly as they did:

- Read broadly, as any extracted value, 27 values materially differ from the original.
- Read narrowly, as material expected facts only, these 27 fall outside it — but MF-01 itself
  does not, because four gold facts across `KND-M5-CD-001` and `KND-M5-CD-003` assert
  `77-2024` and the corpus retains that token nowhere except in corrupted form.

Both paths now arrive at item 5 rather than around it. The reviewer still decides whether
arriving there engages it.

**Unmeasured.** Omission. Whether the OCR path also drops digit-bearing tokens is not
addressed by this instrument and remains open under ADR-007 Section 8.


## Correction, 2026-08-20 — the rate above is a lower bound

Added after the EXP-07 truth-set pass. The measured figures are not withdrawn; they are
qualified. This section contradicts the headline reading of Section "Result" rather than
replacing it, so both remain visible.

**A faithful verdict is confirmed wrong.** Page 6 line 30 retains `2.500` and was verdicted
*faithful*. The reviewer subsequently stated the page prints `2,500`. The comma was read as a
period, which is a substitution, and the sweep recorded it as correct.

**The miss is systematic in kind, not a slip.** Separator damage is the one defect class that
survives fragment-level comparison, because the fragment still looks like a plausible number.
`2.500` reads as a number; only the printed original shows it should be `2,500`. The reviewer
caught the identical defect in `3.214` on line 34, which is why the inconsistency surfaced at
all.

**Exposure: 27 of the 262 faithful rows carry a `.` or `,`** and are therefore rows where this
class could hide. Distribution: page 1 (3), 2 (6), 3 (1), 4 (2), 6 (4), 8 (1), 10 (9), 11 (1).
Most are probably sound — page 10's nine are cleanly formed currency amounts — but none has
been checked against the original for separator fidelity specifically.

**Consequence.** The substitution count of 27 and the rate of 8.8% are a **floor**. The true
rate is at least that and is not established until the 27 separator-bearing faithful rows are
re-checked. Every conclusion drawn from the measurement holds a fortiori: SF-01 remains
demonstrated, and MF-01 remains non-isolated. Nothing that depended on the rate being *at
least* 8.8% is weakened.

**A second defect class was also confirmed.** Page 1 line 1's `75` and page 12 line 6's `9924`
are both **fabrications** — tokens the reviewer confirms are absent from the original page.
Two invented numbers in 306 tokens. Fabrication is not a reading error and no fidelity
configuration is guaranteed to remove it; a fabricated figure is indistinguishable from a real
one downstream and nothing in the pipeline contradicts it. See EXP-07 Section 4a class F.
