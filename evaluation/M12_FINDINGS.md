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

## (d) The 11 "unknown" cases: was the fact actually in the context given to the model?

**How this was checked.** For each of the 11 cases tagged "unknown" in part (b),
the real `QdrantRetriever` was invoked again (same `top_k=8`, `score_threshold=0.5`,
read-only, generation bypassed) and the *full chunk text* of every returned
evidence item was read — not just its document and page number, which is all part
(b) checked. Each gold `expected_answer_facts` string was then checked against that
concatenated text for its key strings: **present** (the fact's substance, including
its specific figures/names, appears, allowing minor paraphrase or OCR noise),
**partially present** (some required detail is there but a specific value is cut
off or missing), or **absent** (not in the retrieved text at all, even though the
correct document and/or page nominally appears per part (b)'s coarser check).

**This corrects two cases from part (b).** Part (b) checked document+page presence
only and counted `KND-M5-DF-012` and `KND-M5-LT-007` among the nine "full evidence
present" unknowns. Reading the actual chunk text shows neither one actually
contains the required data: both target `RR17_2024_Procurement_Monitoring_Report.pdf`,
whose page 1 alone is split into **30 separate chunks** (checked directly against
the `chunks` table — most pages in this corpus are 2-3 chunks; this one page has
30, driven by how wide, sparse table rows extract to text). With only 8 evidence
slots shared across the entire corpus, a single specific project's row on that page
has to out-score 29 sibling chunks from the same page just to be included, and for
both of these cases it didn't. The specific data-bearing chunk was confirmed to
exist in the ingested corpus by querying it directly, and to be plausible for the
question's evidence gate: full retrieval score-threshold detail is in part (b);
this is a chunk-density problem layered on top, specific to this one wide-format
document. Reclassified below as **facts not in context**, not "unknown, retrieval
succeeded."

### Facts in context, model abstained anyway (7 cases)

| case_id | fact | status | evidence (short) |
|---|---|---|---|
| `KND-M5-CD-004` | adjustment/enhancement deadline ≤ Dec 31, 2024 (both docs) | present | RR 11-2024: "adjustments shall be undertaken on or before December 31, 2024"; RMC 77-2024: "before December 31, 2024 stating the reason ... for the request for extension" |
| | extension ≤ six months from Dec 31, 2024 (both docs) | **partially present** | RR 11-2024: "shall not be longer than six (6) months from December 31, 2024" (full). RMC 77-2024's retrieved chunk starts mid-word: "...onths from December 31, 2024" — a chunk-boundary artifact cut off the word "six" itself, even though the same figure is stated in the OCR'd source |
| | approval by Regional Director / Asst. Commissioner LTS (both docs) | present | RR 11-2024 and RMC 77-2024 both contain "approved by the concerned Regional Director or Assistant Commissioner of the Large Taxpayers Service" near-verbatim |
| `KND-M5-CD-005` | fine PhP 1,000–50,000 (both docs) | present | RR 11-2024 and RMC 77-2024 both contain "not less than One Thousand Pesos (Php 1,000.00) but not more than Fifty Thousand Pesos (Php 50,000.00)" verbatim |
| | imprisonment 2–4 years (both docs) | present | both contain "not less than two (2) years but not more than four (4) years" verbatim |
| | cites Section 264(a) (both docs) | present | both contain "Section 264(a) of the Tax Code" verbatim |
| `KND-M5-DF-005` | no COR replacement required for displayed Registration Fee | present | "not required to replace its existing BIR Certificate of Registration that displays the Registration Fee" — verbatim |
| | existing COR remains valid | present | "The COR shall retain its validity although the Registration Fee is shown therein" — verbatim |
| | updating needed only for non-fee changes | present | "Updating the COR is only necessary if there are changes to the registration information, excluding Registration Fee" — verbatim |
| `KND-M5-DF-008` | RMC 3-2024 issued January 10, 2024 | present | "issued on January 10, 2024" — verbatim |
| | RA 11976 + Veto Message signed January 5, 2024 | present | "both signed by President Ferdinand R. Marcos Jr. on January 5, 2024" — verbatim |
| `KND-M5-DF-009` | 90 calendar days from effectivity for IRR | present | "Within ninety (90) calendar days from the effectivity of the Act ... shall promulgate the necessary rules and regulations" — verbatim, on the retrieved RMC 03-2024 p.2 chunk |
| `KND-M5-DF-017` | business style not required on invoice | present | "Business Style of the buyer or seller is not required to be indicated in the Invoice" — verbatim |
| | seller may indicate business name for branding | present | "the seller may indicate its business name in the Invoice for trade name or store name identification or branding purposes" — verbatim |
| `KND-M5-DF-020` | effective April 27, 2024 | present | "effective on April 27, 2024" — verbatim |
| | 15 days from April 12, 2024 publication | present | "fifteen (15) days from the date of publication on the BIR official website on April 12, 2024" — verbatim |

All seven have every required fact's key strings sitting in the context handed to
the model, several verbatim or near-verbatim to the gold fact string itself. These
are the strongest evidence in this whole review that the failure is downstream of
retrieval — in prompt construction or generation — not a content-availability
problem.

### Facts not in context (4 cases, one corrected from part (b))

| case_id | fact | status | why |
|---|---|---|---|
| `KND-M5-CD-010` | micro-enterprise withholding exemption vetoed (RMC 3-2024) | absent | Not on the retrieved RMC 03-2024 p.1 chunk (a general summary). The sentence exists verbatim on p.2 — confirmed because `KND-M5-DF-009`'s retrieval (a differently-phrased question) independently pulled that exact p.2 chunk — but p.2 wasn't retrieved for *this* question's phrasing |
| | RR 4-2024 §2.58.5 repeal on EOPT effectivity | absent | Retrieved RR 04-2024 p.1 chunk is only its opening summary paragraph; no mention of Section 2.58.5 |
| | RR 4-2024: withholding obligation remains | absent | Same chunk; not present |
| `KND-M5-DF-012` | total ABC PhP 2,730,755.00 (project 2024-001) | **absent** (corrects part (b)) | Confirmed present in the corpus at chunk `e2cd7fd1-...` (page 1, one of 30 page-1 chunks) but not among the 8 retrieved |
| | total contract cost PhP 2,622,648.24 | **absent** (corrects part (b)) | Same chunk as above; not retrieved |
| `KND-M5-LT-003` | Sections 245, 248, 269 (NIRC amended-list, p.2) | absent | Retrieved RMC 03-2024 chunk is p.1 only; p.2 (where this list continues) was not retrieved at all |
| | Section 34(K) repealed | absent | Same — not on the retrieved p.1 chunk |
| `KND-M5-LT-007` | 2024-001 / 2024-002 / 2024-005 rows (project, PMO, ABC, contract cost) | **absent** (corrects part (b)) | Retrieved evidence contains *other* projects (2024-056, 2024-200, 2024-253) and aggregate totals from the same wide table, but none of the three requested rows |

### Split

| | Count | Cases |
|---|---:|---|
| Facts in context, model abstained anyway | 7 | CD-004, CD-005, DF-005, DF-008, DF-009, DF-017, DF-020 |
| Facts not in context | 4 | CD-010, DF-012, LT-003, LT-007 |

Combined with part (b)'s verified cross-document retrieval limit (`KND-M5-CD-006`,
`KND-M5-CD-009` — distinct from `KND-M5-CD-010`, which is in this section's
facts-not-in-context group, not that one), the full 13 false negatives split as:
**6 with a genuine content-availability gap** (2 cross-document-limit + 4
facts-not-in-context) **and 7 where the model had what it needed and declined
anyway** (2 + 4 + 7 = 13). The generation-side question raised in part (b) narrows
accordingly: it applies specifically to `KND-M5-CD-004`, `KND-M5-CD-005`,
`KND-M5-DF-005`, `KND-M5-DF-008`, `KND-M5-DF-009`, `KND-M5-DF-017`, and
`KND-M5-DF-020` — not to the full 11-case "unknown" set part (b) originally
grouped together, four of which turn out to have a content-availability
explanation after this section's deeper check.

