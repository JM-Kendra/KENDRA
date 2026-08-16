# Kendra Architecture Experiment Plan

**Status:** Planned; no experiment result is claimed
**Planning milestone:** Milestone 7a
**Execution milestones:** Milestones 9–11
**Last updated:** 2026-08-16

## 1. Purpose and gate

This document preregisters the time-boxed spike plans and pass/fail criteria for EXP-01 through EXP-06 in [ARCHITECTURE.md](ARCHITECTURE.md). It satisfies the planning prerequisite for Milestone 8 scaffolding. It does not authorize ingestion or question-answering work in this milestone, and it does not establish that any experiment has run or passed.

The accepted architecture, trust boundaries, component families, source authority rules, and frozen [MVP specification](MVP_SPEC.md) remain unchanged. Assigned implementation milestones cannot pass until their experiments pass. A failed or inconclusive experiment fails closed as described below.

## 2. Controls common to every experiment

### Approved corpus and evaluation inputs

The only source corpus is the ignored, locally held BIR sample approved by its `APPROVAL_MANIFEST.json`. Before an experiment uses source content, the runner must verify the approval status and scope and require the following exact entries from [`evaluation/gold_cases.json`](../evaluation/gold_cases.json):

| Filename | SHA-256 | Physical pages | Format stratum |
|---|---|---:|---|
| `RR_02_2024_Publication.pdf` | `e578c3069f8b6ec8f302eec7001dd3b233558743746b2184a4ad4c6fadd58816` | 1 | Digital text |
| `RR_03_2024_VAT_Percentage_Tax.pdf` | `55462106e17a7fe2db14569d2d4aabd1015cf800bf0a60f26cba34ab55cddfbb` | 1 | Digital text |
| `RR_04_2024_Filing_Payment.pdf` | `1311cc3abdd51ad9a9793a51616eb43d5cf4815f4f45ecc5b758832448fc803a` | 1 | Digital text |
| `RR_07_2024_Invoicing_Registration.pdf` | `f6656606754483e5814f064f145ac467f8fc856bfd51fcd92a2969aef8047b32` | 1 | Digital text |
| `RR_11_2024_Invoicing_Amendments.pdf` | `47c9466a33558bb291533e5597139a35006f4d7abf3cadb6a56555fbb25c9fba` | 3 | Digital text |
| `RMC_03_2024_EOPT_Act.pdf` | `a26b7ebc3244900dd900c2de8c8962d806707cb31f2bd3b0c61e07745f0ef0c5` | 2 | Digital text |
| `RMC_77_2024_Invoicing_QA_OCR.pdf` | `48f53fa97ea817a364b3ad192678de93eab8db6048e3793c672df902e52c1a3e` | 12 | Scanned image with no text layer |
| `RR17_2024_Procurement_Monitoring_Report.pdf` | `d11e83cbcc2116a072d82389ab6007d735d5b7aea09e2b3ea8c9a890277243d0` | 16 | Digital, table-heavy |
| `Registration_Checklist_Annex_A1A3.pdf` | `748faae03cf3141448c0a1a4f00b64afec3705d1e33ee483f2933c096066ff1a` | 4 | Digital, form layout |

These entries total nine documents and 41 one-based physical pages. The evaluation file contains 50 cases: 20 direct factual, 10 list/table, 10 cross-document comparison, and 10 deliberately unsupported; 14 cases are marked `ocr_required`.

### Preregistration and isolation

Before each run, commit or otherwise freeze a reviewed experiment registration that names the source-manifest checksum, dataset Git revision, candidate configurations, tool/model identities, hardware, operating mode, seed, timeouts, and scoring code revision. Candidate values cannot be added, removed, or tuned after expected results are examined. A changed candidate set is a new preregistered run, and previous failures remain reported.

Expected facts, expected pages, unacceptable behaviors, and ambiguity notes may be used only by the evaluation harness and human adjudicators after runtime output is captured. They must never enter extraction, chunking, retrieval, prompting, generation, or the runtime request path.

