# ADR-006: Single-observer material token adjudication

**Status:** Proposed. **Not accepted and not activated.** Activation is blocked pending the
Section 7 condition.
**Date drafted:** 2026-08-19
**Builds on:** [ADR-005](005-material-token-omission.md), closed as rejected 2026-08-19
**Active policy while this is proposed:** [ADR-004](004-extraction-completeness.md)
`native-page-token-coverage-v1`, retained as fail-closed containment

> **Disclosure.** This record was drafted **with the ADR-005 diagnostic dataset in hand**.
> It was drafted **before** the source-page observation of the RR 11-2024 page 1 `3`
> token. That ordering is deliberate: this ADR must not be a rule written to accommodate
> a token whose nature was already known. The rule below is general, special-cases no
> document, page, or token, and would have been written identically had the diagnostic
> surfaced a different single-observer token. The `3` becomes the first application of the
> rule, not its justification.
>
> No threshold or rule in this record may be altered after any new evidence is examined.

## 1. What the ADR-005 diagnostic established

The bounded conflict-taxonomy diagnostic produced 843 `surplus_copies` classifications and
**one** `absent_from_native` classification across the three failing documents.

| Finding | Status |
|---|---|
| ADR-004's multiset comparison scored parser surplus as source conflict | Confirmed |
| Physical page 15 omission is a Docling omission, not a native defect | Confirmed; both totals present in native, once each |
| Rejected tokens are overwhelmingly duplication artefacts | Confirmed; 843 of 844 |
| Docling `export_to_text(page_no=...)` preserves physical page scope | Confirmed for RMC 03-2024; page-1 output is a strict subset of native page-1 vocabulary and contains none of native page 2's 104 page-2-only tokens |
| Normalization artefacts inflate `absent_from_native` | Not observed; no fragment or separator-variant tokens found |

ADR-005 was nonetheless rejected, because its Section 3.1 required **zero**
`absent_from_native` material tokens and one was found. That threshold was frozen before
the evidence existed and was not weakened after it arrived.

## 2. The question ADR-005 did not answer

ADR-005 treated Docling and Poppler as observers of equal standing and took the union of
their material token sets as the proxy for material page content. That construction has no
resolution path for a **single-observer material token** — a digit-bearing token that
exactly one candidate reports. Under ADR-005 such a token makes the union unsatisfiable by
the non-observing candidate, and if the observing candidate is unretainable for any other
reason the page fails permanently, with no mechanism to establish what is actually on the
page.

This is the correct default. Fail-closed on an unresolved observation is the binding
invariant. But it is not a complete design, because the project already holds an authority
capable of resolving it: **the original document.** Invariant 1 states the preserved
version is authoritative and extracted text is not. A disagreement between two derived
representations is exactly the case that authority exists to settle.

The architecture already anticipates this. The error table entry for conflicting sources
reads: *authorized human adjudicates outside the model.* No mechanism was ever specified.

## 3. Decision

Adopt `material-token-omission-v2`: the ADR-005 Section 4 policy, **unchanged in every
respect**, plus a frozen adjudication register for single-observer material tokens.

ADR-005 Section 4 is incorporated by reference in full — distinct-set comparison, the
observed material set, the retainability test, the 0.90 distinct-token coverage floor
carried over unchanged, preference order Docling → native → Tesseract, whole-page blocks,
`pdf-page:<n>;block:whole-page;method:<method>` pointers, and no merging under any
circumstance. Nothing in that section is relaxed, and no threshold is re-tuned.

### 3.1 Single-observer material token

A material token reported by exactly one usable candidate for a given physical page. A
token reported by two or more candidates is not single-observer regardless of occurrence
counts, and a token reported by none does not exist.

### 3.2 Adjudication

Each single-observer material token requires a recorded human observation of the
**original PDF page** before that page may be retained. The adjudicator records exactly
one verdict:

- **`present_in_source`** — the value is visibly present on the physical page. The
  observing candidate is correct; the non-observing candidate omitted material content.
- **`absent_from_source`** — the value is not visibly present. The observing candidate
  emitted a token the page does not contain, typically structural: a footnote or reference
  marker, list or section numbering, a header or folio artefact, or a synthesized table
  element.

There is no third verdict. An adjudicator who cannot determine which applies records
nothing, and the page fails closed.

### 3.3 Effect on retainability

The observed material set is recomputed as the union of all candidates' material tokens,
**minus** every token adjudicated `absent_from_source` for that page. Tokens adjudicated
`present_in_source` remain in the set and are binding.

