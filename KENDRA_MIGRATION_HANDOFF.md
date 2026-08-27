# KENDRA migration handoff

- **Repository:** `/Users/mariacherrienakaya/Projects/kendra`
- **Snapshot date:** 2026-08-24 (Asia/Manila)
- **Purpose:** evidence-backed resumption guide for a fresh Codex session
- **Snapshot HEAD:** `2ec7b8072eb70e8228d17b68604f873a1b9fd864`

This file describes the repository as inspected on the snapshot date. It separates code
presence from milestone acceptance: Milestone 10 code exists on a prototype branch, but the
recorded experiment and governance gates still classify Milestone 10 as blocked. Do not erase
that distinction.

## 1. Resume here first

1. Work in `/Users/mariacherrienakaya/Projects/kendra`, not in a ChatGPT project mirror.
2. Before changing anything, run the Git baseline commands in Section 9. The checkout already
   contains uncommitted Milestone 5 evaluation/adjudication work; preserve it.
3. Do not begin Milestone 11 application code. The exact next task is to finish the independent
   review and adjudication of the uncommitted `kendra-bir-public-gold-v2` candidate, then close
   the experiment and specification gates listed in Section 12.
4. Treat original, immutable PDF bytes plus their IDs, checksum, provenance, and physical-page
   location as authoritative. OCR, text, chunks, vectors, database rows, scores, and answers are
   derived and non-authoritative.
5. The allowed runtime scope remains localhost, one trusted evaluator, and the approved public
   BIR evaluation corpus only. There is no authentication. Do not ingest real agency, personal,
   confidential, privileged, procurement-sensitive, case-restricted, or mixed-permission data.

## 2. Current Git state

### Branch and commits

| Item | Verified value |
|---|---|
| Branch | `prototype/milestone-10-verification-contract` |
| HEAD | `2ec7b8072eb70e8228d17b68604f873a1b9fd864` — `docs: correct the span-containment rule before EXP-05 freezes` |
| Upstream | `origin/prototype/milestone-10-verification-contract` |
| Upstream relationship | ahead by 4, behind by 0 |
| `main` | `f3d0f39970fa0eeb3e1e05b9d493d0cb07744e7c` |
| HEAD versus local `main` | ahead by 7, behind by 0 |
| `origin/main` relationship | local `main` is ahead by 18 according to `git branch -vv` |
| Remote | `origin` = `https://github.com/JM-Kendra/KENDRA.git` for fetch and push |

The seven commits on the current branch after local `main` are:

```text
c8eec18 prototype: add Milestone 10 verification contract, unimplemented by design
666ba8e milestone-10: implement grounded question answering
49c234d docs: propose ADR-010 verified-span answering, raise EXP-07 identifier collision
8bba366 docs: draft EXP-05 preregistration for verified-span answering
bb1e377 milestone-10: serve preserved sources so citations can be opened
6814bb9 docs: propose ADR-011 interface surface unfreeze for Milestone 11
2ec7b80 docs: correct the span-containment rule before EXP-05 freezes
```

### Pre-existing uncommitted work

The following state was present before this handoff was created. Do not discard, stage, or
combine it with other work without the project owner's direction.

Modified:

- `docs/EVALUATION_METHOD.md`
- `docs/experiment-decisions/gold-case-defect-CD003-CD010.md`
- `evaluation/README.md`
- `evaluation/cases/README.md`
- `evaluation/gold_cases.json`
- `scripts/README.md`

Untracked:

- `evaluation/cases/M5_GOLD_V2_REVIEW.md`
- `scripts/prepare_m5_adjudication.py`
- `scripts/validate_gold_cases.py`

The changes advance the tracked candidate from `kendra-bir-public-gold-v1` to
`kendra-bir-public-gold-v2`, preserve `initial_expert_review_required`, and add page 1 to the
affected page scopes in `KND-M5-CD-003` and `KND-M5-CD-010`. They also add a hash-bound,
two-reviewer adjudication packet and mechanical validators. No expected fact or scoring
criterion was changed. The candidate SHA-256 is
`6aace5184c6778cad8c0d1972d83c99b6d3837355064ecc88dc941d86bab8f86`.