Every run uses the same checksum-verified corpus, dataset revision, source version, fixed random seed where applicable, hardware allocation, concurrency of one, and cache-state definition except for the controlled variable named by the experiment. Network state and all dependency versions are recorded.

### Evidence ownership

Generated reports, predictions, traces, extracted text, OCR output, chunks, embeddings, vector indexes, screenshots, timing files, model output, hardware captures, and reviewer worksheets are derived data. Store them outside Git under the ignored path:

```text
evaluation/runs/<experiment-id>/<run-id>/
```

The run directory must contain a manifest linking the evidence to source checksums, the dataset and application Git revisions, frozen configuration identities, and tool/model versions. Only plans, frozen non-secret configurations, automated tests, evaluation cases, and final reviewed decision records may be committed. Final decision records belong under `docs/experiment-decisions/` when the assigned milestone runs; that directory is not created by this planning milestone.

### Fixed decision rule

Pass criteria are conjunctive: every listed condition must pass. Any fail criterion, missing required observation, source-integrity failure, incomplete run, unadjudicated material ambiguity, or inability to reproduce the result makes the outcome `failed` or `inconclusive`, never `passed`. Criteria and thresholds must not be weakened after results are seen. Changing a criterion requires a reviewed architecture or specification change and a new preregistered run; it does not convert an earlier failure into a pass.

## 3. EXP-01 — Page extraction and OCR

### Question and decision

- **Experiment ID and question:** EXP-01 — Can Docling with page-level Tesseract fallback preserve exact physical-page identity and the table/form context required by the approved cases?
- **Decision produced:** Freeze the Docling quality gate, Tesseract trigger and configuration, page-state model, page/region representation, and supported document classes. Identify any document class that must remain unpublished.

### Prerequisites and exact inputs

- **Prerequisite milestones and data:** Milestones 1–8 complete; Milestone 9 ingestion, checksum verification, page-record, Docling, and Tesseract spike capability available; expert-reviewed source approval remains valid.
- **Exact approved inputs:** All nine checksum-matched PDFs and all 41 physical pages in Section 2; the approved manifest; the 50-case dataset for expected-page and fact review; the digital-text, scanned-image, table-heavy, and form-layout strata. The 12-page `RMC_77_2024_Invoicing_QA_OCR.pdf` is the mandatory all-page OCR case.

### Variables and procedure

- **Controlled variables:** Source bytes, page-count library, Docling version/configuration, Tesseract engine and language-data versions, rendering resolution, CPU/memory limits, timeouts, hardware, page numbering, and reviewer rubric remain fixed. Only the preregistered extraction-quality gate and its declared Tesseract branch candidates vary.
- **Procedure:**
  1. Verify approval scope, filenames, all nine SHA-256 values, readability, encryption state, and page counts before processing.
  2. Run each preregistered Docling quality-gate candidate over every page and record one explicit state per physical page.
  3. Invoke Tesseract only when the candidate gate returns `ocr_required`; require all 12 pages of the scanned circular to take that branch.
  4. Reconcile page records to the exact contiguous sequence `1..page_count` for every source.
  5. Compare extracted/OCR evidence with expected physical pages and have reviewers inspect every material expected fact plus representative tables, forms, and layouts against the rendered originals.
  6. Repeat the selected candidate once with identical inputs to confirm the same page identities, methods, and states.

### Metrics and gates

- **Metrics collected:** Checksum and page-count precondition results; page records attempted/completed/failed; missing and duplicate page counts; extraction method/state by page; OCR trigger precision against the frozen rule; expected-page mapping rate; material fact-alteration count; table/form interpretability findings; timeouts; peak memory; and elapsed time.
- **Pass criteria:** All nine checksums match; exactly 41 contiguous physical-page records exist; zero pages are omitted or duplicated; all 12 scanned-circular pages trigger OCR; every nonblank page has an explicit usable or failed state; expected-page mapping is 100%; extraction/OCR changes zero material expected facts; and table/form context needed by the gold cases remains interpretable.
- **Fail criteria:** Any checksum or page-count mismatch; any missing, duplicate, or silently empty page; any scanned-circular page that does not trigger OCR; any nonblank page without an explicit usable/failed state; expected-page mapping below 100%; one material fact changed; or required table/form context made uninterpretable.
- **Time box:** One working day after ingestion capability exists. Setup failures caused by missing approved inputs stop the clock and produce an inconclusive source-precondition result, not a pass.