Retainability is then evaluated under ADR-005 Section 4.7 against that adjusted set. In
particular:

- a candidate lacking a `present_in_source` token is **not** retainable, without exception;
- a candidate emitting an `absent_from_source` token is not penalised for it, and the token
  does not obligate any other candidate;
- an `absent_from_source` verdict does **not** remove the token from the retained text. The
  retained block is one whole unmodified candidate. Only the comparison set changes.
- if no candidate is retainable after adjustment, the page fails closed as before.

### 3.4 Register format

Adjudications live in a single JSON register under the gitignored `evaluation/runs/` tree,
frozen and checksummed before any rerun, on the same terms as a preregistration. Each
entry records: document filename and source SHA-256; one-based physical page; the
normalized token; the observing candidate; the verdict; the adjudicator; the UTC
timestamp; and a free-text basis naming what was seen on the page.

The register is keyed on `(source_sha256, page_number, token)`. It is scoped to exact
source bytes: a new document version invalidates every adjudication against the old
checksum. The register's SHA-256 is recorded in the ADR and in the run preregistration.

## 4. Guards against adjudication becoming a rubber stamp

This mechanism can degrade into "approve whatever blocks the run." These constraints are
part of the frozen policy, not operational guidance:

1. **Per-token, never per-rule.** An adjudication authorizes one token on one page of one
   source checksum. No pattern, regex, class, or blanket exemption is admissible.
2. **Frozen before rerun.** The register is checksummed before corpus processing. Adding an
   entry after seeing rerun output invalidates the run exactly as amending a
   preregistration would.
3. **Source observation required.** The basis field must name what was seen on the physical
   page. An entry whose basis restates the token, cites parser behaviour, or cites the
   diagnostic is void — those are not observations of the original.
4. **`present_in_source` cannot be traded away.** It always binds. There is no path by
   which a value confirmed visible on the page is excluded from the comparison set.
5. **Volume is itself evidence.** Every EXP-01 record must report the adjudication count.
   Above **20 adjudications across the 41-page corpus**, the extraction configuration is
   declared unfit regardless of whether the run otherwise passes, and EXP-01 fails. A rule
   requiring human resolution of half a percent of pages is a gate; one requiring it at
   scale is a parser that does not work.
6. **No self-adjudication of convenience.** Where a page has more than one single-observer
   token and they resolve inconsistently — some `present_in_source`, some
   `absent_from_source`, on the same candidate — the record must state why, since a
   candidate both omitting real content and inventing tokens on one page is a signal about
   that candidate, not about the page.

## 5. Why this is stricter than ADR-005, not looser

ADR-005 had no adjudication step. v2 adds a mandatory human observation of the
authoritative artefact before certain pages may be retained, and adds a corpus-level
adjudication ceiling that can fail a run which otherwise passes every criterion.

What changes is that a page blocked by a token **confirmed not to exist on it** stops being
permanently unretainable. That is not a weakened criterion; it is a corrected one. ADR-005
treated every single-observer token as evidence about the page. Some are evidence about the
parser, and only the original document distinguishes them.

The direction of the asymmetry is worth stating plainly, because it is tempting and must
not be assumed: a layout model synthesizes structure and can emit tokens the page does not
contain, while a text-layer dump largely omits or reorders rather than invents. **This ADR
does not encode that asymmetry.** It does not privilege either candidate. Every
single-observer token, from either parser, in either direction, requires the same recorded
observation of the original.

## 6. Consequences

### Positive

- Pages blocked solely by a structural artefact become retainable, on recorded evidence.
- The authoritative artefact — the original page — becomes the resolver of derived
  disagreement, as invariant 1 and the architecture error table already require.
- Every such resolution is checksummed, attributable, and reproducible.
- Fail-closed remains the default: no adjudication means no retention.

### Negative and limitations

- Ingestion is no longer fully automatic for affected pages. This is intended.
- Adjudication quality is bounded by the adjudicator. A careless `absent_from_source`
  verdict admits a page that omits real content, and no downstream check catches it.
- The register is per-checksum, so a reissued document discards its adjudications.
- Every ADR-005 Section 6 limitation carries over unchanged: set comparison misses
  repetition errors, material tokens remain digit-bearing only, and a materially omitted
  **word** is still caught only by the coarse 0.90 lexical floor.
- Engineering representation only. No source authority, currency, applicability, or
  legal or tax interpretation is established.

## 7. Activation condition (fixed at drafting time)

This ADR may be accepted **only if all four hold**:

