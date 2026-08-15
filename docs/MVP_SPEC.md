# Kendra MVP Specification

**Status:** Frozen for the first MVP implementation phase
**Freeze date:** 2026-08-15
**Scope:** Documentation and acceptance contract only; no implementation is authorized by this milestone

## 1. Purpose

This document is the normative acceptance contract for Kendra's first complete vertical slice. The MVP must accept an approved PDF, preserve and process it locally, retrieve page-grounded evidence, generate a locally produced answer, and return citations that a reviewer can resolve to the exact preserved source page. When the uploaded documents do not support an answer, the user-visible answer must be exactly:

> Insufficient information in the uploaded documents.

The preserved original PDF is authoritative. Extraction, OCR, chunks, embeddings, indexes, metadata mirrors, excerpts, and generated answers are derived aids and do not replace the original.

This specification must be read with [ARCHITECTURE.md](ARCHITECTURE.md), [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md), [THREAT_MODEL.md](THREAT_MODEL.md), [EVALUATION_METHOD.md](EVALUATION_METHOD.md), [source-of-truth-policy.md](source-of-truth-policy.md), and ADRs [001](adr/001-local-first.md), [002](adr/002-document-storage.md), and [003](adr/003-grounded-answering.md). If a lower-level implementation choice conflicts with those controls or this contract, the implementation does not pass.

## 2. Preflight evidence

Milestones 1–6 were confirmed from Git artifacts before this specification was created:

| Milestone | Commit | Artifact evidence |
|---|---|---|
| 1 | `f7258bb` | Repository governance, source-of-truth policy, ignore rules, and project boundaries |
| 2 | `1aa56e5` | `PRODUCT_BRIEF.md`, `ASSUMPTIONS.md`, and `OPEN_QUESTIONS.md`; the commit message is mislabeled but the required artifacts are present |
| 3 | `6cec1a4` | `USER_WORKFLOWS.md` |
| 4 | `034daac` | `DATA_GOVERNANCE.md` and `THREAT_MODEL.md` |
| 5 | `1cb5d9e` | `EVALUATION_METHOD.md` and `evaluation/gold_cases.json` |
| 6 | `94abd11` | `ARCHITECTURE.md` and ADRs 001–003 |

The empty follow-up commit `81f48f1` does not change Milestone 4's artifact set. Git history must not be rewritten merely to correct milestone labels.

## 3. Freeze determination

The MVP contract is **frozen** because no unresolved decision currently changes the accepted service topology, trust boundaries, authority model, or storage ownership:

- the deployment is one local Docker Compose project on one controlled workstation;
- the web, modular FastAPI application, PostgreSQL, Qdrant, and Ollama boundaries are fixed;
- originals use `LocalDocumentStore` outside Git;
- ordinary runtime access to originals is read-only;
- ingestion is serialized and operator-controlled through a one-off use of the application image, not a continuously running worker;
- BGE-M3, Qdrant, Docling, page-level Tesseract fallback, and an Ollama-served Qwen-family model are fixed component families; and
- grounding and citations are enforced by the API, not trusted to model prose.

For this MVP, **upload** means that a trusted operator submits an approved local PDF and its approval manifest to the controlled one-off ingestion interface. It does not mean browser upload or an ordinary runtime API write to the document repository. Adding browser upload would widen write privileges and change ADR-002's trust boundary; that change requires an ADR update and makes this specification unfrozen until reviewed.

The following calibration values remain to be selected by the experiments in `ARCHITECTURE.md`, but they do not change the accepted architecture:

| Calibration item | Required freeze artifact before an acceptance run |
|---|---|
| Docling quality gate and Tesseract trigger | Versioned extraction configuration and EXP-01 result |
| Chunk size, positive overlap, table/form handling | Versioned chunker configuration and EXP-03 result |
| BGE-M3 dense-only or dense-plus-sparse retrieval | Versioned retrieval configuration and EXP-02 result |
| `top_k` and candidate-support threshold | Versioned retrieval configuration selected without using evaluation answers at request time |
| Exact Qwen variant, quantization, context, and timeout | Pinned model identity and EXP-04 result |
| Prompt and structured-output schema versions | Git revision or immutable content checksum |

An acceptance run with an unset, unrecorded, or post hoc changed calibration value fails. If an experiment shows that a new service, worker, cloud dependency, cross-page citation model, different authoritative store, or different trust boundary is required, the specification is no longer frozen and implementation must stop pending a reviewed architecture decision.