## (e) Retrieval architecture: a shared top-k merge has no per-document floor

Both content-availability gaps documented in this review — the cross-document
retrieval limit (part (b): `KND-M5-CD-006`, `KND-M5-CD-009`) and the wide-table
chunk-density miss (part (d): `KND-M5-DF-012`, `KND-M5-LT-007`) — trace to the
same underlying mechanism, not two unrelated bugs.

`QdrantRetriever.retrieve()` (`apps/api/src/kendra_api/answering/retrieval.py`)
queries every active document's Qdrant collection, merges every returned
candidate into one list by raw score, and truncates **once**, globally, to
`top_k=8`. Nothing in that merge guarantees any particular document — let alone
every document a cross-document case needs — keeps even one slot:

- **Cross-document case:** a required second document's chunks simply score
  lower than chunks from unrelated documents and lose every slot in the shared
  window (`KND-M5-CD-006`, `KND-M5-CD-009` — confirmed by direct retrieval
  replay, part (b)).
- **Wide-table document:** one page of `RR17_2024_Procurement_Monitoring_Report.pdf`
  alone splits into 30 chunks (confirmed directly against the `chunks` table,
  part (d)) — a specific data-bearing chunk has to outscore 29 same-page,
  same-document siblings, *in addition to* every other document's chunks, just
  to be considered.