### Evidence, artifact, schedule, and failure behavior

- **Generated evidence and output location:** Run manifest, page inventory, method/state map, quality measurements, rendered-page review worksheet, discrepancies, timings, and resource data under `evaluation/runs/EXP-01/<run-id>/`.
- **Configuration or decision artifact produced:** A reviewed `docs/experiment-decisions/EXP-01.md` plus the versioned extraction/OCR configuration named by that record.
- **Execution milestone:** Milestone 9, before publishing any affected document class.
- **Failed or inconclusive behavior:** Do not publish the affected document class. Preserve the failure evidence, revise the preregistered extraction design or narrow the supported class through reviewed change control, and rerun. Never label unusable extraction as blank or relax fact/page criteria after review.

## 4. EXP-02 — BGE-M3 retrieval configuration

### Question and decision

- **Experiment ID and question:** EXP-02 — Which bounded BGE-M3 retrieval configuration retrieves every adjudicated supporting page without falsely supporting an unsupported case?
- **Decision produced:** Freeze dense-only or dense-plus-sparse Qdrant fusion, the compatible chunk configuration, `top_k`, fusion parameters, candidate-support threshold, payload checks, and active-generation retrieval rule.

### Prerequisites and exact inputs

- **Prerequisite milestones and data:** Milestone 9 complete with EXP-01 and EXP-03 passed for all published document classes; Milestone 10 retrieval-only capability available; checksum-resolved sources, page records, chunks, embeddings, registry pointers, and one isolated staging generation available; gold-set adjudication state recorded.
- **Exact approved inputs:** All 50 stable case questions from the versioned dataset, comprising 40 supported and 10 unsupported cases, over only the nine approved sources. Expected pages and answers remain evaluation-side only. No generation/model output is allowed.

### Variables and procedure

- **Controlled variables:** Source/chunk records, pinned BGE-M3 artifact and runtime, vector dimensions, Qdrant version, dataset order/seed, hardware, concurrency, and network state remain fixed. The preregistered candidate matrix varies only retrieval form, a small declared set of chunk size/positive-overlap policies passed by EXP-03, `top_k` values no greater than 12, fusion parameters, and candidate thresholds. The exact matrix must be frozen before scoring.
- **Procedure:**
  1. Verify every chunk and point resolves through the same staging generation to an admitted version/checksum/page.
  2. Disable Ollama and all answer generation, then embed and retrieve each of the 50 questions once for every preregistered candidate.
  3. Capture the bounded candidate IDs, scores, ranks, source versions, physical pages, and generation identities before exposing gold labels to scoring.
  4. Score allowed-page recall by direct, list/table, comparison, OCR, non-OCR, and unsupported strata.
  5. Apply the candidate-support rule to unsupported cases and inject stale, orphaned, and cross-generation pointers to verify rejection.
  6. Select a configuration only when it satisfies every pass criterion; freeze it before any generation experiment.

### Metrics and gates

- **Metrics collected:** Allowed-page recall at each bounded `top_k`; case-level recall; rank of first supporting page; candidate counts; supported/unsupported confusion data for the support rule; false-supported count; stale/orphan/cross-generation rejection count; latency; and resource use, all segmented by required strata.
- **Pass criteria:** Every supported case retrieves an adjudicated supporting page within the bounded candidate set; the frozen support rule produces zero false-supported outcomes on all unsupported cases; no stale, orphaned, checksum-mismatched, inactive, or cross-generation result is accepted; one configuration is selected and frozen before generation evaluation; and evaluation answers/pages never enter the runtime request path.
- **Fail criteria:** One supported case lacks a supporting page in the bounded set; one unsupported case is classified as supported; one invalid generation/source pointer is accepted; `top_k` exceeds 12; no single preregistered configuration satisfies all criteria; or runtime code receives evaluation-only fields.
- **Time box:** One working day after retrieval-only capability exists.