## 4. MVP operating boundary

The MVP is limited to:

- one trusted operator/evaluator;
- one local workstation;
- loopback-only user-facing ports;
- the approved public BIR evaluation corpus;
- one bounded collection and one active published index generation;
- serialized ingestion and one in-flight question unless an experiment records a stricter limit; and
- operation with outbound networking disabled after dependencies and model artifacts are staged.

No real agency, confidential, personal, privileged, procurement-sensitive, case-restricted, or mixed-permission document may be ingested. Passing this MVP does not demonstrate authenticity, currentness, applicability, lawful custody, access control, production readiness, or agency approval.

The current evaluation candidate contains nine PDFs, 41 physical pages, and 50 questions: 40 supported and 10 deliberately unsupported. Fourteen questions depend on the 12-page image-only OCR document. The dataset remains `initial_expert_review_required`; results are provisional until the human review and adjudication gate in `EVALUATION_METHOD.md` is complete.

## 5. Global invariants

Every implementation and verification must preserve these invariants:

1. Physical PDF pages are numbered from one. Printed labels may be additional metadata but never replace physical page numbers.
2. Each byte change creates a new immutable `version_id` and SHA-256 checksum. Existing source bytes are never overwritten.
3. Every derived record identifies its source `version_id`, source checksum, processing run, and producing Git/pipeline revision.
4. Page text and chunks never cross physical page boundaries.
5. Qdrant is derived and disposable. A vector hit cannot support an answer until the API resolves it through the active PostgreSQL generation to the exact source version and page.
6. Document text is untrusted evidence, never an instruction to the application or model.
7. The model cannot create trusted filenames, page numbers, excerpts, checksums, paths, or citations.
8. Every material supported claim has at least one API-validated evidence identifier and citation.
9. Retrieval similarity and model self-report are not proof of support.
10. A source checksum mismatch, missing original, inactive generation, invalid model schema, unknown evidence identifier, or unresolved material conflict cannot produce a supported answer.
11. The full upload-to-answer path must complete locally with zero unexpected outbound network connections.
12. Original documents, derived data, secrets, runtime state, and generated evaluation reports remain outside Git.

## 6. Vertical-slice acceptance contract

### Step 1 — Upload a PDF

| Contract field | Requirement |
|---|---|
| Input | One local PDF path plus the approved collection/intake manifest, submitted by the trusted operator to the one-off ingestion interface. The manifest identifies the permitted filename, expected SHA-256, page count, and approval scope. |
| Expected behavior | The interface streams the selected bytes into a quarantined staging area without changing them, treats the filename and PDF contents as untrusted input, and creates a unique ingestion correlation identifier. Ordinary runtime services do not receive write access to the authoritative repository. |
| Output | A machine-readable intake receipt containing `ingestion_id`, original filename, received byte length, quarantine state, and start time. It contains no source excerpt. |
| Failure behavior | A missing file or manifest, unreadable input, disallowed approval scope, path-containment failure, unsupported media type, configured size/page limit breach, or interrupted transfer fails closed. No admitted version or searchable partial content is created. |
| Measurable acceptance criteria | Each of the nine approved PDFs can be submitted; the staged byte length equals the input byte length; the staged SHA-256 equals the input SHA-256; and failed submissions create zero admitted versions and zero Qdrant points. |
| Required verification | **Automated:** valid, missing, truncated, non-PDF, oversized, path-traversal, interrupted-transfer, and manifest-mismatch tests. **Manual:** operator confirms that admission requires the explicit one-off path and that the running API source mount is read-only. |

### Step 2 — Validate and store the original locally