Both are instances of one architectural property: the merge has no floor. A
document, or a specific row within one document's page, can be real, correctly
embedded, and directly relevant, and still lose every slot to volume from
elsewhere in the corpus.

**Proposed, not implemented:**

1. **A per-document quota in the top-k merge.** Reserve a minimum number of
   slots (e.g., at least one, possibly scaled by how many documents a request's
   scope spans) across the documents represented in the candidate pool before
   filling remaining slots by best score. This targets the cross-document gap
   directly — it would guarantee `KND-M5-CD-006`'s and `KND-M5-CD-009`'s missing
   second document at least a chance to be represented, rather than losing
   outright to volume from unrelated documents.
2. **Table-aware chunking that keeps rows with headers.** The current chunker
   (`KENDRA_CHUNK_SIZE_CHARS=1200`, `KENDRA_CHUNK_OVERLAP_CHARS=200`) splits
   extracted text purely by character count, which is what drives one table
   page to 30 chunks. A table-aware strategy that detects tabular structure and
   keeps each data row bundled with enough header/label context to be
   self-contained and independently discoverable would reduce the
   chunk-count-per-page explosion this finding measured directly.

**Any chunking change requires re-ingest and a new corpus baseline under
ADR-007 — stated explicitly so it isn't treated as a small fix.** The
currently-ingested corpus, hash-verified and referenced throughout every M12
report and this document, would no longer match a changed chunker's output. A
new pipeline identity and a fresh ingestion pass would be required, and every
finding recorded in this document against the current baseline
(`0bcc9dd7d0aaf7bd370e8d3eb60303a42e8ef91c`) would need to be read as historical
against that baseline, not silently re-validated against a new one. This
parallels how EXP-03 (`docs/EXPERIMENT_PLAN.md` Section 5) originally set the
current 1200/200 chunking policy — a change here is the same class of decision
and needs its own preregistration, not an ad hoc edit. Neither proposal above is
implemented, scheduled, or preregistered by this document.

## (f) EXP-11 Stage 0 pre-Stage-1 truncation check (read-only)

**Full report:** `evaluation/runs/EXP-11/20260901T014805Z-0bcc9dd7/truncation_check.md`
(also copied to `~/Downloads/reports/` per the requester's instruction; both
are outside git per the existing `/evaluation/runs/` ignore rule, same as
`stage0_cases.jsonl`/`stage0_summary.md` in that same run directory). This
section is a summary; the full report has the per-case reconstruction, exact
commands, and full quoted evidence.