### Evidence, artifact, schedule, and failure behavior

- **Generated evidence and output location:** Frozen candidate-matrix identity, query outputs, rank/recall tables, invalid-pointer injections, timings, resource measurements, and selection worksheet under `evaluation/runs/EXP-02/<run-id>/`.
- **Configuration or decision artifact produced:** A reviewed `docs/experiment-decisions/EXP-02.md` plus the versioned BGE-M3, chunk compatibility, Qdrant fusion, `top_k`, threshold, and support-rule configuration named by that record.
- **Execution milestone:** Milestone 10 before generation is enabled.
- **Failed or inconclusive behavior:** Do not enable generation and do not select a least-bad configuration. Record failure, revisit retrieval or chunking through reviewed architecture change control, preregister a new candidate matrix, and rerun without erasing prior results.

## 5. EXP-03 — Page-bounded chunking

### Question and decision

- **Experiment ID and question:** EXP-03 — Which deterministic, page-bounded chunking policy preserves complete evidence and the layout context required by the approved cases?
- **Decision produced:** Freeze chunk size, positive overlap, table/form handling, source offsets/regions, deterministic ID/checksum scheme, and maximum context policy.

### Prerequisites and exact inputs

- **Prerequisite milestones and data:** Milestones 1–8 complete; Milestone 9 page extraction spike available; checksum-resolved page records from the candidate EXP-01 pipeline available. Final selection requires EXP-01 to pass for the relevant document classes.
- **Exact approved inputs:** Usable page-scoped representations for all 41 approved physical pages, including every table-heavy and form-layout page, all 12 OCR pages, and every page referenced by direct, list/table, and cross-document supported cases.

### Variables and procedure

- **Controlled variables:** Source bytes/checksums, accepted page text and regions, tokenizer/version, normalization rules, table/form block representation, hardware, and ordering remain fixed. Only a small preregistered set of deterministic target sizes, positive overlaps, and layout-block retention policies varies; its exact values are frozen before any gold scoring.
- **Procedure:**
  1. Run each preregistered policy independently for every usable page; never concatenate physical pages.
  2. Validate page identity, text coverage, offsets/regions, sequence, overlap, unique IDs, and content checksums mechanically.
  3. Repeat each run with identical inputs and compare the complete ordered chunk IDs and checksums.
  4. Review the table, form, list, OCR, and cross-document strata against required source context without exposing expected answers to the chunker.
  5. Select a policy only if both mechanical and human interpretability gates pass.

### Metrics and gates

- **Metrics collected:** Cross-page chunk count; usable-text coverage; uncovered/duplicated offsets; overlap per adjacent pair; invalid-region count; unique-ID count; deterministic mismatch count; chunks/page and length distribution; and reviewer findings for headings, rows, labels, OCR context, and source attribution.
- **Pass criteria:** Zero chunks cross a physical-page boundary; usable page text has complete coverage; every multi-chunk page has positive overlap; all offsets/regions are valid; repeated runs produce identical ordered chunk IDs and checksums; and table headers, row meaning, form labels, OCR context, and cross-document attribution required by the gold cases remain interpretable.
- **Fail criteria:** Any cross-page chunk; any uncovered usable text; missing positive overlap on a split page; invalid or ambiguous offset/region; duplicate or nondeterministic identity; or loss of required table, form, OCR, or attribution context.
- **Time box:** Four hours after extraction capability exists.

### Evidence, artifact, schedule, and failure behavior

- **Generated evidence and output location:** Candidate configurations, chunk manifests, coverage/overlap reports, reproducibility diffs, distributions, and reviewer worksheet under `evaluation/runs/EXP-03/<run-id>/`.
- **Configuration or decision artifact produced:** A reviewed `docs/experiment-decisions/EXP-03.md` plus the versioned chunker configuration and identity algorithm named by that record.
- **Execution milestone:** Milestone 9, after usable page representations exist and before retrieval configuration is selected.
- **Failed or inconclusive behavior:** Select no chunk policy and do not begin EXP-02. Record the failure, revise and preregister the small policy set, then rerun. Do not accept incomplete coverage or weaken page/context invariants.