| Contract field | Requirement |
|---|---|
| Input | Quarantined bytes and the approved manifest from Step 1. |
| Expected behavior | Recalculate SHA-256; verify media type, readability, encryption state, filename set, byte length, physical page count, and approval scope; allocate opaque `document_id` and `version_id`; write the exact PDF and durable manifest to staging; then atomically admit both without overwriting an existing version. |
| Output | An immutable local object plus manifest, and a registry record containing stable IDs, original filename, SHA-256, byte length, media type, one-based page count, logical repository URI, provenance reference, admission state, and processing state. |
| Failure behavior | Checksum, page-count, readability, encryption, manifest, synchronization, or atomic-admission failure leaves the item quarantined or failed. It is not processed, indexed, or returned by retrieval. Existing admitted bytes remain unchanged. |
| Measurable acceptance criteria | All nine stored source checksums and page counts exactly match both `APPROVAL_MANIFEST.json` and `evaluation/gold_cases.json`; all 41 pages are represented by the admitted objects; a byte-altered file is rejected; and failure injection before or during atomic admission never overwrites an existing object. |
| Required verification | **Automated:** checksum/page-count precondition, immutable-path, duplicate, byte-change, atomicity, path-containment, stream, and range-read tests. **Manual:** open each stored PDF and confirm it is the approved original rendition; inspect repository permissions and separation from Git and derived stores. |

### Step 3 — Parse every page

| Contract field | Requirement |
|---|---|
| Input | One admitted, checksum-verified PDF version. |
| Expected behavior | Docling attempts every physical page independently and preserves page order, layout blocks, and source-region mapping where available. A page receives an explicit terminal state: `extracted`, `ocr_required`, `verified_blank`, or `unextractable`; absence of text is never silently recorded as successful extraction. |
| Output | Exactly one page record for every physical page, containing `version_id`, physical page number, extraction method/state, quality result, derived text/layout or verified-blank marker, and processing-run identity. |
| Failure behavior | Parser error, timeout, resource limit, page-count discrepancy, missing page record, duplicate page number, or unusable nonblank page blocks publication of that document's staging generation. The prior active generation remains searchable. |
| Measurable acceptance criteria | The nine approved PDFs produce exactly 41 page records; each document has the contiguous page sequence `1..page_count` with no omission or duplicate; and every nonblank page ends as `extracted` or successfully OCR-extracted before publication. |
| Required verification | **Automated:** record-count, contiguous-numbering, page-boundary, blank-page, parser-timeout, and partial-failure tests. **Manual:** compare representative digital, table-heavy, form-layout, and image-only page records with the opened originals. |

### Step 4 — Use OCR when ordinary extraction is insufficient

| Contract field | Requirement |
|---|---|
| Input | A page marked `ocr_required` by the versioned Docling quality gate. |
| Expected behavior | Run the pinned local Tesseract configuration only for that page, preserve the same physical page identity and available source regions, record Docling and OCR outputs separately, and select the usable derived representation without altering the original. The 12 pages of `RMC_77_2024_Invoicing_QA_OCR.pdf` must trigger OCR. |
| Output | Page-scoped OCR text, OCR/tool/language configuration identity, quality result, physical-page/source-region mapping, and `extraction_method: tesseract`. |
| Failure behavior | OCR timeout, crash, unusable output, or lost page mapping marks the page `unextractable`, blocks publication for that source version, and cannot be replaced by model memory or an empty successful record. |
| Measurable acceptance criteria | OCR runs on all 12 pages of the image-only circular and on every other page that fails the frozen quality gate; it does not run on a page that passes that gate; all 14 OCR-required evaluation questions remain traceable to their expected original pages; and OCR activity makes zero external network requests. |
| Required verification | **Automated:** quality-gate branch coverage, all-page OCR fixture, method/version recording, timeout, empty-output, and mapping-loss tests. **Manual:** reviewers compare every cited OCR excerpt with the rendered source page and record material OCR errors. |

### Step 5 — Divide page text into overlapping, page-aware chunks

| Contract field | Requirement |
|---|---|
| Input | Accepted page-scoped Docling or OCR text/layout and the frozen chunker configuration. |
| Expected behavior | Create deterministic chunks that never cross a physical page. Consecutive chunks from a page with more than one chunk have a positive configured overlap. Table/form chunks retain the headings and row/column context required to interpret their content. |
| Output | Stable `chunk_id`, `version_id`, source checksum, physical page, page-text offsets or source regions, sequence, text, extraction method, processing-run ID, chunker version/configuration, and chunk content checksum. |
| Failure behavior | Missing coverage, cross-page content, invalid offsets, absent source identity, duplicate chunk ID, lost table context, or nondeterministic output under the same pinned inputs blocks the staging generation. |
| Measurable acceptance criteria | One hundred percent of chunks reference exactly one existing physical page; all usable page text is covered without gaps; every multi-chunk page has positive overlap between adjacent chunks; all offsets are in bounds; chunk IDs are unique; and a rebuild with identical inputs/configuration produces the same ordered chunk identities and checksums. |
| Required verification | **Automated:** coverage, overlap, page-boundary, offset, uniqueness, deterministic-rebuild, and source-pointer tests. **Manual:** inspect chunks for the table, form, list, OCR, and cross-document strata to confirm necessary context was not separated. |

