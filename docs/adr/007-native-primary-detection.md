# ADR-007: Native-primary retention with non-retaining completeness detection

**Status:** Accepted 2026-08-19 by Kim, on the design reasoning in
Sections 1-3 and the native-primary retention measurement. The empirical gate
remains EXP-01's existing preregistered criteria; acceptance of this record
does not assert that EXP-01 passes.
**Date drafted:** 2026-08-19
**Supersedes if accepted:** [ADR-004](004-extraction-completeness.md) `native-page-token-coverage-v1`
**History:** [ADR-005](005-material-token-omission.md) rejected 2026-08-19;
[ADR-006](006-single-observer-adjudication.md) rejected on condition 7.1 (88 single-observer
tokens against a ceiling of 20)
**Basis:** Full-corpus conflict taxonomy, set-coverage and boundary diagnostics, and the
native-primary retention measurement, all under `evaluation/runs/EXP-01/`

> **Gating.** This record proposes a design and is argued on design reasoning. It defines
> **no activation condition of its own.** The empirical gate is EXP-01's existing
> preregistered criteria, unchanged. ADR-005 and ADR-006 each failed on a bespoke gate that
> was stricter than, and measured something other than, the policy it gated. That pattern
> is not repeated here.

## 1. What the diagnostics established

Three read-only diagnostics over the nine approved documents and 41 physical pages:

| Finding | Evidence |
|---|---|
| ADR-004's multiset comparison scored parser surplus as source conflict | 843 `surplus_copies` against 1 `absent_from_native` |
| Docling omits material content Poppler retains | 87 native-only material tokens: 31 page folios, 8 fused footnote-marker headers, 39 dropped table rows, 6 TOC entries, 3 boundary artefacts |
| Docling misattributes text across page boundaries | RR 11-2024, both boundaries: Docling's page-N export carries page-N+1 prose, moved not copied, following paragraph structure |
| Poppler's page assignment matches the paper | Boundary 2→3 verified against the rendered original: page 2 visibly ends mid-sentence, page 3 visibly opens with the clause |
| Docling contributes no content native lacks | On all five pages ADR-005 §4.8 would have preferred Docling, the two token multisets are occurrence-for-occurrence identical |
| Native-primary retains everything | 29/29 text-layer pages, 12/12 scanned pages via Tesseract, 41/41 total; minimum native page 462 meaningful characters against a 40-character floor |

### 1.1 The ADR-005 rejection, re-read

The lone `absent_from_native` token — a bare `3` on RR 11-2024 page 1 — is Docling
carrying page 2's opening fragment (`Section 3(D)(3) of RR No. 7-2024`) into its page-1
export. Native page 1 correctly ends mid-sentence; native page 2 opens with the fragment,
both `3`s present.

The ADR-005 rejection stands procedurally: the condition was per-page, frozen before the
evidence, and failed as written. But its evidentiary basis now reads differently. The token
was never absent from the native representation at document scope. It was the page-identity
defect leaving a fingerprint, and a per-page comparison read that fingerprint as a native
omission.

**This is the load-bearing lesson.** Per-page comparison between two observers is unsound
when one of them misattributes content across page boundaries. Any comparison this project
performs must account for that.

### 1.2 The disqualifying defect in mixed retention

ADR-005 §4.7 retains 41/41, which looks like a pass and is not one.

At RR 11-2024 boundary 2→3, native p2 is retained (Docling p2 misses two material tokens)
and Docling p3 is retained (§4.8 preference). Native p2 does not hold the straddling clause
— native correctly places it on page 3. Docling p3 does not hold it either — Docling moved
it into a page-2 export that was not retained. **The 26-word clause survives on no retained
page.** It contains no digit-bearing token, so the material gate is blind to it, and both
pages clear the 0.90 lexical floor.

That is undetected material content loss: the precise EXP-01 failure class, reproduced
under the proposed replacement. At boundary 1→2 the same mechanism produces the other
symptom — Docling p1 retained under a `pdf-page:1` pointer while carrying page-2 text,
which is a citation resolving to the wrong page and a direct violation of invariant 2.

Both arise specifically from **mixed-method retention across an attribution boundary**.

## 2. Decision

Adopt `native-primary-detection-v1`.

### 2.1 Retention