## 6. EXP-04 — Local Qwen model selection

### Question and decision

- **Experiment ID and question:** EXP-04 — Which of two pinned, workstation-suitable Ollama-compatible Qwen-family variants or quantizations can meet the structured grounded-answer and bounded latency contract locally?
- **Decision produced:** Freeze the exact model artifact and checksum, quantization, context size, Ollama version, prompt/schema identity, timeout, and concurrency.

### Prerequisites and exact inputs

- **Prerequisite milestones and data:** EXP-02 passed and its retrieval configuration frozen; Milestone 10 grounded-answering and server-side validator capability available; the target workstation hardware inventory recorded; model artifacts staged before timed runs; no cloud fallback configured.
- **Exact approved inputs:** Two explicitly pinned Ollama-compatible Qwen-family candidates chosen for the measured workstation and preregistered before evaluation; the same server-owned evidence packets for all 50 gold questions under the frozen retrieval configuration; the exact supported/unsupported response schema and prompt version. Gold fields remain evaluator-side only.

### Variables and procedure

- **Controlled variables:** Corpus, evidence packets, retrieval configuration, prompt/schema, Ollama version, context allocation, seed/decoding settings, concurrency of one, hardware allocation, timeouts, case order, and warm/cold definitions remain fixed. Only the pinned model/quantization candidate varies unless context size is explicitly preregistered as part of each candidate identity.
- **Procedure:**
  1. Record model manifests/checksums and exclude one-time download from the experiment time box and response latency.
  2. Run the same randomized, recorded case order for each candidate, preserving cold and warm runs separately.
  3. Validate structured output and evidence-ID membership before scoring or exposing prose.
  4. Score answer correctness, citation validity, unsupported behavior, timeouts, warm/cold latency, and memory pressure using the evaluation method.
  5. Inject an unknown evidence ID for each candidate and require server-side rejection.
  6. Select a candidate only if it passes every gate without destabilizing PostgreSQL, Qdrant, Ollama, the API, or the source store.

### Metrics and gates

- **Metrics collected:** Completed/failed/timed-out counts; structured-schema validity; strict supported-answer correctness; claim citation validity/completeness; unknown-ID acceptance; unsupported rejection and false-answer rates; warm p50/p90/p95/max and cold response time; peak host RAM, available/used GPU memory, service restarts, and out-of-memory events.
- **Pass criteria:** At least one candidate returns valid structured output for every completed response; accepts zero unknown evidence IDs; produces zero unsupported false answers; meets all frozen answer and citation requirements; has warm Quick-mode p95 response time at most 30 seconds and cold response time at most 120 seconds; and completes without exhausting host memory or destabilizing required services.
- **Fail criteria:** Both candidates fail any pass condition; one unknown evidence ID is accepted; one unsupported false answer is exposed; required answer/citation correctness is missed; warm p95 exceeds 30 seconds; cold response exceeds 120 seconds; or resource pressure destabilizes a required service. A timeout or incomplete required observation prevents a pass.
- **Time box:** One working day after grounded-answering capability exists, excluding one-time model download.

### Evidence, artifact, schedule, and failure behavior

- **Generated evidence and output location:** Model manifests, run outputs, schema/answer/citation scores, invalid-ID injections, latency distributions, and resource captures under `evaluation/runs/EXP-04/<run-id>/`.
- **Configuration or decision artifact produced:** A reviewed `docs/experiment-decisions/EXP-04.md` plus the pinned model, Ollama, prompt/schema, context, timeout, and concurrency configuration named by that record.
- **Execution milestone:** Milestone 10 after generation and validation capability exists and after EXP-02 passes.
- **Failed or inconclusive behavior:** Select no model and do not enable a user-visible generated-answer path. Preserve retrieval-only evidence as the safe fallback, record failure, and require a newly preregistered model or reviewed architecture change. Do not choose the least-bad candidate.

## 7. EXP-05 — Two-stage grounding and abstention gate

### Question and decision