This handoff is itself an additional untracked file after saving. The snapshot above therefore
describes the tree immediately before `KENDRA_MIGRATION_HANDOFF.md` was added.

## 3. Architecture and trust boundaries

KENDRA is a local-first modular monolith deployed with Docker Compose:

- **Web:** Next.js 16 / React 19. The current page is a minimal readiness UI, not the planned
  Milestone 11 evidence-review interface.
- **API:** FastAPI/Python 3.12. It owns readiness, storage access, ingestion modules, retrieval,
  answer validation, citations, and source streaming.
- **PostgreSQL 17:** derived registry, processing, chunk, publication, and generation metadata.
- **Qdrant 1.18:** rebuildable vector collections and retrieval payloads.
- **Ollama 0.32:** local BGE-M3 embeddings and, in the prototype, a local Qwen answer model.
- **Docling, Poppler, and Tesseract:** local PDF detection/extraction tools inside the API image.

### Runtime topology

- `postgres`, `qdrant`, and `ollama` are on the internal `kendra_private` network only.
- `api` joins `kendra_private` and `kendra_edge`; its host port binds to `127.0.0.1` by default.
- `web` is on `kendra_edge` and also binds to `127.0.0.1` by default.
- The ordinary API mounts the document repository read-only.
- The profile-scoped `ingest` command mounts the approved intake read-only and the document
  repository writable solely for immutable admission.
- Model-loader services are profile-scoped setup jobs. No cloud fallback is allowed in the
  controlled run.

### Authoritative and derived data

Authoritative evidence is the exact preserved source version: immutable bytes, stable
`document_id`, exact `version_id` or SHA-256, provenance, and one-based physical-page
location. A byte change creates a new version; cited bytes are never overwritten.

PostgreSQL, Qdrant, OCR, extracted text, chunks, embeddings, model output, logs, caches, and
evaluation results are derived. They must resolve back to the admitted source and pipeline/Git
revision. If source identity, checksum, page, active generation, or permissions cannot be
verified, the system must fail closed.

### Ingestion flow

```text
approved PDF + closed manifest
  -> validate path/media/size/page count/checksum/approval fields
  -> atomically admit immutable original
  -> retain one whole-page representation per physical page
  -> deterministic page-bounded chunks
  -> local BGE-M3 embeddings
  -> PostgreSQL staging metadata + Qdrant staging generation
  -> activate only after complete publication
```

Processing failure preserves the admitted original, marks derived state failed where possible,
and never activates a partial Qdrant generation. Exact-checksum duplicates are idempotent.

### Answering flow on the prototype branch

```text
question + collection_id
  -> embed query and search the active generation
  -> resolve every candidate against server-owned PostgreSQL/source records
  -> reject stale, unknown, checksum-invalid, or out-of-range evidence
  -> give the model opaque request-scoped evidence IDs only
  -> parse a closed JSON response
  -> validate every claim and evidence ID
  -> construct citation metadata on the server
  -> return supported, insufficient_evidence, conflicting_evidence,
     source_unavailable, or system_error
```

The exact unsupported sentence is `Insufficient information in the uploaded documents.` and
must carry no claims or citations. The current implementation validates evidence IDs and source
metadata but does **not** prove that generated claim prose is entailed by or contained in the
cited excerpt; ADR-010 proposes verified-span answering to close that gap.

## 4. Directory structure

