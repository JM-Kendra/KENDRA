# ADR-009: OCR render resolution and recognition model fidelity

**Status:** Proposed. **Not accepted and not activated.**
**Date drafted:** 2026-08-20
**Amends:** [ADR-007](007-native-primary-detection.md) `native-primary-detection-v1`, active —
the OCR branch only. The native retention path, the 40-character floor, the detector's
demotion, and page identity are untouched.
**Active policy while this is proposed:** ADR-007, unchanged in every respect.
**Related:** [ADR-008](008-ocr-fidelity-and-detection.md), proposed — detection.
This record is about *fidelity*. They are separate problems and neither substitutes for the
other.

> **Disclosure.** This record was drafted **with the 2026-08-20 substitution measurement in
> hand** — 27 substitutions in 306 digit-bearing tokens across the 12 OCR-retained pages, in
> `docs/experiment-decisions/ocr-substitution-measurement.md`. That ordering is stated plainly.
> The measurement is what establishes that a fidelity problem exists at all; without it this
> record would be speculation. The candidate configurations below are argued from the
> installed toolchain's defaults, not from which tokens happen to be wrong.

## 1. What the measurement established

Of 306 digit-bearing tokens on the 12 OCR-retained pages: 262 faithful, **27 substitutions
(8.8%)**, 17 originals unreadable. Seven of twelve pages carry at least one substitution;
pages 2, 4, 5, 8 and 10 are clean. Page 6 alone carries 13 of 41, clustered inside a
reproduced sample invoice where currency amounts lost decimal separators and digits.

The distribution matters: clean prose pages alongside one badly damaged figure region is the
signature of insufficient effective resolution and layout handling on a degraded sub-image,
not of a recogniser that cannot read the document.

## 2. What the active configuration actually is

ADR-007's OCR branch is `pdftoppm -r 300 -png` followed by `tesseract <png> stdout -l eng`.
Three properties follow, none of them deliberate choices recorded in any ADR:

1. **Render resolution is 300 DPI.** Adequate for body text, which is where the clean pages
   are. The page-6 invoice is a raster image nested inside a scanned page, so its effective
   resolution is a fraction of the page's; thin glyphs and decimal separators fall to a few
   pixels.
2. **The recognition model is Debian's `tesseract-ocr-eng`,** which ships the *fast* integer
   LSTM model. The `best` float model is materially more accurate on degraded input and is
   not installed.
3. **No page segmentation mode is specified,** so Tesseract 5.3.0 uses PSM 3, fully automatic
   layout analysis, on every page including mixed prose-and-figure pages.

These are the toolchain's defaults. They were inherited, never selected against evidence.

## 3. Decision proposed

Raise OCR fidelity by changing **render resolution** and **recognition model** only, selected
by a preregistered experiment (EXP-07) rather than by inspection.

**Page segmentation mode is deliberately excluded from this record.** Altering layout analysis
could regress the five currently clean pages, and no principled basis exists for preferring
another mode for mixed content. If EXP-07's selected candidate leaves substitutions
outstanding, PSM belongs in a separate record with its own preregistration — not appended here
once results are visible.

## 4. Gating

This record defines **no activation condition of its own**, following ADR-007 and ADR-008.
ADR-005 and ADR-006 each failed on a bespoke gate that measured something other than the
policy it gated; this record does not repeat that.

Its empirical gate is **EXP-07**, whose candidate matrix, truth set, scoring rule and decision
rule are frozen before any candidate is run. Adoption additionally requires EXP-01 to rerun
under the selected configuration against its existing unchanged criteria.

## 5. What this record does not claim

- **It does not close SF-01.** A more accurate recogniser is still an unverified one. With no
  detector on OCR pages, an improved substitution rate would be believed rather than
  established. Invariant 4 fails closed on unverifiable evidence; ADR-008 or an equivalent
  remains necessary regardless of EXP-07's outcome.
- **It does not repair the 17 unreadable originals.** Where the rendered source is illegible
  to a human reviewer, no render or model change recovers information the paper does not
  carry. Those regions need a disposition decision, not a configuration change.
- **It does not address omission.** The measuring instrument inventories retained tokens, so a
  token OCR drops entirely is invisible to it. ADR-007 Section 8 carries this open.
- **It does not return EXP-01 to `passed`,** and it does not unblock EXP-03 or Milestone 10.

## 6. Costs

Higher resolution increases render time, image size and OCR time roughly with the square of
DPI; the `best` model is several times slower than `fast`. EXP-07 records timing and peak
memory per candidate, and the 12-page document must stay inside the existing per-page timeout.
A candidate that cannot meet the timeout is not selectable regardless of accuracy.

Installing `best` model data adds a build-time artifact that must be version-pinned and
checksum-recorded, since the recognition model becomes part of the reproducibility surface.

## 7. Alternatives considered

**Do nothing.** Rejected. An 8.8% substitution rate in a corpus region carrying monetary
amounts is not compatible with citation-verifiable answering, and the region has no detection.

**Tune settings against the 306 measured tokens until the count drops.** Rejected, and named
here explicitly because it is the attractive path. Selecting a configuration by how well it
repairs the specific tokens known to be broken is fitting to the answer sheet. It is the same
error class that invalidated EXP-01 twice. EXP-07 fixes its candidate list and decision rule
before any candidate runs.

**Preprocess images (deskew, binarise, upscale).** Deferred. It adds a stage with its own
parameters and failure modes. Establish what resolution and model alone achieve first.

**Replace Tesseract.** Deferred. A different engine changes the component family fixed by the
MVP specification and would require revisiting ADR-001 and the architecture record.

## 8. Revisit when

Revisit if EXP-07 selects no candidate, if the selected candidate cannot meet the timeout, or
if omission detection later shows that substitution was the smaller of the two defects.