- **Experiment ID and question:** EXP-05 — Does the API-enforced retrieval and answer gate reject unsupported, malformed, uncited, unknown-ID, and prompt-injected output without falling back to model memory or unvalidated prose?
- **Decision produced:** Freeze the structured response schema, evidence-membership and claim-citation validation rules, exact abstention behavior, error mapping, and fail-closed response policy.

### Prerequisites and exact inputs

- **Prerequisite milestones and data:** EXP-02 passed; Milestone 10 answer validator and bounded model adapter available; exact unsupported sentence and API-owned citation rules from the MVP specification implemented in the spike harness. EXP-04 may run in the same milestone, but EXP-05 evaluates the server gate independently of model quality.
- **Exact approved inputs:** All ten deliberately unsupported cases `KND-M5-UN-001` through `KND-M5-UN-010`; preregistered below-threshold retrieval packets; missing citations; unknown and synthetic evidence IDs; malformed status/claim/schema variants; uncited material claims; checksum/generation/source mismatches; and safe synthetic document-borne prompt-injection instructions. Synthetic fixtures contain no source PDF or restricted data and are reviewed before the run.

### Variables and procedure

- **Controlled variables:** Frozen retrieval rule, evidence set, response schema, exact unsupported sentence, validator version, error policy, prompt version, source/generation state, and network isolation remain fixed. Test mutations vary one declared invalid condition at a time, followed by selected combined-failure cases.
- **Procedure:**
  1. Run all ten unsupported cases through the complete two-stage gate.
  2. Feed each preregistered invalid response and evidence mutation directly to the validator so model cooperation cannot hide a missing control.
  3. Inject prompt text that requests role changes, secret access, external tools, alternative citations, or use of model memory.
  4. Capture the validator decision before any user-visible prose is returned.
  5. Confirm discarded output is not reused through cache, retry, logs, citations, or a fallback path.

### Metrics and gates

- **Metrics collected:** Unsupported rejection and false-answer rates; invalid cases attempted/rejected/accepted; unknown-ID rejection; uncited-claim rejection; malformed-output discard rate; exact-response match; prompt-injection rejection; cloud/network/tool invocations; and user-visible unvalidated-prose count.
- **Pass criteria:** Unsupported rejection is 100%; unsupported false-answer rate is 0%; every unknown evidence ID and uncited material claim is rejected; all malformed output is discarded; the exact response `Insufficient information in the uploaded documents.` is returned where applicable; and no fallback uses model memory, cloud AI, tools, or unvalidated prose.
- **Fail criteria:** Any invalid answer is accepted; any definitive unsupported answer or unvalidated prose becomes user-visible; any unknown ID or uncited material claim survives; any malformed output is reused; the required sentence differs where applicable; or any external/model-memory fallback occurs.
- **Time box:** Four hours after the answer validator exists.

### Evidence, artifact, schedule, and failure behavior

- **Generated evidence and output location:** Fixture manifest, validator decisions, rejection reasons, exact-response comparisons, prompt-injection cases, network/tool observations, and negative-test summary under `evaluation/runs/EXP-05/<run-id>/`.
- **Configuration or decision artifact produced:** A reviewed `docs/experiment-decisions/EXP-05.md` plus the versioned schema, validation policy, abstention/error mapping, prompt identity, and automated negative tests named by that record.
- **Execution milestone:** Milestone 10 after the answer validator exists.
- **Failed or inconclusive behavior:** Disable generated answers and expose no invalid prose. Record the failure, repair the server gate, add a regression fixture, and rerun the entire preregistered suite. Any single accepted invalid answer fails the experiment.

## 8. EXP-06 — Citation source resolution

### Question and decision

- **Experiment ID and question:** EXP-06 — Can every supported claim's server-owned citation resolve to the checksum-matched original, correct one-based physical page, and exact evidence excerpt in the viewer?
- **Decision produced:** Freeze the citation object fields, source-resolution checks, viewer URL/page contract, excerpt rule, optional region behavior, and OCR labeling/review behavior.

### Prerequisites and exact inputs