```text
.
├── apps/
│   ├── api/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/kendra_api/
│   │   │   ├── answering/       # M10 retrieval, model adapter, validation, citations
│   │   │   ├── connections/     # PostgreSQL, Qdrant, Ollama readiness clients
│   │   │   ├── ingestion/       # M9 validation through generation publication
│   │   │   ├── storage/         # source-storage seam and local implementation
│   │   │   ├── config.py        # typed KENDRA_* settings
│   │   │   ├── documents.py     # preserved-PDF streaming/range endpoint
│   │   │   ├── health.py        # GET /api/v1/health
│   │   │   └── main.py          # FastAPI factory and optional answering wiring
│   │   └── tests/               # backend, ingestion, M10, and source-content tests
│   └── web/
│       ├── Dockerfile
│       ├── package.json
│       └── src/app/              # current readiness-only interface
├── docs/
│   ├── adr/                      # ADR-001 through ADR-011
│   ├── experiment-decisions/     # EXP outcomes, drafts, defects, boundary calls
│   ├── ARCHITECTURE.md
│   ├── DATA_GOVERNANCE.md
│   ├── EVALUATION_METHOD.md
│   ├── EXPERIMENT_PLAN.md
│   ├── MVP_SPEC.md
│   ├── PRODUCT_BRIEF.md
│   ├── THREAT_MODEL.md
│   ├── USER_WORKFLOWS.md
│   └── source-of-truth-policy.md
├── evaluation/
│   ├── gold_cases.json           # tracked definitions; currently modified candidate v2
│   ├── cases/                    # review protocol; one untracked M5 packet
│   └── runs/                     # ignored generated evidence/results
├── scripts/                      # reviewed diagnostics and evaluation tooling
├── document-repository/          # ignored originals/manifests; never Git
├── intake/                       # ignored one-off admission input
├── docker-compose.yml
├── .env.example
├── README.md
└── CLAUDE.md                     # important invariants, but stale about code presence
```

`apps/worker/` was removed when the architecture settled on a modular API plus a one-off
ingestion command. There is no independently deployed worker service.

## 5. Milestones 1–10

Milestone mapping is artifact-based. The early commit subjects are inconsistent, and
`81f48f1` is empty; do not rewrite valid history merely to rename it.

| Milestone | Commit(s) and deliverable | Implementation status |
|---|---|---|
| 1 | `f7258bb` — repository governance, Git/artifact exclusions, source-of-truth policy, directory placeholders | Complete foundation. No application existed at this point. |
| 2 | `1aa56e5` — `PRODUCT_BRIEF.md`, `ASSUMPTIONS.md`, `OPEN_QUESTIONS.md` (subject says `1:`, but artifacts map to M2) | Documentation complete; product/user assumptions are not field-validated. No separate M2 marker commit exists. |
| 3 | `6cec1a4` — user roles, bounded workflows, citation packet, `CONFIRM` field hypotheses | Documentation complete; agency-specific roles/workflows still require confirmation. |
| 4 | `034daac` — data governance and threat model; `81f48f1` is an empty follow-up | Policy complete, controls largely unimplemented. Real or restricted data remains prohibited. |
| 5 | `1cb5d9e` — 50-case BIR gold set and evaluation method | Initial dataset committed, but never expert-adjudicated. Candidate v2 correction and its review tooling are currently uncommitted and still require two independent reviewers plus an adjudicator. |
| 6 | `94abd11` — local-first architecture and ADR-001 through ADR-003 | Architecture accepted for the bounded MVP. Later experiment outcomes have qualified parts of it. |
| 7 | `aa6a968` — frozen 12-step MVP contract; `a75611b` — EXP-01 through EXP-06 plan | Specification/plan complete, but final acceptance depends on expert adjudication and experiment gates. Proposed ADR-010/011 would require an explicit unfreeze before their wider contracts are implemented. |
| 8 | `ad2afd1`, `250f111` — Docker/FastAPI/Next.js foundation, typed settings, connections, storage seam, readiness UI and tests | Implemented and verified as a health-only foundation. No authentication. |
| 9 | `3ce70b6` — ingestion; `b6036ba` and later experiment records; `b1fcd79` — ADR-007 native-primary implementation | Code is implemented and unit-tested. Milestone acceptance is not complete: EXP-01 is failed/inconclusive and EXP-03 is failed/blocked. ADR-007 is accepted/implemented but is not a passing experiment. |
| 10 | `c8eec18` contract, `666ba8e` grounded answering, `bb1e377` preserved-source serving | Prototype code and hermetic tests exist. The milestone remains **blocked/not accepted** by repository governance; EXP-02/04/05 have not passed, Compose does not enable answering, and live contract tests were not run in this verification. |

## 6. Exactly what Milestone 9 changed

### Initial implementation: `3ce70b6`

The initial M9 commit changed 25 files with 2,174 insertions and 5 deletions. It added:

