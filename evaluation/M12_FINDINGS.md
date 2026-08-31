# Milestone 12 findings — live gold evaluation root-cause review

**Status:** a review of one live gold-evaluation run (`evaluation/runs/M12-gold/20260831T125331Z-0bcc9dd7`,
source revision `0bcc9dd7d0aaf7bd370e8d3eb60303a42e8ef91c`, clean tree). This document
does not change answering behavior and does not reopen M10, EXP-01, or EXP-03. Per
`docs/milestones/M12_STATUS.md`, Milestone 10 answering is an unaccepted prototype;
nothing here is evidence toward accepting it. This is diagnosis, not repair.

Every claim below was checked against the live services (read-only) rather than
inferred from category or filename pattern-matching — see the "how this was checked"
note under each finding. An earlier verification pass in this conversation guessed
that several of the false negatives below were explained by the already-documented
SF-01 OCR blind region and the RMC 03-2024 page-duplication finding, purely because
the same document names were involved. That guess was checked here and was **wrong**
for every case it was applied to — see part (b). It is recorded as wrong rather than
quietly corrected, consistent with this project's rule against re-litigating results
without leaving the trail.

## (a) `KND-M5-UN-002` — a temporal-boundary defect, proposed for the M10 contract

**Case:** *"Is RR No. 7-2024 still the controlling invoicing regulation as of August
15, 2026?"* Expected `unsupported`
(`unacceptable_answer_behavior`: *"Claiming currentness or controlling status from
the absence of a later source in this bounded 2024 sample."*). Actual: `supported` —
*"RR No. 7-2024 is superseded by RR No. 11-2024 which amended the transitory
provisions of RR No. 7-2024, and the invoicing requirements are effective on April
27, 2024."*

**Why this is a defect, not a scoring artifact:** the two citations are legitimate —
real excerpts from the two named 2024 documents, correctly describing that RR
11-2024 amends RR 7-2024. The defect is specifically the unhedged claim that this
settles the regulation's status *as of August 15, 2026* — a date roughly two years
past the latest document date in the entire approved corpus. Nothing in a
2024-dated, nine-document sample can establish currentness at a 2026 date; the
model treated "no later contradicting source in this bounded sample" as proof of
"still controlling," which is exactly the reasoning `unacceptable_answer_behavior`
was written to name and reject. This is the single highest-severity result in the
run: a confident, citation-backed, factually-plausible-sounding answer to a
question the corpus cannot answer, with no hedge and no visible uncertainty.

**Proposed verification-contract rule (for M10, not implemented here):**

> A question that asks about a document's status, applicability, or controlling
> effect **as of a date later than every document's own date in the resolved
> evidence set** must be answered `unsupported`, or `supported` with an explicit,
> stated temporal bound (e.g., "as of \[latest document date], no supersession is
> recorded in this corpus; later issuances are not covered"). It must not assert
> continued or terminated controlling status at the later date without that bound.

This would sit alongside the existing frozen contract in
`apps/api/tests/test_milestone10_contract.py` (itself derived from `MVP_SPEC.md`,
ADR-003, and `EVALUATION_METHOD.md`, none of which currently name this failure
mode explicitly — `EVALUATION_METHOD.md`'s unsupported-answer section says an
answer "fails if it... treats absence as proof," which already covers this in
principle, but the contract has no test asserting it and no case in the frozen
gold set before `KND-M5-UN-002` exercised it end to end). Adding it to the actual
contract file is deliberately **not** done here: this project's rule is that
criteria are frozen before evidence is examined, and this rule is being proposed
*because of* evidence just observed, not before it. It belongs in a future
preregistration for M10's own review, not retrofitted into the existing frozen
contract now.

## (b) The 13 false negatives, root-caused against live retrieval evidence

**How this was checked:** for each case, the actual `QdrantRetriever` (same
`top_k=8`, `score_threshold=0.5` as the live run) was invoked directly against the
question, bypassing generation entirely, to see exactly what evidence the model was
given. This is diagnostic-only — read-only against the live Postgres/Qdrant/Ollama
services, nothing written, no answering code touched. RMC 03-2024's chunk table was
also queried directly to check whether the previously-documented page-1 duplication
(`CLAUDE.md`: "~34.5× Docling occurrence volume") is still present under the current
ADR-007 retention policy.

**Headline result: retrieval was not the bottleneck for most of these cases.** Of
13 false negatives: **2** tag as a verified cross-document retrieval limit, **11**
tag as unknown (9 where retrieval was fully correct and the cause lies elsewhere,
plus 2 with a narrower, partially-explained retrieval gap that still doesn't meet
the bar for a "cross-document retrieval limit" finding — detailed in their own
subsections below rather than glossed over). **Zero** are explained by an OCR gap,
and **zero** are explained by the page-duplication finding — that finding does not
reproduce in this corpus (checked directly, see below). Both of those were the
earlier, unverified guess; they are wrong.

### Cross-document retrieval limit (2 cases, verified)

Retrieval merges per-collection results by score and truncates to `top_k=8` total
*across all 9 documents' collections combined* — a comparison case needs both of its
documents to survive that shared, single merged window. In these two cases, one
required document never appeared in the returned evidence at all, crowded out by
unrelated documents that scored higher:

- **`KND-M5-CD-006`** — *"Which NIRC sections listed as amended in RMC No. 3-2024
  are also named as the implementation scope of RR No. 7-2024?"* Needs
  `RMC_03_2024_EOPT_Act.pdf` p.1 and `RR_07_2024_Invoicing_Registration.pdf` p.1.
  Evidence returned: `RMC_03_2024_EOPT_Act.pdf` p.1 (correct) plus
  `RR_03_2024_VAT_Percentage_Tax.pdf`, `RMC_77_2024_Invoicing_QA_OCR.pdf`, and
  `RR17_2024_Procurement_Monitoring_Report.pdf`. **`RR_07_2024` never appears.**
- **`KND-M5-CD-009`** — *"How does RR No. 7-2024's registration scope relate to the
  concrete Annex A1 checklist for a self-employed applicant?"* Needs
  `RR_07_2024_Invoicing_Registration.pdf` p.1 and
  `Registration_Checklist_Annex_A1A3.pdf` p.1. Evidence returned: `RR_07_2024` p.1
  (correct) plus four other documents. **`Registration_Checklist_Annex_A1A3.pdf`
  never appears.**

### Unknown, with a partial retrieval gap noted (1 case)

- **`KND-M5-CD-010`** — *"What do RMC No. 3-2024 and RR No. 4-2024 say about
  withholding-tax provisions that were vetoed or repealed?"* Needs
  `RMC_03_2024_EOPT_Act.pdf` pp.1-2 and `RR_04_2024_Filing_Payment.pdf` p.1. Both
  documents appear in evidence with p.1 present for each, but `RMC_03_2024`'s p.2
  is missing. Because both required documents ARE represented (unlike the two cases
  above, where one was entirely absent), this doesn't meet the bar for "cross-document
  retrieval limit" as verified there — the model had at least partial coverage of
  both sides of the comparison and still declined. Tagged **unknown**, with this
  partial gap recorded as a plausible contributing factor rather than a confirmed
  cause.

### Unknown, with a narrow single-document page miss (1 case)

- **`KND-M5-LT-003`** — *"Which final three NIRC sections on RMC No. 3-2024's
  amended-section list appear on page 2...?"* Needs `RMC_03_2024_EOPT_Act.pdf` p.2
  specifically. Evidence returned only p.1 of that document. Checked directly
  against Postgres: p.2 has 2 chunks in the table (not zero, not duplicated away —
  `SELECT ... GROUP BY page_number` returns p.1: 3 chunks, p.2: 2 chunks, a normal
  distribution). So the chunks exist and are not the page-1-duplication artifact;
  they simply didn't score high enough against this question's embedding to enter
  the top 8. This is a real, narrow retrieval-recall gap, but it is single-document
  (no second document to be "crowded out" by), so it doesn't meet the bar for
  "cross-document retrieval limit" either. Tagged **unknown** rather than force-fit
  into a category the evidence doesn't support.

### Page-duplication finding: checked, does not reproduce here

`CLAUDE.md` documents RMC 03-2024's page-1 duplication as "not root-caused" but
also states it "no longer affects retention, since Docling no longer retains"
under ADR-007. Queried directly:

```
RMC_03_2024_EOPT_Act.pdf  page 1 → 3 chunks
RMC_03_2024_EOPT_Act.pdf  page 2 → 2 chunks
```

No skew. The historical finding was about a Docling-based measurement that no
longer governs retention; it does not describe this corpus's current chunk table.
None of the false negatives above are attributable to it, including the ones
touching RMC 03-2024.

### OCR gap: checked, does not reproduce here

Four of the 13 false negatives touch the 12-page OCR-only circular
(`RMC_77_2024_Invoicing_QA_OCR.pdf`, `ocr_required: true`):
`KND-M5-CD-004`, `KND-M5-CD-005`, `KND-M5-DF-017`, `KND-M5-DF-020`. In every one of
these four, the retriever successfully returned that document at a page matching
`expected_pages`. SF-01 (`CLAUDE.md`'s open OCR-containment gap, proposed to close
under ADR-008) remains real and separately documented, but it did not cause any of
these four misses — the OCR text embedded and retrieved correctly here. Tagging any
of these "OCR gap" would have been the same unverified pattern-match error called
out at the top of this document.

### Unknown — retrieval succeeded, the model still declined (9 cases)

For all nine of these, the retriever returned the correct document(s) at a page
matching `expected_pages`, with no missing authoritative document. Generation still
returned `insufficient_evidence`. This is not explained by retrieval; the cause is
somewhere in the prompt-construction or generation path, which is out of scope for
this document (no answering-behavior change is being made here) and worth a
targeted look when M10 itself is next worked on.

| case_id | category | authoritative doc(s) retrieved at the right page | note |
|---|---|---|---|
| `KND-M5-CD-004` | cross_document_comparison | both (RR 11-2024 p.1,3; RMC 77-2024 p.9,11) | full evidence present |
| `KND-M5-CD-005` | cross_document_comparison | both (RR 11-2024 p.1-3; RMC 77-2024 p.5,10,11) | full evidence present |
| `KND-M5-DF-005` | direct_factual | RR 11-2024 p.1-2 | full evidence, top score 0.77 |
| `KND-M5-DF-008` | direct_factual | RMC 03-2024 p.1 | only 2 evidence items total, but the right one, scored 0.59 |
| `KND-M5-DF-009` | direct_factual | RMC 03-2024 p.1-2 (needed p.2, present) | full evidence present |
| `KND-M5-DF-012` | direct_factual | RR17-2024 p.15 (among 6 pages, all correct doc) | full evidence, single-doc |
| `KND-M5-DF-017` | direct_factual | RMC 77-2024 (OCR) p.1,2,5,6,11 | full evidence present |
| `KND-M5-DF-020` | direct_factual | RMC 77-2024 (OCR) p.1,11 | full evidence present |
| `KND-M5-LT-007` | list_or_table | RR17-2024 p.16 (among 6 pages, all correct doc) | full evidence, single-doc |

`KND-M5-CD-010` and `KND-M5-LT-003` (above) are also tagged **unknown** — for two
distinct, narrower reasons than the nine above (a partial cross-document gap, and a
single-document page miss, respectively) — kept in their own subsections rather
than merged into this list so the three different flavors of "unknown" aren't
conflated with each other.

### Summary by tag (every false negative gets exactly one of the four requested tags)

| Tag | Count | Cases |
|---|---:|---|
| OCR gap | 0 | — (checked; not reproduced — see below) |
| Page duplication | 0 | — (checked; not reproduced in current corpus — see below) |
| Cross-document retrieval limit (verified) | 2 | CD-006, CD-009 |
| Unknown | 11 | CD-004, CD-005, CD-010, DF-005, DF-008, DF-009, DF-012, DF-017, DF-020, LT-003, LT-007 |

## (c) Atomic-fact recall is unscored

The run's atomic-fact recall figure (0.32, `apps/api/src/kendra_api/evaluation/scoring.py`'s
`normalized_substring_or_token_overlap>=0.8` matcher) is a mechanical, provisional
approximation, explicitly labeled as such in every `report.json`/`report.md` this
milestone produces. It is **not** a scored result and must not be read as one:
per `docs/EVALUATION_METHOD.md`, atomic-fact and citation correctness require
judging meaning, not string overlap, and this project's own rule is not to treat
mechanical/parser success as proof of correctness or completeness. The 85 mechanical
false negatives behind that 0.32 include, at minimum, correct answers phrased
differently than the gold fact string (the scorer's known, documented limitation —
see `CLAUDE.md`'s open items on the fact scorer's weak join-match rule). This number
is superseded only by a human review of `scoring_worksheet.json` supplied back via
`--scored-worksheet` (`apps/api/src/kendra_api/evaluation/run.py`); until that
happens, it stays unscored, and `acceptance_claim` stays `false` on every report
regardless of what the provisional number says.