1. Poppler `pdftotext -layout -nopgbrk` produces the retained candidate for every physical
   page whose native layer meets `KENDRA_MINIMUM_PAGE_TEXT_CHARS`.
2. Pages below that floor use whole-page Tesseract, unchanged from ADR-004.
3. **Docling is removed from the retention path.** No page is retained from a Docling
   candidate.
4. The retained block remains the whole physical page. Pointers remain
   `pdf-page:<one-based-number>;block:whole-page;method:<pdf_text|tesseract>`.
5. Original PDF bytes and their checksum remain authoritative.

Retention is therefore single-method per page and, for any document without a
sub-floor page, single-method per document. No attribution boundary can split it.

### 2.2 Non-retaining completeness detection

Removing Docling from retention must not remove the second observer. ADR-004 exists
because parser success is not proof of completeness, and native-primary as a bare rule
would trust one parser exactly as the original 40-character gate did — better observer,
same structural defect.

Docling is therefore retained as a **detector that never contributes retained text**:

6. Docling produces a candidate for every page of every document, with internal OCR
   disabled.
7. Comparison is over **distinct material-token sets at document scope**, not per page.
   Per-page comparison is unsound under §1.1 and is not performed.
8. A **material token** is a token containing at least one digit, unchanged from ADR-004's
   high-signal definition.
9. If Docling's document-scope material token set contains any token absent from the
   retained representation's document-scope material token set, the **document** fails
   closed with a content-free `extraction_completeness_conflict`.
10. Docling holding tokens native also holds, in any quantity or on any page, is not a
    conflict. Occurrence counts carry no decision weight.
11. Docling's page attribution is never used, never recorded, and never resolves a
    citation.

On the approved corpus this yields zero conflicts: the single Docling-only material token
is present in the native representation at document scope.

### 2.3 Versioned runtime configuration

- `KENDRA_EXTRACTION_COMPLETENESS_POLICY=native-primary-detection-v1`
- `KENDRA_MINIMUM_PAGE_TEXT_CHARS=40`

`native-page-token-coverage-v1` remains a valid configuration value and available as
containment. `KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT` is **not used** by this
policy: lexical coverage between candidates was a proxy for completeness, and document-scope
material-token containment measures it directly. Removing an unused threshold is not a
weakening; no retained page is admitted that the old floor would have excluded, because
the old floor gated a Docling path this policy does not have.

## 3. Why single-method retention is the correct shape

The alternative framings all preserve mixing:

- **Method consistency per document** collapses in practice — a document is only as good as
  its worst page, so RR17 lands entirely on native regardless, and Docling's complexity is
  carried for a path it rarely wins.
- **Boundary detection as a gate** builds a detector against a mechanism nobody has
  characterized. The ~34.5× within-page duplication on RMC 03-2024 page 1 is unexplained
  and co-occurs with dropping that page's TOC tail — one uncharacterized behaviour with
  two known symptoms. A detector for a third symptom is a patch on a black box.

Single-method retention eliminates the defect by construction rather than detecting it.

## 4. What this costs

**Reading order on two pages.** Registration Checklist pages 3–4 have token-identical
candidates in different sequence. Docling's layout-aware order is the only representational
content mixed retention held that this policy gives up. Accepted.

**Layout-aware extraction generally.** Table structure, reading order, and cell
relationships are unavailable at this milestone. This is a real cost against EXP-03 and is
addressed in §7.

**Nothing in token content.** On every page ADR-005 would have retained from Docling, the
two multisets are identical. Docling contributes no material token anywhere in the corpus
that native lacks at document scope.

## 5. Consequences

### Positive

- No retained page can carry another page's text, so citation page-resolution holds.
- Boundary-straddling content cannot be lost between two retained pages.
- Representation rises from 20/41 pages under containment to 41/41.
- A second independent observer is preserved, at the scope where it is sound.
- The retained representation for physical page 15 contains both
  `175,284,574.00` and `169,021,829.87` with page-15 provenance.

### Negative and limitations

- Detection is document-scope, so it cannot catch native placing real content on the wrong
  page. Nothing in the corpus evidences that, and Poppler's assignment was verified against
  rendered originals at both RR 11-2024 boundaries, but the property is unproven in
  general rather than established.
- Material tokens remain digit-bearing only. A materially omitted **word** is not detected
  by this gate at all — the ADR-005 §6 gap persists, and the 0.90 lexical floor that
  partially covered it is gone with the Docling path. Prose omission by Poppler is
  currently caught by nothing.