- closed-manifest PDF validation: contained intake path, PDF media/signature, byte/page limits,
  expected SHA-256, expected page count, approval scope/status, and provenance reference;
- immutable source admission under stable document/version identities with duplicate
  idempotency and unchanged-original checks;
- Docling/native extraction plus whole-page Tesseract fallback for sparse scanned pages;
- deterministic, overlapping, one-based, page-bounded chunks;
- local BGE-M3 embeddings through Ollama;
- PostgreSQL schema/registry code for documents, versions, pages, chunks, processing runs, and
  index generations;
- Qdrant staging collection writes and fail-closed generation publication;
- the `kendra-ingest` CLI and Compose `ingestion` / `ingestion-setup` profiles;
- Docling model staging and Ollama embedding-model staging; and
- generated digital/scanned PDF fixtures and ingestion adapter, extraction, pipeline, and
  validation tests.

Primary paths are `apps/api/src/kendra_api/ingestion/`, `apps/api/tests/test_ingestion_*`,
`apps/api/tests/pdf_fixtures.py`, `.env.example`, `docker-compose.yml`, and `README.md`.

### Follow-up M9 work

- `b6036ba` recorded EXP-01 extraction and EXP-03 chunking results.
- `288366f` preserved a failed extraction-completeness repair and introduced ADR-004
  fail-closed containment. Do not amend or erase this failure record.
- ADR-005 and ADR-006 were explored and rejected/not activated; their result-shaped evidence
  must not be retroactively reclassified.
- `2a0a16e` accepted ADR-007 and added native-primary contract tests.
- `b1fcd79` implemented `native-primary-detection-v1`: Poppler `-layout` native text is retained
  above the 40-character floor; otherwise whole-page Tesseract is retained. Docling becomes a
  non-retaining detector.
- The ADR-007 rerun retained 41/41 pages in two deterministic passes with zero unresolved
  conflicts, but established only 77/125 facts mechanically. Adjudication raised that to
  121/125; four facts were held by the gold-case page-scoping defect, and MF-01 remained open.

Important: `KENDRA_EXTRACTION_COMPLETENESS_POLICY` exists in settings and `.env.example`, but
the reference Compose `api` and `ingest` environment lists do not pass it through. Current
settings therefore default to the older `native-page-token-coverage-v1`, not accepted ADR-007's
`native-primary-detection-v1`. Do not claim the reference deployment runs ADR-007 until this is
corrected and verified under approved change control.

## 7. Exactly what Milestone 10 changed

### Contract first: `c8eec18`

- Added `apps/api/tests/test_milestone10_contract.py` before answering code.
- Registered hermetic `milestone10` and live `milestone10_live` pytest markers.
- Kept both markers outside the default 53-test baseline.
- Encoded fail-closed behavior, API-owned citations, known OCR corruption protection, and
  live-corpus expectations without committing source document text.

### Grounded answering: `666ba8e`

This commit changed 12 files with 956 insertions and 8 deletions. It added
`apps/api/src/kendra_api/answering/` with:

- request/response, claim, citation, source, and evidence models;
- Qdrant retrieval tied to the active PostgreSQL generation;
- PostgreSQL source/version resolution;
- a bounded Ollama answer-model adapter using opaque evidence IDs;
- two-stage server validation and typed abstention/error responses;
- server-built citation IDs, source/version/checksum/page/chunk/extraction/run/revision fields;
- `POST /api/v1/questions`; and
- optional collaborator wiring behind `KENDRA_ANSWERING_ENABLED`.

The implementation rejects or abstains on empty retrieval, inactive generations, checksum
mismatch, invalid pages, unknown evidence IDs, absent collaborators, invalid model JSON, and
retrieval/model/registry failures. It prevents the model from authoring citation metadata.

It does **not** establish source-text fidelity or claim entailment. A model-authored claim can
still be plausible prose whose cited excerpt does not support it. The observed unsupported-case
failure motivated proposed ADR-010 verified-span answering and the EXP-05 draft.

### Openable citations: `bb1e377`