### Step 6 — Generate embeddings locally

| Contract field | Requirement |
|---|---|
| Input | Every publishable chunk and the pinned local BGE-M3 configuration. |
| Expected behavior | Generate one embedding representation per chunk inside the local application environment. Query embeddings use the same compatible model/configuration. No source content or query is sent to an external service. |
| Output | One finite, correctly dimensioned vector representation per chunk, linked to `chunk_id`, embedding model/artifact identity, runtime version, and processing run. Sparse fields may be included only if the frozen EXP-02 configuration selects BGE-M3 dense-plus-sparse retrieval. |
| Failure behavior | Missing model artifact, dimension mismatch, non-finite value, incomplete batch, runtime failure, or network dependency fails the processing run. The system does not publish partial embeddings or substitute another model silently. |
| Measurable acceptance criteria | Embedding count equals publishable chunk count; every vector has the configured dimension and only finite values; every vector identifies the pinned BGE-M3 artifact; query and document dimensions match; and an outbound-disabled clean run completes without network attempts. |
| Required verification | **Automated:** count, dimension, finite-value, model-identity, partial-batch, incompatible-query, and offline tests. **Manual:** inspect the recorded model artifact checksum/license inventory and verify no cloud endpoint is configured. |

### Step 7 — Store vectors and metadata

| Contract field | Requirement |
|---|---|
| Input | Validated source/page/chunk records and complete BGE-M3 representations from Steps 2–6. |
| Expected behavior | Write vectors and minimal retrieval payloads to a new Qdrant staging generation; write source, processing, page, chunk, and publication metadata to PostgreSQL; validate every pointer; then atomically make the new generation active. The active generation is never mutated in place. |
| Output | A published `index_generation` plus Qdrant points containing only `chunk_id`, `version_id`, source checksum, physical page, processing-run ID, and generation ID. PostgreSQL retains the remaining resolvable metadata and publication state. |
| Failure behavior | Count mismatch, orphan pointer, checksum mismatch, incomplete document, Qdrant/PostgreSQL disagreement, storage failure, or interrupted publication marks staging failed and leaves the prior active generation unchanged. |
| Measurable acceptance criteria | Qdrant point count equals the publishable chunk count; 100% of points resolve through PostgreSQL to an admitted source version/checksum/page and the same generation; zero orphan or mixed-generation points exist; and injected failures before/during publication leave only the old generation searchable. |
| Required verification | **Automated:** count reconciliation, payload-schema, pointer, checksum, generation, atomic-publication, rollback, stale-index, and rebuild tests. **Manual:** inspect one complete source-to-page-to-chunk-to-point chain and confirm that Qdrant does not contain authoritative PDF bytes or unrestricted metadata. |

### Step 8 — Ask a question

| Contract field | Requirement |
|---|---|
| Input | `POST /api/v1/questions` with UTF-8 JSON containing a nonempty `question` of at most 2,000 Unicode code points and the fixed MVP `collection_id`. |
| Expected behavior | Validate the request, assign a `request_id`, bind it to the single active collection/generation, preserve the exact accepted question in protected derived run data, and start monotonic timing. The browser communicates only with the loopback-local application. |
| Output | A structured semantic response described in Section 7, or a typed HTTP error before retrieval begins. |
| Failure behavior | Empty, whitespace-only, over-limit, malformed, unknown-collection, or extra control-bearing input is rejected without model invocation. No question text is placed in a URL, Git, or an external service. |
| Measurable acceptance criteria | Valid questions enter retrieval exactly once; invalid requests cause zero embedding, Qdrant, or model calls; the request ID is unique; and captured timing/query data stays in the approved local derived-output location. |
| Required verification | **Automated:** request schema, Unicode, boundary-length, unknown-field, unknown-collection, duplicate-submission, and no-downstream-call tests. **Manual:** inspect browser/API traffic and local logs for content minimization and loopback-only routing. |

### Step 9 — Retrieve relevant evidence