- Docling's unexplained duplication behaviour is out of the retention path but not
  resolved. It affects the detector's occurrence counts, which carry no decision weight.
- Tesseract remains derived assistance with its existing recognition error, including the
  known RMC 77-2024 page-1 header corruption, unchanged by this policy.
- Visual and layout completeness of the native layer is unverified beyond token evidence
  and two boundary spot-checks against rendered originals.
- Engineering representation only. No source authority, currency, applicability, or legal
  or tax interpretation is established.

## 6. Regression coverage required before activation

- no page is ever retained from a Docling candidate, under any candidate configuration;
- a page above the character floor is retained from native; below it, from Tesseract;
- a document where Docling holds a material token absent from the native representation at
  document scope fails closed;
- a document where that token is present on **any** native page passes, including when
  Docling attributes it to a different page than native does;
- an RR 11-2024-shaped boundary fixture — Docling page N carrying page N+1's opening
  clause — produces no conflict and no retention change;
- page-15 fixtures retain both totals with `pdf-page:15` provenance;
- retained text is never modified, merged, or reordered from the native candidate;
- physical pages remain contiguous and one-based;
- repeated extraction remains deterministic;
- the 12-page scanned circular remains wholly on the Tesseract path;
- original bytes are unmodified;
- no extracted content or secret appears in errors or captured logs.

## 7. Conditions for Docling's return

Removal is scoped to Milestone 9 retention and is not a permanent verdict. Chunking at this
milestone is deterministic character-offset windowing that consumes no layout structure, so
Docling currently costs page-identity correctness to buy something nothing uses. EXP-03 will
need layout back. It returns under its own ADR, and only when:

1. the boundary attribution behaviour is characterized, with a detection or configuration
   answer rather than an observation;
2. the within-page duplication mechanism is identified;
3. the approved corpus contains enough multi-page prose to sample straddling paragraphs —
   see §8.

## 8. Open items, not resolved by this record

**Corpus under-sampling.** RR 11-2024 is the only multi-page prose document in the corpus
and exhibits boundary attribution at 2 of 2 boundaries. LGU and BIR material is
predominantly multi-page prose. At least one further multi-page prose regulation is required
before any retention policy is declared fit; adding it changes the approved corpus and needs
its own governance step under the data-governance record.

**Gold-case scoping.** Cross-document cases KND-M5-CD-001, -003 and -010 expect document
numbers (`RMC No. 77-2024`, `RR No. 11-2024`, `RMC No. 3-2024`) on interior pages where
those strings appear only on page 1. No page-faithful retention rule satisfies them. This is
a gold-case defect requiring expert review, recorded here and **not** acted on:
`evaluation/gold_cases.json` retains `initial_expert_review_required` and is not edited by
this ADR.

**Prose-omission detection.** With the lexical floor gone, no mechanism detects Poppler
omitting non-digit material content. A future record should address this; it is out of
scope here.

**Fact-check standard.** The native-primary measurement classified 68 of 125 gold facts as
having benign token misses — paraphrase, inflection, normalization joins, numeric
formatting — by inspection. That is a read-only diagnostic, not preregistered scoring. The
EXP-01 rerun must score every fact under its preregistered rubric, and the rerun result, not
the measurement, determines the outcome.

## 9. Preregistration and rerun

Before any corpus processing or scoring, a new ignored run registration frozen with: prior
invalidated run IDs `20260817T085707+0800-3ce70b6` and
`20260817T111818+0800-b6036ba-repair1`; current Git revision; source-manifest and
evaluation-dataset checksums; the exact retention and detection rules; all candidates with
versions, model checksums, and configuration; fail-closed rules; hardware and timeouts;
reviewer rubric; and start time.

Criteria are EXP-01's existing preregistered criteria, unchanged. EXP-01 returns to `passed`
only if every one passes over all nine documents and all 41 physical pages, across two
deterministic passes.

## 10. Scope

This record does not change `evaluation/gold_cases.json` from
`initial_expert_review_required`. It validates representation fidelity, not legal or tax
interpretation. It implements no retrieval or question-answering behaviour. A passing EXP-01
permits layout-aware EXP-03 work to resume but does not itself pass EXP-03 or unblock
Milestone 10.