- Added `GET /api/v1/documents/{version_id}/content`.
- Resolves a version through the server registry and `LocalDocumentStore`.
- Re-hashes the preserved bytes before serving.
- Streams exact PDF bytes, supports byte ranges, rejects traversal/unknown/checksum-invalid
  sources, and emits safe headers.
- Added `apps/api/tests/test_documents_content.py` and `scripts/m10_answer_diagnostic.py`.

### Deployment reality

M10 is off by default. `docker-compose.yml` does not pass `KENDRA_ANSWERING_ENABLED`, answer
model, retrieval, answer-timeout, or `KENDRA_PIPELINE_GIT_REVISION` settings to `api`.
`ollama-model-loader` pulls only the embedding model, not the configured answer model. Thus the
reference Compose deployment does not activate the M10 collaborators. The routes are present,
but an unconfigured question path fails closed rather than providing an accepted answering
service.

## 8. Decisions and constraints to preserve

### Binding product and evidence constraints

- Build evidence retrieval and verification, not an authority-deciding chatbot.
- Never claim currentness, legal meaning, applicability, eligibility, procurement action, or
  approval from model output.
- API code constructs citations from server-owned metadata; the model receives opaque evidence
  IDs only.
- Preserve one-based physical-page identity end to end.
- Abstain on missing, conflicting, below-threshold, unavailable, stale, invalid, or
  non-resolvable evidence.
- Treat document content as untrusted evidence, never instructions.
- Keep the first implementation a modular monolith; no Kubernetes, microservices, cloud
  routing, external models, observability platform, background watchers, or NAS coupling.

### Evaluation and experiment constraints

- Parser success and text volume are not extraction-completeness evidence.
- Freeze thresholds, candidate sets, decision rules, and scoring before inspecting results.
- Never weaken a gate after seeing results; write a new ADR/preregistration and preserve the old
  result.
- Do not relabel failed or inconclusive experiments as passed.
- `evaluation/gold_cases.json` remains `initial_expert_review_required` until attributable
  expert review and adjudication are complete.
- Generated runs and review worksheets belong under ignored `evaluation/runs/`.

### Git and artifact constraints

- Never commit source PDFs, OCR/extracted text, run evidence, generated reports, databases,
  vectors, model weights, caches, build output, volumes, `.env`, or secrets.
- Preserve failure commits, especially `3ce70b6`, `b6036ba`, and `288366f`; do not amend or
  rewrite them.
- Stage only explicit milestone paths. Do not include unrelated user work.
- Do not amend, push, or rewrite history unless the operator explicitly asks. The operator
  pushes.
- For a milestone handoff, report commit hash, committed files, checks, and final tree state.

### Constraints from this handoff session

- Only this Markdown handoff may be added; application code must not be modified.
- Repository claims must be verified from live Git/files/tests rather than remembered status.
- Existing uncommitted work belongs to the user and must remain untouched.

## 9. Setup, build, test, and deployment commands

Run from the repository root unless noted.

### Baseline and local configuration

```bash
cd /Users/mariacherrienakaya/Projects/kendra
git status --short --branch
git branch --show-current
git rev-parse HEAD
git log --oneline --decorate -15
git diff --stat
git diff --name-status

cp .env.example .env
mkdir -p document-repository intake
```

Replace the local PostgreSQL password in `.env`; never commit `.env`. If using an approved NAS
later, change the document-store host path only after its ownership, permissions, availability,
backup, and recovery boundaries are approved.

### Validate and build

```bash
docker --version
docker compose version
docker compose --env-file .env.example config --quiet
docker compose build
```

### Start, inspect, and stop

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=100 api web postgres qdrant ollama
curl -i http://127.0.0.1:8000/api/v1/health
docker compose down
```

Open `http://127.0.0.1:3000` for the current readiness UI. `docker compose down` retains named
volumes. Do not add `--volumes` unless intentional derived-data deletion is explicitly approved.

### Stage models and ingest one approved PDF

```bash
docker compose --profile ingestion-setup run --rm docling-model-loader
docker compose --profile ingestion-setup run --rm ollama-model-loader
docker compose up -d postgres qdrant ollama
docker compose --profile ingestion run --rm ingest approved-sample.pdf --manifest approved-sample.json
```