| Contract field | Requirement |
|---|---|
| Input | Validated question, active generation identity, frozen BGE-M3 query configuration, `top_k`, and candidate threshold. |
| Expected behavior | Embed the question locally, search only the active Qdrant generation, apply the frozen candidate rule, resolve every hit through PostgreSQL, confirm the exact original version is present and checksum-valid, and provide only bounded evidence IDs/text to the answerer. |
| Output | An ordered internal evidence set containing opaque evidence IDs, scores, chunk IDs, source versions/checksums, physical pages, excerpts, extraction method, and generation identity. Scores are diagnostic relevance signals, not support declarations. |
| Failure behavior | No candidate above the rule yields `insufficient_evidence`; missing Qdrant/PostgreSQL/source state yields a typed safe failure; orphaned, stale, inactive, cross-generation, or checksum-invalid hits are discarded and cannot support an answer. |
| Measurable acceptance criteria | One hundred percent of supplied evidence IDs belong to the active generation and resolve to checksum-valid originals; zero below-threshold or orphaned hits reach the model; supported evaluation cases include their adjudicated supporting pages within the retrieval set; and deliberately unsupported cases cannot pass merely related text as support. |
| Required verification | **Automated:** retrieval-only evaluation, active-generation filter, threshold boundary, stale/orphan/cross-generation injection, missing-source, and expected-page recall tests. **Manual:** review false negatives and near-match false positives by direct, table/list, comparison, OCR, and unsupported stratum before generation results are considered. |

### Step 10 — Generate an answer locally

| Contract field | Requirement |
|---|---|
| Input | The question, fixed system instructions, and numbered/delimited untrusted evidence items from Step 9. |
| Expected behavior | The pinned Qwen-family model runs through local Ollama with no tools or network access and returns the frozen structured schema: status, bounded material claims, and evidence IDs selected only from the supplied set. The API validates the schema and evidence membership before using any prose. |
| Output | A validated `supported`, `insufficient_evidence`, or `conflicting_evidence` model result. The API may also produce `source_unavailable` or `system_error`; those are system outcomes, not supported answers. |
| Failure behavior | Timeout, unavailable model, invalid JSON/schema, unknown evidence ID, uncited material claim, prompt-injection compliance, or generated source metadata causes the prose to be discarded and returns a conservative typed failure. There is no fallback to pretrained memory, cloud AI, or an unvalidated answer. |
| Measurable acceptance criteria | Every accepted supported claim references at least one supplied evidence ID; zero accepted claims use an unknown ID; all document-borne instruction fixtures fail to alter policy or invoke tools; and the complete 50-case evaluation runs locally with every timeout/error counted rather than omitted. |
| Required verification | **Automated:** schema/property tests, unknown/missing evidence IDs, uncited claims, prompt injection, model timeout/unavailability, no-tool, and outbound-disabled evaluation. **Manual:** expert review of factual completeness, material qualifications, source attribution, and automation-bias risks. |

### Step 11 — Return exact filename, page, and excerpt citations

| Contract field | Requirement |
|---|---|
| Input | API-validated claims and evidence IDs from Step 10. |
| Expected behavior | `CitationResolver` builds citations exclusively from server-owned records. Each material claim links to one or more citation objects. The UI displays citations adjacent to claims and can open the preserved PDF at the cited physical page. |
| Output | Each citation contains `citation_id`, `claim_id`, `document_id`, `version_id`, source SHA-256, exact original filename, one-based physical `page`, an exact contiguous evidence `excerpt`, `chunk_id`, extraction method, processing-run ID, producing Git/pipeline revision, and a source URL built from server-owned IDs. |
| Failure behavior | Missing claim linkage, caller/model-authored metadata, invalid page, noncontiguous or altered excerpt, unresolved original, checksum mismatch, or inaccessible source prevents a supported response. The system never substitutes an index excerpt for a missing original. |
| Measurable acceptance criteria | Filename equals the admitted `original_filename`; page exists in the checksum-matched PDF; excerpt exactly equals a contiguous substring of the stored page-derived evidence used for the claim; 100% of material claims have a valid citation; citation precision, completeness, correct-page rate, and source resolvability are each 100% on the accepted MVP evaluation run. |
| Required verification | **Automated:** server-ownership, claim-link, exact-substring, checksum, page-range, source-open, wrong-page, altered-excerpt, and missing-original tests. **Manual:** reviewers open every evaluation citation at the original physical page and confirm the passage supports the adjacent claim in context; OCR excerpts are visibly labeled derived and checked against the rendered page. |