1. **Bounded population.** Across all nine approved documents and all 41 physical pages,
   the total count of single-observer material tokens is **20 or fewer**. The diagnostic
   already covers three documents and found one; the remaining six must be measured before
   this condition can be evaluated.
2. **Every one adjudicated.** Each is resolved by a recorded source-page observation
   meeting Section 4.3, with no `unresolved` entries and no page left partially adjudicated.
3. **Corpus retention.** With the register applied, all 41 physical pages are retainable
   under ADR-005 Section 4.7 across two deterministic passes. A page still failing closed
   after adjudication rejects this ADR — the remaining defect is not single-observer
   disagreement.
4. **Duplication magnitude explained.** The ~34.5× within-page occurrence inflation on
   RMC 03-2024 page 1 (13,592 Docling occurrences from 188 distinct tokens against 394
   native occurrences) is identified as a specific, named Docling behaviour. It does not
   affect a set-based rule, but an unexplained parser behaviour of that magnitude may not
   be carried silently into an accepted configuration.

If any condition fails, Section 10 applies.

## 8. Regression coverage required before activation

The full ADR-005 Section 7 list applies unchanged. In addition:

- a single-observer material token with no register entry fails the page closed;
- an `absent_from_source` verdict removes the token from the observed material set and the
  page becomes retainable;
- an `absent_from_source` verdict does **not** alter the retained candidate's text;
- a `present_in_source` verdict keeps the token binding and rejects any candidate lacking it;
- a register entry keyed to a different `source_sha256` does not apply;
- a register entry keyed to a different page number does not apply;
- a token observed by two candidates is not single-observer and is never adjudicable;
- an entry with an empty or missing basis field is rejected as void;
- exceeding the 20-adjudication corpus ceiling fails the run;
- register mutation after freeze is detected by checksum and invalidates the run.

## 9. Preregistration required before rerun

As ADR-005 Section 8, plus: the adjudication register SHA-256; the adjudication count; and
the register content frozen before corpus processing. Prior invalidated run IDs
`20260817T085707+0800-3ce70b6` and `20260817T111818+0800-b6036ba-repair1` carry forward.

EXP-01 returns to `passed` only if every preregistered criterion passes over all nine
documents and all 41 physical pages, across two deterministic passes, within the
adjudication ceiling.

## 10. If the activation condition fails

This ADR is closed as rejected. `native-page-token-coverage-v1` remains in force as
containment. EXP-01 remains failed, EXP-03 remains failed and blocked, Milestone 10 remains
blocked.

A failure of condition 1 or 3 means single-observer disagreement is not the residual
defect, and the next design is region-aware structured/native reconciliation with explicit
per-region provenance and no silent merge — a materially larger change requiring its own
architecture decision, which this record does not authorize.

## 11. Alternatives considered

### Treat all single-observer Docling tokens as artefacts

Rejected. It encodes the parser asymmetry described in Section 5 as an assumption rather
than an observation, and would admit any page where Docling invents plausible-looking
values. It also happens to be the rule that would have waved the RR 11-2024 `3` through
without anyone looking at the page, which is precisely the ADR-004 failure mode.

### Exclude single-digit or short tokens from the material definition

Rejected. It is a threshold chosen to fit one observed token. A single-digit table cell is
material content, and the rule would silently discard it corpus-wide.

### Require adjudication of every conflicting page rather than every single-observer token

Rejected as too coarse. Page-level adjudication invites approving a page on general
impression; token-level adjudication forces the adjudicator to locate one specific value.

### Add a third parser to break ties

Deferred, as in ADR-004 and ADR-005. Three derived observers still cannot establish what is
on the page; only the original can. A third parser would reduce adjudication volume, not
remove the need for the mechanism.

### Region-aware reconciliation now

Deferred. It remains the stated fallback in Section 10 and is likely the eventual design.
It is disproportionate if the residual defect is a handful of structural artefacts, and
Section 7 condition 1 is what decides which situation this is.

## 12. Open item carried forward

The RMC 03-2024 page-1 duplication magnitude is unexplained and is condition 7.4.
Candidate mechanisms to investigate: TableFormer span replication across merged cells,
`traverse_pictures=True` re-traversing embedded text, or repeated item emission in the
Docling 2.117.0 `export_to_text` path. A bounded investigation is required; no result is
claimed here.

## 13. Scope

This record does not change `evaluation/gold_cases.json` from
`initial_expert_review_required`. It validates representation fidelity, not legal or tax
interpretation. It implements no retrieval or question-answering behaviour. A passing
EXP-01 permits layout-aware EXP-03 work to resume but does not itself pass EXP-03 or
unblock Milestone 10.
