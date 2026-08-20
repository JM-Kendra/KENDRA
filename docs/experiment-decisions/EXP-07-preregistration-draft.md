# EXP-07 — OCR render resolution and recognition model

**Status:** Draft. **Not frozen and not a registration.** It becomes
`evaluation/runs/EXP-07/<run-id>/registration.json` only when Section 4's truth set is complete
and the file is checksummed **before any candidate is run**.
**Drafted:** 2026-08-20
**Gates:** [ADR-009](../adr/009-ocr-render-and-model-fidelity.md), proposed.
**Requires before freezing:** reviewer-supplied correct readings for the 27 substitutions
(Section 4). Nothing in Sections 2, 5 or 6 may be revised after the first candidate runs.
**Addendum required:** `EXPERIMENT_PLAN.md` lists EXP-01 through EXP-06. Adding EXP-07 to it
needs reviewer approval and is not done unilaterally by this draft.

## 1. Question and decision

**EXP-07 — Which bounded combination of render resolution and Tesseract recognition model
reduces digit substitution on OCR-retained pages without regressing any token that is already
correct?**

Produces: a selected OCR configuration named by a reviewed `EXP-07.md`, or an explicit failure
selecting none.

## 2. Frozen candidate matrix

Two factors, fully crossed, so each factor's contribution is attributable rather than
confounded. Fixed before any run.

| Candidate | Render DPI | Model | Selectable |
|---|---:|---|---|
| `C0_BASELINE_300_FAST` | 300 | `fast` (`tesseract-ocr-eng`) | No — reference only |
| `C1_400_FAST` | 400 | `fast` | Yes |
| `C2_600_FAST` | 600 | `fast` | Yes |
| `C3_400_BEST` | 400 | `best` | Yes |
| `C4_600_BEST` | 600 | `best` | Yes |

`C0` reproduces the active ADR-007 branch and establishes the baseline column; it is never
selectable, being the configuration whose defect prompted the experiment.

Page segmentation mode is **held at Tesseract's default (PSM 3) in every candidate** per
ADR-009 Section 3. It is not a variable here and may not be introduced mid-experiment.

## 3. Controlled variables

Source bytes and checksums; the nine-PDF manifest; page numbering; `pdftoppm` and Tesseract
binary versions; the pinned `best` model artifact and its SHA-256; container image; CPU and
memory limits; per-page timeout; concurrency of one; disabled network; and the ADR-004
tokenizer. Only DPI and model vary.

The `best` model artifact must be version-pinned and checksum-recorded before the run, since it
becomes part of the reproducibility surface.

## 4. Truth set — required before freezing

Built from `evaluation/runs/EXP-01/diagnostic-ocr-token-inventory/review-results.json`, the
2026-08-20 single-observer sweep of all 306 digit-bearing tokens.

| Reviewer verdict | Count | Truth value | In truth set |
|---|---:|---|---|
| `faithful` | 262 | the baseline surface form, reviewer-confirmed | Yes |
| `substitution` | 27 | **must be supplied by the reviewer** | Yes, once supplied |
| `unreadable_in_original` | 17 | none exists | **No — excluded** |

**Truth set size: 289 token occurrences, page-scoped.**

The 17 unreadable are excluded because no ground truth exists for them; scoring a candidate
against a value nobody can read would manufacture a result. They are neither credited nor
penalised, and their exclusion is recorded so the denominator is not silently 306.

## 4a. Defect taxonomy discovered during truth-set construction

**Freezing is blocked.** The reviewer supplied readings on 2026-08-20 and the result shows
Section 5 as drafted cannot score 10 of the 27 rows. The instrument assumed every defect was a
*substitution* — a wrong value standing where a right one belongs. Three further classes
appeared. This is recorded before freezing, which is the only point at which the scoring rule
may still be corrected.

| Class | Rows | Scorable by Section 5 as drafted |
|---|---:|---|
| **S — substitution.** A wrong value stands where a right one belongs. | 8 | Yes |
| **X — no truth exists.** Reviewer cannot read the original. 2 left blank, 7 annotated as unreadable in the value field. | 9 | Excluded by design |
| **F — fabrication.** The token is absent from the original entirely; OCR produced a number that is not there. | 1 | **No** |
| **T — tokenization damage.** The digits are right but the number's structure is destroyed, so one printed number becomes several tokens. | 7 | **No** |
| **L — cross-alphabet misread.** A letter was read as a digit; the true reading contains no digit and so is not a material token under ADR-004. | 2 | **No** |

### Why each unscorable class breaks the rule

**F, fabrication.** Page 12 retains `9924` where the reviewer reports no such number on the
page. Section 5 asks whether a truth token is *present*. There is no truth token, so the
question has no answer. Fabrication requires the opposite test — that the token is **absent** —
and a configuration that repairs a substitution while continuing to invent a value has not
improved. This class is more serious than substitution: a fabricated figure is
indistinguishable from a real one downstream, and nothing in the pipeline contradicts it.

**T, tokenization damage.** On page 6 a printed `2,500.00` is retained as `2.500` followed by
`00`. Asked for the truth of the token `00`, the reviewer correctly answered `00` — the
fragment is right. The number is not. Per-token truth cannot express this defect, because the
unit of damage is the printed number and the unit of measurement is the token. Recording these
as "truth equals retained value" would score them as *correct*, which is precisely backwards.