### Step 12 — Return the exact unsupported response

| Contract field | Requirement |
|---|---|
| Input | A valid question for which the uploaded, admitted, permitted corpus lacks sufficient resolvable evidence, including no qualifying candidate, a missing required fact/condition, or a currentness/applicability question without authoritative status evidence. |
| Expected behavior | The API returns `status: insufficient_evidence`, does not ask the model to guess, and supplies no affirmative citation. The user-visible answer contains exactly `Insufficient information in the uploaded documents.` with identical capitalization and punctuation and no prefix, suffix, explanation, or disclaimer. |
| Output | HTTP 200 semantic response with the exact answer string, an empty `claims` array, and an empty `citations` array. Machine-readable request/timing/version metadata may remain outside the user-visible answer field. |
| Failure behavior | A guessed fact, model-memory answer, external-source answer, merely related citation, caveated definitive answer, altered wording, or nonempty claim/citation array fails the MVP contract. A genuine conflict, unavailable source, or system error uses its distinct typed status and must not masquerade as ordinary insufficiency. |
| Measurable acceptance criteria | All 10 deliberately unsupported cases return the exact 51-character ASCII answer string, zero claims, and zero citations; unsupported rejection rate is 100%; unsupported false-answer rate is 0%; and identical behavior is observed with outbound networking disabled. |
| Required verification | **Automated:** byte-for-byte response-field assertion across all unsupported cases plus near-match, below-threshold, currentness, prompt-injection, and model-memory traps. **Manual:** confirm that the UI renders only the exact sentence and does not add helper prose, toast text, or a fabricated source. |

## 7. API-level acceptance contract

### 7.1 Question request

```http
POST /api/v1/questions
Content-Type: application/json
```

```json
{
  "question": "When was Revenue Regulations No. 2-2024 issued?",
  "collection_id": "kendra-bir-public-gold-v1"
}
```

Only the fields above are accepted in the first MVP. Authentication or user context is not implied.

### 7.2 Supported response

```json
{
  "request_id": "opaque-request-id",
  "status": "supported",
  "answer": "Revenue Regulations No. 2-2024 was issued on February 28, 2024.",
  "claims": [
    {
      "claim_id": "claim-1",
      "text": "Revenue Regulations No. 2-2024 was issued on February 28, 2024.",
      "citation_ids": ["citation-1"]
    }
  ],
  "citations": [
    {
      "citation_id": "citation-1",
      "claim_id": "claim-1",
      "document_id": "opaque-document-id",
      "version_id": "opaque-version-id",
      "source_sha256": "64-lowercase-hex-characters",
      "filename": "RR_02_2024_Publication.pdf",
      "page": 1,
      "excerpt": "exact contiguous server-owned evidence excerpt",
      "chunk_id": "opaque-chunk-id",
      "extraction_method": "docling",
      "processing_run_id": "opaque-processing-run-id",
      "pipeline_git_revision": "full-git-commit-id",
      "source_url": "/api/v1/documents/opaque-version-id/content#page=1"
    }
  ],
  "limitations": []
}
```

The example values are illustrative; the field names and invariants are normative. The API builds the citation object after validation.

### 7.3 Unsupported response

```json
{
  "request_id": "opaque-request-id",
  "status": "insufficient_evidence",
  "answer": "Insufficient information in the uploaded documents.",
  "claims": [],
  "citations": []
}
```

The `answer` value is immutable contract text. Localization, explanatory additions, or alternate punctuation are outside this MVP.

### 7.4 Other safe outcomes

| Status | HTTP behavior | User-visible behavior |
|---|---|---|
| `conflicting_evidence` | 200 semantic outcome | No definitive answer; show the competing, validated source pages without deciding which controls |
| `source_unavailable` | 503 | No derived excerpt is presented as authoritative; explain that the original cannot be verified |
| `system_error` | 500 or 503 | No generated prose is exposed; return a correlation identifier without source/query content |

### 7.5 Source access

`GET /api/v1/documents/{version_id}/content` streams only the server-resolved preserved PDF after containment, identity, and checksum validation. The caller cannot supply a filesystem path. The citation's one-based page is used by the client PDF viewer; requesting a missing or mismatched version fails closed.