- **Prerequisite milestones and data:** EXP-01 through EXP-05 passed for the evaluated path; Milestone 11 evidence viewer and source streaming capability available; source repository mounted read-only at runtime; supported-case citations generated by the API from active registry records.
- **Exact approved inputs:** Every citation attached to every material claim produced for all 40 supported evaluation cases, the nine approved source versions/checksums, expected physical pages used only by the evaluation harness, exact stored page evidence, and rendered original PDFs. OCR-derived citations are explicitly identified.

### Variables and procedure

- **Controlled variables:** Source bytes/checksums, active generation, registry state, citation schema, server resolver, PDF renderer/viewer version, page-number convention, excerpt normalization rule, browser settings, and evaluator rubric remain fixed. Optional region highlighting is assessed only when the frozen citation object supplies a region.
- **Procedure:**
  1. Resolve each API-owned citation without accepting a caller-supplied filesystem path.
  2. Verify stable source identity and checksum before streaming any original bytes.
  3. Open the preserved PDF and navigate the viewer to the cited one-based physical page.
  4. Compare the excerpt with the exact contiguous stored page evidence and the adjacent material claim.
  5. Verify optional region highlighting when present.
  6. Manually compare every OCR-derived excerpt with the rendered original page and confirm the UI labels it as OCR-derived assistance.
  7. Inject unresolved, checksum-mismatched, wrong-page, and model-authored citation variants and require fail-closed rejection.

### Metrics and gates

- **Metrics collected:** Citations and material claims attempted; source resolvability; checksum/filename accuracy; correct physical-page rate; exact contiguous-excerpt rate; claim-level citation completeness and adjacency; optional-region accuracy when applicable; OCR label/manual-check completion; and invalid-citation rejection count.
- **Pass criteria:** Source resolvability is 100%; correct physical-page rate is 100%; filename and checksum accuracy are 100%; every excerpt is an exact contiguous substring of stored page evidence; every material claim has a valid adjacent citation; every OCR-derived excerpt is visibly identified and manually checked against the rendered page; and all injected invalid citations fail closed.
- **Fail criteria:** Any unresolved source; checksum or filename mismatch; wrong or nonexistent page; noncontiguous, altered, or model-authored excerpt/citation metadata; uncited material claim; missing OCR label/manual check; or accepted invalid citation.
- **Time box:** Four hours after the evidence viewer exists.

### Evidence, artifact, schedule, and failure behavior

- **Generated evidence and output location:** Citation-resolution matrix, checksum/page/excerpt comparisons, viewer captures, OCR review worksheet, invalid-citation injections, and discrepancy log under `evaluation/runs/EXP-06/<run-id>/`.
- **Configuration or decision artifact produced:** A reviewed `docs/experiment-decisions/EXP-06.md` plus the versioned citation schema, resolver/viewer contract, excerpt rule, OCR label, and automated resolution tests named by that record.
- **Execution milestone:** Milestone 11.
- **Failed or inconclusive behavior:** Do not claim citation verification or pass Milestone 11. Suppress unresolved citations and any answer that depends on them, correct the resolver/viewer contract through reviewed change control, and rerun all affected citations without weakening the 100% gates.

## 9. Planned execution order and milestone effect

| Execution milestone | Required experiments | Gate effect |
|---|---|---|
| Milestone 9 | EXP-01 and EXP-03 | Affected document classes cannot publish and retrieval work cannot proceed unless both relevant plans pass. |
| Milestone 10, before generation | EXP-02 | Generation remains disabled until a bounded retrieval configuration passes and is frozen. |
| Milestone 10, after validation exists | EXP-04 and EXP-05 | No generated-answer path passes unless a model and the independent server gate both pass. |
| Milestone 11 | EXP-06 | Citation/source-viewer acceptance requires every citation-resolution gate to pass. |

This interim Milestone 7a satisfies only the experiment-planning prerequisite. It permits Milestone 8 scaffolding to begin but does not claim that any experiment has executed or passed. EXP-07 through EXP-10 remain required at the later gates defined in [ARCHITECTURE.md](ARCHITECTURE.md); this plan does not change, defer, or satisfy them.