**Why this check was run:** before EXP-11 Stage 1 (the `B0` vs `B1_LARGER`
model comparison, gated on Stage 0's 6 `model-abstained` cases per
`stage0_summary.md`), confirm that none of Stage 0's classifications were an
artifact of Ollama silently truncating an oversized prompt rather than a
genuine model decision to abstain.

**`model_client.py`'s only decoding option is `temperature: 0`** — no `num_ctx`,
`num_predict`, or `seed` is set anywhere in this codebase (confirmed by grep).
**The effective serving context on `kendra-ollama-1` is 4096 tokens** — not
`qwen2.5:7b-instruct`'s trained 32768 — because `OLLAMA_CONTEXT_LENGTH` is
unset on the container and nothing in this deployment ever passes `num_ctx`;
confirmed directly via `ollama ps` immediately after a live call (`CONTEXT
4096`), not inferred from the model's own advertised context length.

**Per-case token counts, measured exactly (not estimated)** by replaying each
of the 7 candidate cases' evidence retrieval live (real `QdrantRetriever`,
`top_k=8`, `score_threshold=0.5`, same corpus/source revision as Stage 0 and
this document's part (d)), building the identical prompt `model_client.py`
builds, and reading Ollama's own `prompt_eval_count` for it (this build of
Ollama, 0.32.0, has no `/api/tokenize` endpoint):

| case_id | evidence items | prompt tokens | of 4096-token window |
|---|---:|---:|---:|
| `KND-M5-CD-004` | 8 | 2,802 | 68% |
| `KND-M5-CD-005` | 8 | 2,810 | 69% |
| `KND-M5-DF-005` | 8 | 2,701 | 66% |
| `KND-M5-DF-008` | 2 | 1,012 | 25% |
| `KND-M5-DF-009` | 8 | 2,736 | 67% |
| `KND-M5-DF-017` | 8 | 2,920 | 71% |
| `KND-M5-DF-020` | 8 | 2,835 | 69% |

**Truncation is not confirmed.** Every case sits well under the 4096-token
window, with headroom to spare for the (short, 40–90 token) response — the
worst case (`KND-M5-DF-017`) uses 71% of the window. This is a negative result
specific to these 7 cases as retrieved today; it does not clear the 4096-vs-32768
gap itself, which remains a live, undocumented configuration risk independent
of whether it happened to bite here (a larger `top_k` or longer chunks in a
future case could still cross it).

**`docker logs kendra-ollama-1` search for "truncat" is inconclusive, not a
clean negative.** The one hit in the entire log (`truncated = 0`, dated
2026-08-26) predates both the M12 clean run window (`20260831T125331Z`) and
the Stage 0 run window (`20260901T014805Z`) by days. Neither window has *any*
log coverage — 0 lines in either `--since`/`--until` range — and the gap is
current, not just historical: live calls made during this same check produced
zero new log lines despite `kendra-ollama-1` responding normally. This channel
cannot corroborate or refute truncation for either run; the token-count
reconstruction above is the only evidence this check relies on.