Before ingestion, set `KENDRA_PIPELINE_REVISION` to the exact Git commit being run and verify the
manifest contains the expected filename, SHA-256, physical-page count, approval scope,
provenance reference, and approved status.

### Backend tests

```bash
docker build --target test -t kendra-api-test ./apps/api
docker run --rm kendra-api-test
docker run --rm kendra-api-test python -m pytest -q -m milestone10
```

The live tier is intentionally separate and requires a running, correctly configured service
stack plus an ingested approved corpus:

```bash
cd apps/api
KENDRA_M10_LIVE=1 python -m pytest -m "milestone10 or milestone10_live"
```

Do not run the live tier against an unapproved corpus or treat hermetic contract success as a
passing experiment.

### Frontend tests

```bash
docker build --target test -t kendra-web-test ./apps/web
```

The test stage runs both `npm run typecheck` and `npm test`.

### Gold-dataset mechanical checks

These commands apply to the current uncommitted candidate tooling:

```bash
python3 scripts/validate_gold_cases.py evaluation/gold_cases.json
python3 scripts/validate_gold_cases.py evaluation/gold_cases.json \
  --manifest document-repository/approved-samples/APPROVAL_MANIFEST.json
```

Passing is mechanical validation only, never expert approval.

Generate reviewer packets only when an attributable review run is actually starting:

```bash
python3 scripts/prepare_m5_adjudication.py evaluation/gold_cases.json \
  evaluation/runs/M5-adjudication/<run-id>
```

The generator refuses to overwrite a non-empty packet directory.

## 10. Environment-variable names

No secret values are included here. `KENDRA_POSTGRES_PASSWORD` is required.
`KENDRA_QDRANT_API_KEY` is optional and secret when used.

### API/runtime settings

```text
KENDRA_ENVIRONMENT
KENDRA_LOG_LEVEL
KENDRA_API_HOST
KENDRA_API_PORT
KENDRA_CORS_ORIGINS
KENDRA_READINESS_TIMEOUT_SECONDS
KENDRA_POSTGRES_HOST
KENDRA_POSTGRES_PORT
KENDRA_POSTGRES_DATABASE
KENDRA_POSTGRES_USER
KENDRA_POSTGRES_PASSWORD
KENDRA_QDRANT_URL
KENDRA_QDRANT_API_KEY
KENDRA_OLLAMA_URL
KENDRA_DOCUMENT_STORE_ROOT
KENDRA_INGESTION_INTAKE_ROOT
KENDRA_DOCLING_ARTIFACTS_PATH
KENDRA_PDF_MAX_BYTES
KENDRA_PDF_MAX_PAGES
KENDRA_MINIMUM_PAGE_TEXT_CHARS
KENDRA_EXTRACTION_COMPLETENESS_POLICY
KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT
KENDRA_CHUNK_SIZE_CHARS
KENDRA_CHUNK_OVERLAP_CHARS
KENDRA_INGESTION_TOOL_TIMEOUT_SECONDS
KENDRA_EMBEDDING_MODEL
KENDRA_EMBEDDING_BATCH_SIZE
KENDRA_QDRANT_COLLECTION_PREFIX
KENDRA_PIPELINE_REVISION
KENDRA_ANSWERING_ENABLED
KENDRA_ANSWER_MODEL
KENDRA_ANSWER_TIMEOUT_SECONDS
KENDRA_RETRIEVAL_TOP_K
KENDRA_RETRIEVAL_SCORE_THRESHOLD
KENDRA_PIPELINE_GIT_REVISION
```

### Compose host bindings and paths

```text
KENDRA_API_BIND_HOST
KENDRA_WEB_BIND_HOST
KENDRA_WEB_PORT
KENDRA_DOCUMENT_STORE_HOST_PATH
KENDRA_INGESTION_INTAKE_HOST_PATH
NEXT_PUBLIC_KENDRA_API_BASE_URL
```

### Setup jobs, service internals, and tests

```text
HF_HOME
HF_HUB_CACHE
HF_XET_CACHE
OLLAMA_HOST
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
KENDRA_M10_LIVE
```