The MVP has no ordinary HTTP upload endpoint. The controlled one-off ingestion interface must emit machine-readable status using the same identifiers and terminal states defined in Steps 1–7.

## 8. End-to-end acceptance gate

The MVP implementation is accepted only when one reproducible run demonstrates all of the following:

1. Source preconditions pass for the exact nine approved PDFs and their approval manifest.
2. Stored originals match all nine expected checksums and all 41 physical pages.
3. Every physical page is attempted, and every nonblank published page has usable page-mapped text.
4. Tesseract is used for all 12 pages of the image-only circular and only where the frozen quality rule requires it elsewhere.
5. All chunks are deterministic, overlapping where split, page-bounded, and source-resolvable.
6. Every publishable chunk has a valid local BGE-M3 representation and matching Qdrant point.
7. Publication reconciliation finds zero orphaned, stale, mixed-generation, or checksum-mismatched entries.
8. All 50 evaluation cases are attempted under one recorded configuration and seed; no failure or timeout is silently excluded.
9. All 40 supported evaluation cases return `status: supported` and satisfy the strict atomic-fact rules in `EVALUATION_METHOD.md`; every material claim has correct, complete, source-resolvable page citations.
10. All 10 deliberately unsupported cases return the exact required sentence with no claims or citations.
11. Every citation reopens the checksum-matched original at the correct one-based physical page, and the displayed excerpt matches the evidence actually used.
12. A clean restart, rebuild of disposable derived data, and rerun preserve source identities and citation resolution.
13. With outbound networking disabled, admission, clean derived-data rebuild, question answering, citation opening, and the full evaluation run complete with zero unexpected external requests.
14. No real restricted document, secret, source PDF, model weight, database, index, cache, log, or generated evaluation report is added to Git.

Because the current gold set still requires expert review, an engineering run may be reported as provisional but the MVP must not be declared accepted until the human-review and adjudication procedure in `EVALUATION_METHOD.md` is complete. This is an evaluation-governance gate, not an unresolved architecture decision.

## 9. Required verification evidence

The eventual implementation milestone must retain outside Git a run manifest containing:

- source approval-manifest checksum and all source checksums;
- dataset ID, schema version, status, and Git revision;
- application Git revision;
- Docling, Tesseract/language-data, chunker, BGE-M3, Qdrant, PostgreSQL, Ollama, Qwen, prompt, and schema identities;
- hardware, operating system, container image digests, resource limits, and network state;
- active index-generation ID and source-set manifest checksum;
- automated test results and failure-injection results;
- evaluation metrics and all attempted/completed/failed/timed-out counts;
- manual page/citation review sign-off and adjudication state; and
- evidence from the zero-outbound-network test.

Generated answers, traces, screenshots, metrics, logs, and reports remain derived data outside Git. Git may contain only non-sensitive test definitions, fixtures, scoring rules, configuration templates, and reviewed code.

## 10. Explicit deferrals

The following are not part of the MVP and must not be claimed, stubbed as if complete, or used as acceptance evidence:

- authentication;
- user management;
- roles, permissions, session management, and offline revocation;
- NAS deployment;
- cloud AI or any external model/embedding fallback;
- analytics platforms;
- production monitoring or alerting platforms;
- high availability, automatic failover, or production RPO/RTO;
- multi-agency tenancy;
- multi-user or mixed-permission operation;
- real confidential or personal data;
- production backup, disaster-recovery, retention, or incident-response claims;
- automated document currentness, authenticity, applicability, legal interpretation, procurement decisions, or approvals; and
- corpus federation, background watching, synchronization, or a distributed worker platform.

These deferrals are deliberate scope boundaries. They do not waive the governance or threat-model controls required before any real-document pilot.

## 11. Change control

This specification may be clarified without unfreezing only when the change does not alter an observable acceptance requirement, component family, service boundary, source authority rule, trust boundary, API field meaning, exact unsupported text, or deferred scope.

Any material change requires:

1. marking this document **Not frozen**;
2. recording the unresolved decision and its impact;
3. updating or adding the relevant ADR and governance documents;
4. revising affected evaluation cases and migration/rollback requirements; and
5. obtaining review before implementation continues.

Implementation performance does not justify silently weakening this contract. A failed criterion is evidence to improve the design, narrow the declared document class, or formally revise the architecture—not permission to fabricate support, relax citations, or hide uncertainty.