**L, cross-alphabet misread.** Page 9 retains `2` where the original prints `s`, and `7` where
it prints `T`. The true reading is not digit-bearing, so it is not a material token under the
ADR-004 definition this instrument uses. It cannot enter a digit-token truth set at all.

### Consequence

Sections 4 and 5 are superseded by the revision below. The 8 class-S rows and the 9 class-X
exclusions stand. The 10 rows in classes F, T and L require a second reviewer pass before the
truth set is complete, described in Section 4b.

## 4b. Second reviewer pass — required before freezing

1. **Class T (7 rows).** For each, record the **complete number as printed**, not the fragment
   — `2,500.00`, not `00`. The truth unit for these rows becomes the printed number, and
   scoring becomes whether the candidate retains that number as a single token.
2. **Class F (1 row).** Confirm the token is absent from the page, so it can be registered as
   an `expect_absent` assertion.
3. **Class L (2 rows).** Confirm the true characters. These leave the digit-token truth set and
   are recorded as a separate cross-alphabet register, scored but reported apart from the
   digit-token totals.
4. **One class-S row needs confirmation.** Page 1 line 1 retains `75` in the context
   `75.) BUREAU OF INTERNAL REVENUE` and was verdicted a substitution with truth `75`. Whether
   this is class T, class F, or a verdict to withdraw is not inferable from the record.
5. **One consistency item.** Page 6 line 30 retains `2.500` for a printed `2,500` and that
   token was verdicted faithful, while the structurally identical `3.214` on line 34 was
   verdicted a substitution. The reviewer should reconcile the two. This is raised as a
   question, not corrected by engineering.

## 5. Scoring rule

**Revised 2026-08-20 following Section 4a, before any candidate has run.** The original
single-test rule is replaced by three assertion types. The zero-regression decision rule in
Section 6 is unchanged and applies across all three.

Each truth row carries one assertion:

- **`expect_present`** — classes S and T. The truth string, normalized by the ADR-004
  tokenizer, must appear in the candidate page's token multiset with count greater than or
  equal to its truth count.
- **`expect_absent`** — class F. The fabricated token must **not** appear in the candidate
  page's token multiset. A candidate that still produces it fails this row.
- **`cross_alphabet`** — class L. Scored on the true characters and reported separately from
  the digit-token totals, since the ADR-004 material-token definition does not cover them.

Class X rows carry no assertion and are excluded from every denominator, which is reported
explicitly so the total is never silently taken as 27.

For each candidate, for each of the 12 OCR-retained pages:

1. Tokenize the candidate's retained page text with the ADR-004 tokenizer, unmodified.
2. Build the page's truth multiset from Section 4.
3. Each truth row is **satisfied** according to its assertion type above.

**Matching is exact normalized token equality. Substring containment is forbidden.** This is
stated as a rule, not a detail: the EXP-01 fact scorer's join-match accepted `772024` inside
the corrupted `1772024`, and that is how MF-01 escaped detection. This instrument must not
inherit that defect.

Per candidate, report against `C0`:

- `satisfied` of 289;
- `repairs` — truth tokens unsatisfied at `C0` and satisfied by the candidate;
- `regressions` — truth tokens satisfied at `C0` and unsatisfied by the candidate;
- `residual` — truth tokens unsatisfied by the candidate;
- per-page elapsed time, peak memory, and timeout adherence;
- text SHA-256 per page for both passes.

## 6. Decision rule — frozen

A candidate is **eligible** only if **all** hold:

1. `regressions == 0`;
2. every page completes within the existing per-page timeout;
3. two independent passes produce identical text SHA-256 for all 12 pages;
4. zero outbound network connections during the run;
5. source checksums, byte counts and page counts are unchanged between preflight and
   postflight.

**Select** the eligible candidate with the greatest `repairs`. Ties break to the lower DPI,
then to the `fast` model — cheaper wins, so cost never argues for a heavier configuration that
bought nothing.

If **no candidate is eligible**, select none and record EXP-07 as failed. The zero-regression
condition is not relaxed, and no candidate is chosen as least-bad.

## 7. What selection does and does not mean

Selection means one configuration measurably repairs substitutions without breaking anything
already correct. It does **not** mean:

- **that EXP-01 passes.** EXP-01 reruns separately under its existing unchanged criteria.
- **that OCR output is now trustworthy.** With `residual > 0`, substitutions remain. With
  `residual == 0`, substitutions remain *undetectable* rather than absent — SF-01 is untouched
  by this experiment and no fidelity result closes it. ADR-009 Section 5 governs.
- **that omission is addressed.** The instrument scores only tokens the baseline retained. A
  token OCR drops entirely has no truth row and cannot be scored. A candidate that newly
  retains a correct token the baseline dropped receives no credit for it.

## 8. Failure behavior

Select no configuration. Preserve the failure record. Revise the candidate set in a **new**
preregistration — page segmentation mode and image preprocessing are the named next factors —
and rerun. Do not widen the matrix inside this run after seeing results, and do not weaken
Section 6.