The `HF_*`, `OLLAMA_HOST`, and `POSTGRES_*` names are set internally by Compose for loader or
service processes; operators normally configure the corresponding `KENDRA_*` names. The
browser-visible `NEXT_PUBLIC_KENDRA_API_BASE_URL` is compiled into the web image and requires a
web rebuild after a change.

## 11. Known bugs, risks, TODOs, and unfinished work

### Blocking governance and evidence gaps

1. **Milestone status contradiction:** M10 code exists, while `CLAUDE.md`, EXP records, and
   milestone gates say M10 is blocked. Code presence is not acceptance.
2. **EXP-01 is not passed:** the ADR-007 rerun is inconclusive/failed under the frozen rule.
   Four facts were held by the gold-case page-scope defect; candidate v2 is mechanically fixed
   but not independently adjudicated.
3. **MF-01 remains unresolved:** OCR retained the circular header as `177-2024` where the
   rendered source reads `077-2024`; materiality and case impact need an attributable ruling.
4. **SF-01 OCR blind region:** ADR-007's detector yields zero material tokens across all 12
   scanned pages, so omission/substitution detection is vacuous there. A recorded measurement
   found an 8.8% digit-substitution floor and two fabrications; ADR-008/009 remain proposed.
5. **EXP-03 failed:** no page-bounded chunk policy passed the conjunctive table-context gate.
   EXP-02 and accepted retrieval configuration remain blocked.
6. **EXP-02, EXP-04, and EXP-05 have not passed:** retrieval parameters, answer model, and
   grounding mode are engineering defaults/prototypes, not selected configurations.
7. **EXP-07 identifier collision:** architecture reserves EXP-07 for offline-build validation,
   while an OCR preregistration draft also uses EXP-07. Resolve before freezing either plan.
8. **ADR-008, ADR-009, ADR-010, and ADR-011 are proposed, not accepted or activated.** The MVP
   specification remains frozen.

### Implementation and deployment gaps

1. **ADR-007 is not wired through reference Compose.** The active container default can remain
   the older failed `native-page-token-coverage-v1` policy.
2. **M10 is not wired through reference Compose.** Answering settings and pipeline Git revision
   are absent; the answer model is not staged.
3. **Claim support is not mechanically verified.** The M10 validator checks evidence identity,
   not claim/excerpt entailment or exact containment. ADR-010 proposes the fix.
4. **README/CLAUDE/tests documentation is stale.** It says question answering is unavailable and
   the project is at M9, while prototype routes/code exist. Update only after governance decides
   how the prototype is classified.
5. **The M10 live tier is unverified in this snapshot.** It needs a running stack, approved
   ingested corpus, correctly staged answer model, and explicit configuration.
6. **No authentication, authorization, audit enforcement, confidential-data control, production
   backup/recovery, NAS deployment, or multi-user isolation exists.** These are explicit
   deferrals, not minor TODOs.
7. **Fresh frontend image rebuild was inconclusive in this verification.** Docker Hub metadata
   for `node:24-bookworm-slim` timed out twice. The web tree is unchanged since `250f111`, and
   the existing local image passed typecheck and two unit tests, but a fresh build should be
   rerun when registry access is healthy.

### Known diagnostic/scoring defects

- The fact scorer builds its join blob in first-occurrence order rather than document order.
- It can match a digit-bearing token as a substring of a corrupted token, which allowed MF-01
  to escape.
- The approximately 34.5x Docling occurrence duplication on RMC 03-2024 page 1 is not
  root-caused. Docling no longer retains text under ADR-007, but the defect remains evidence
  about detector reliability.
- No active mechanism detects Poppler omission of non-digit material content.

### Current human work

- Review both independent M5 v2 worksheets blindly.
- Record Reviewer A/B qualifications, locked worksheet hashes, and adjudicator authority.
- Resolve MF-01, page-scope semantics, all reviewer disagreements, and whether corrections
  require a v3 dataset.
- Preserve the candidate and raw worksheets by hash; keep raw review data in ignored
  `evaluation/runs/`.

## 12. Exact recommended starting point for Milestone 11