**A protocol deviation was found and is recorded in
`docs/EXPERIMENT_REGISTRY.md`'s `EXP-11` row and in the run directory's
`truncation_check.md` (Section 5):** `EXP-11-preregistration.md` Section 4's
frozen mechanism requires Stage 0 to use a static, pinned evidence packet
seeded from this document's own part (d) diagnostic, explicitly "no live
Qdrant query, no live embedding call." `stage0_summary.md` (line 5) instead
describes evidence "freshly re-fetched via the real `QdrantRetriever`" — a live
retrieval call, not the frozen packet the preregistration specifies. Compounding
this, no machine-readable record of part (d)'s own captured chunk IDs was ever
persisted anywhere (this document records prose excerpts and a document/page
table only), so the "same chunk IDs, same order" check this exercise called for
cannot be performed against any artifact — for either part (d) or Stage 0. Page-
and document-level results are consistent across all three independent
retrievals (part (d)'s original diagnostic, Stage 0's re-fetch, and this
check's own replay) for the cases spot-checked, but that is not the same claim
as chunk-identical replay.

**Bottom line:** truncation is not confirmed, so no truncation-driven
amendment is drafted here (per this task's own conditional). The protocol
deviation above does not concern token-window truncation and is recorded, not
remediated, here — it is a separate methodological gap for whoever reviews
Stage 0 before relying on it to gate Stage 1.

## (g) The six EXP-11 abstentions were correct behavior given the rendered input

**How this was checked.** A read-only inspection (reported as "v8 item-4" in
this project's session records; also `docs/experiment-decisions/EXP-13-preregistration.md`
§0) printed `render_evidence()`'s (`apps/api/src/kendra_api/answering/model_client.py`)
exact output for `KND-M5-CD-004`'s persisted evidence packet
(`evaluation/runs/EXP-11/packets/KND-M5-CD-004.json`) and then checked all 8
of that packet's evidence items, not just the three inspected verbatim.

**Finding, stated exactly as checked:**

1. `render_evidence()` emits, for every evidence item, exactly
   `<evidence id="ev-N">{text}</evidence>` — no document name, title, page,
   checksum, or path of any kind. This is the deployment's current and only
   rendering as of this document; confirmed directly from the function's
   real output, not from its docstring's own claim.
2. The `RMC No. 77-2024` chunks in `KND-M5-CD-004`'s packet (evidence items
   at `order` 3, 4, 5 — the ones needed to establish anything about that
   document) **never name their own document anywhere in their body text.**
   Neither "RMC" nor "77-2024" appears in any of the packet's 8 items,
   including the `RR No. 11-2024` chunks. The only place the string
   "RMC No. 77-2024" appears anywhere in the constructed prompt is the
   question itself.

**Conclusion.** Given points 1 and 2 together, the model has no way —
structural (the rendering) or textual (the chunk content) — to determine
which evidence item, if any, came from a document named "RMC No. 77-2024."
`SYSTEM_INSTRUCTION`'s own rule is "Never answer from prior knowledge. If the
evidence does not establish the answer, return status
insufficient_evidence" — and evidence that cannot even be attributed to the
named document a question asks about does not establish an answer *about that
document*, regardless of whether the right facts happen to be sitting
somewhere in the undifferentiated block of quoted text. **The six EXP-11
candidate cases' original abstentions (`KND-M5-CD-004`, `KND-M5-CD-005`,
`KND-M5-DF-005`, `KND-M5-DF-008`, `KND-M5-DF-009`, `KND-M5-DF-020`, all under
`B0_BASELINE` in Stage 0) were therefore correct, safe behavior given the
input the model actually received — not an unexplained defect.** Parts (b),
(d), and (f) of this document characterized these as a puzzle ("the model had
what it needed and declined anyway"); this section resolves that puzzle: the
model did not have what it needed to attribute the facts to the named
documents the questions asked about, only to *some* document.

**A supporting asymmetry, observed and not further pursued here:** EXP-11
Stage 1 found `B1_LARGER` (`qwen2.5:14b-instruct`) willing to answer 4 of the
6 cases anyway (2 fact-complete, 2 fact-incomplete — `stage1_summary.md`),
but it still abstained, like `B0_BASELINE`, on both cross-document comparison
cases (`KND-M5-CD-004`, `KND-M5-CD-005`) — the two where correctly answering
*requires* attributing separate facts to two differently-named documents at
once, which is exactly the attribution this section shows is structurally
unavailable. The single-document cases (`DF-*`) only require the model to
assume the evidence it was given matches the one document named in the
question, a weaker and evidently sometimes-crossed bar; the cross-document
cases cannot be crossed the same way. This is consistent with, not
independent confirmation of, this section's finding — recorded as an
observation rather than a separately checked result.

**What this does not establish:** that labeling evidence with its document
name would fix these abstentions, or that doing so is safe (a labeled
rendering creates its own risk — a claim echoing a filename/page it was never
supposed to see — see `EXP-13-preregistration.md` Section 7's label-leak
check). That is `EXP-13`'s own, separate, frozen question; this section
establishes only the diagnostic finding that motivated it.
