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

## 5. Scoring rule

For each candidate, for each of the 12 OCR-retained pages:

1. Tokenize the candidate's retained page text with the ADR-004 tokenizer, unmodified.
2. Build the page's truth multiset from Section 4.
3. A truth token is **satisfied** when the candidate page's normalized token count for that
   token is greater than or equal to its truth count.

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