The first Milestone 11 task should be a **gate-resolution package, not interface code**.

### Step 1 — preserve and finish the current M5 candidate work

1. Re-run both mechanical validators from Section 9.
2. Confirm with the owner that the current nine pre-existing working-tree paths are the
   intended v2 candidate package.
3. Generate a new ignored adjudication run directory.
4. Obtain two independent, qualified reviews and an attributable adjudicator decision.
5. Promote, revise to v3, exclude, or reject cases based on that decision. Do not let mechanical
   validation promote the dataset.

### Step 2 — close the experiment chain in order

1. Resolve MF-01 and select/accept an OCR-fidelity design (or narrow supported document classes)
   through a frozen ADR/preregistration.
2. Rerun EXP-01 against the adjudicated dataset and preserved rendered originals. It must pass;
   do not relabel prior runs.
3. Rerun EXP-03 with a preregistered table/region-aware representation. It must pass before
   retrieval selection.
4. Run/freeze EXP-02 retrieval configuration.
5. Resolve the EXP-07 naming collision and accept or reject ADR-010; freeze and run EXP-04 and
   EXP-05 as applicable.
6. Reconcile the M10 milestone record, `CLAUDE.md`, README, settings, model staging, and Compose
   wiring. Run the live M10 contract only against the approved corpus.

### Step 3 — settle the M11 interface contract before code

Review ADR-011. Until it is accepted and the MVP specification is explicitly unfrozen, edited,
reviewed, and re-frozen, the M11 interface must stay within the frozen surface:

- question input using the existing `question` and `collection_id` request only;
- answer status, claims, citations, limitations, and exact abstention display;
- open the preserved PDF through `GET /api/v1/documents/{version_id}/content` at the cited
  physical page;
- visibly label OCR-derived excerpts and make the original page the verification target;
- no browser upload;
- no Quick/Deep modes;
- no document-selection request field; and
- no numeric relevance score, percentage, bar, colour scale, or confidence display.

If ADR-011 is later accepted, document selection may only narrow the active generation; modes
may describe latency/breadth but not accuracy; browser upload must preserve a recorded approval
attestation; numeric relevance score remains rejected unless a separate decision authorizes it.

### Step 4 — implement the smallest M11 slice and run EXP-06

Only after Steps 1–3 are complete, implement the evidence-inspection UI against the existing API
and source-content endpoint. Add no new backend surface unless the accepted contract requires
it. Then run EXP-06: every supported citation must resolve to the exact checksum-verified source
and intended one-based physical page, and unresolved citations must fail closed. Milestone 11
does not pass unless EXP-06's 100% gates pass.

## 13. Verification performed for this handoff

Verified on 2026-08-24 before saving this file:

| Check | Result |
|---|---|
| Git branch/HEAD/upstream/main/remote and full status | Verified; values recorded in Section 2 |
| Milestone history and per-commit file changes | Verified with `git log`, `git show --stat`, and commit-range diffs |
| Compose resolution | `docker compose --env-file .env.example config --quiet` passed |
| Gold candidate mechanical validation | Passed: 9 documents, 41 pages, 50 cases, 125 facts, 40 supported, 10 unsupported; expert adjudication still required |
| Gold candidate versus approved local manifest | Passed; manifest checked by SHA-256 and document/page metadata |
| Whitespace/conflict check | `git diff --check` passed for the pre-existing work |
| Backend image build | Passed |
| Default backend suite | 53 passed, 41 deselected |
| Hermetic M10 contract | 35 passed, 6 live tests skipped, 53 deselected |
| Fresh frontend test-image build | Inconclusive: base-image registry metadata timed out twice |
| Existing-image frontend typecheck | Passed; web tree is unchanged since `250f111` |
| Existing-image frontend unit tests | 2 passed |
| Live Compose health and live M10 corpus tests | Not run; no runtime-readiness claim is made |

After saving, re-run:

```bash
git diff --check -- KENDRA_MIGRATION_HANDOFF.md
git status --short --branch
```

The expected final change from this task is only untracked `KENDRA_MIGRATION_HANDOFF.md`, in
addition to the nine pre-existing modified/untracked paths recorded in Section 2.
