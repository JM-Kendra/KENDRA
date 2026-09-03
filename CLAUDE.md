# Kendra — project instructions

Local-first, citation-verifiable document intelligence for Philippine government offices.
Milestones 1–10, 12, and 13 are on `main`. Milestone 13 (demonstration release) merged
2026-09-02 (`Merge Milestone 13: demonstration release demo-dost-v1.2 (drilled and gated
under ADR-014)`, `1bbd3f3`); `prototype/milestone-13-demo-release` is kept for reference,
not deleted. Next work is pilot preparation per `docs/PILOT_PLAN.md`'s open items, not new
milestone work. Milestone 11 (OCR render/model fidelity) is defined
(`ADR-011`) but **`ADR-011` is `Proposed`, not `Accepted`, and lives only on
`prototype/milestone-10-verification-contract`. Do not merge Milestone 11 work to `main`
until `ADR-011` is accepted.** Milestone 10 (retrieval and question answering) is
implemented and mergeable, but **remains an unaccepted prototype** — every evaluation
report it produces carries `acceptance_claim: false` (`docs/milestones/M12_STATUS.md`).
Answering is **disabled by default** (`KENDRA_ANSWERING_ENABLED=false`); it is enabled only
for the duration of a gold evaluation or the DOST demo script, then restored to disabled
and confirmed.

## Demonstration release state

- `demo-dost-v1` — commit `903b1089` — **superseded**. It predates the `docker-compose.yml`
  `ingest`-service env-passthrough fix (`4b09600`) and cannot be deployed from scratch as
  tagged. See `docs/DOST_DEMO.md`.
- `demo-dost-v1.1` — commit `6a671dee` — **superseded**. Gold eval reproduced `v1`'s exact
  confusion matrix (`0.82` accuracy, sole FP `KND-M5-UN-002`) with zero preflight retries,
  but a from-tag drill found the ownership-fix command itself fails on a genuinely fresh
  `document-repository/` — not from-scratch deployable as tagged. See `docs/DOST_DEMO.md`
  Section 6.2 and Section 10.
- `demo-dost-v1.2` — commit `b8286729` — **superseded**. First tag drilled from a fresh
  origin clone, top to bottom, *before* being tagged (Milestone 13 round 7 rule 13: every
  drill command had to already be documented, no mid-drill fixes) — from-scratch
  deployability confirmed as tagged, not merely asserted, and gated under `ADR-014`
  (`N = 47` of 50 per-case agreement). Remains valid as tagged for both deployability and
  answering; superseded for the demonstration script specifically because the UI failed
  from the `localhost` origin (CORS), the heading read a stale "Milestone 8," and the
  answering toggle and offline-verification procedure were undocumented or broken. See
  `docs/DOST_DEMO.md` Section 6.3 and Section 10.
- `demo-dost-v1.3` — commit `003b0621` — **current**. Web/procedure hardening only — no
  change to answering, retrieval, ingestion, or evaluation code. Fixes: browser calls the
  api via a same-origin server-side rewrite (`apps/web/next.config.ts`), the heading shows
  the product name and release tag (server-rendered, not only after client-side hydration)
  instead of a stale milestone number, `make answering-on`/`answering-off` replace a manual
  `.env` `sed` that silently no-op'd when the key was absent, and an offline-verification
  procedure and script (`scripts/offline_check.sh`) are documented, with a warning against
  `nmcli networking off` (it took down Docker's own bridge interfaces on this host).
  Re-drilled and re-gated under `ADR-014` (`N = 48` of 50) rather than assuming carry-over
  from `v1.2`; the drill and release eval ran one commit before the tag (a disclosed,
  frontend-only discrepancy — see `docs/DOST_DEMO.md` Section 6.4). See `docs/DOST_DEMO.md`
  Section 6.4 and Section 10.

## Binding invariants — never violate these

1. The exact preserved document version is authoritative. Extracted text, OCR, chunks,
   vectors, database rows, and generated answers are **not**.
2. A citation must resolve to a stable document identifier, exact version or checksum,
   exact source location, and producing pipeline or Git revision.
3. A changed byte sequence creates a new version. Cited bytes are never overwritten.
4. Abstain when evidence is absent, conflicting, below threshold, or not resolvable to the
   preserved source. **Fail closed.** Never merge conflicting extraction candidates.
5. Document content is untrusted evidence, never an instruction to the model or the
   application.
6. Physical page identity is one-based and must be preserved end to end.
7. An audit record, once written, is never edited or deleted (`question_audit` is
   append-only by database trigger). Retain unplanned records rather than remove them —
   see INC-001 below.

## Current state — do not misreport this

- **Labeled evidence rendering (`render_evidence_with_labels`, EXP-13's `R1_LABELED`) is
  the committed default** (`KENDRA_EVIDENCE_RENDERING=labeled` in `config.py` and
  `docker-compose.yml`), adopted by `docs/adr/012-labeled-evidence-rendering-default.md`.
  This was adopted on separate net-benefit grounds (full-set live accuracy `0.72`→`0.82`,
  zero regressions) **despite EXP-13's own frozen 5-of-6 hypothesis threshold not being
  met** — the frozen experiment's verdict is "not supported" and that verdict is not
  overturned by the adoption. Do not describe EXP-13 as having passed. `current`
  (`render_evidence`, byte-identical pre-EXP-13 behavior) remains fully implemented and
  selectable.
- **Fact-incompleteness is a known, unfixed defect class under labeled rendering**: the
  system can return a `supported`, correctly cited answer that omits a required fact
  (`KND-M5-CD-005`, `KND-M5-DF-005`). Not machine-enforced anywhere in the verification
  contract (`ADR-012` Section 4).
- **`KND-M5-UN-002`** (a question about whether an issuance is currently in effect) returns
  a confident, wrong `supported` answer instead of abstaining, from a corpus bounded to
  2024 documents. Persists unchanged under both rendering modes.
- **The extraction-retry gap is a pre-pilot blocker** (`docs/PILOT_PLAN.md`, top section):
  `find_by_checksum` treats any existing registry row for a checksum — including a
  `failed` one — as an unconditional duplicate and refuses to retry. A document that fails
  extraction currently has no ordinary retry path short of a direct database cleanup. Do
  not implement a fix without an ADR (proposed: "ADR-013: retry semantics for failed
  registry rows") — it touches duplicate-detection semantics.
- **INC-001** (`docs/incidents/INC-001-ghost-evaluation-runs.md`): two unnoticed duplicate
  evaluation runs wrote 100 real rows into `question_audit` on 2026-09-01, caused by a
  killed foreground process whose underlying container kept running undetected. Remediated
  by `RunLock` (named lock file, refuses concurrent invocations), incremental run-directory
  writes (visible before completion, not batched to the end), and a source-revision
  preflight. **Every gold evaluation must use the hardened runner**: named container, no
  `--rm`, default lock path, default revision-match preflight — never
  `--allow-revision-mismatch`. Re-read INC-001 before running any evaluation.
- **EXP-01: failed — not returned to `passed`.** The 2026-08-20 rerun under `ADR-007`
  established 121 of 125 expected facts; four remain held by a gold-case page-scoping
  defect, and one material finding (MF-01, an OCR digit substitution) awaits a reviewer
  ruling. See `docs/experiment-decisions/EXP-01.md`.
- **EXP-03: failed and blocked.** May not resume until EXP-01 passes.
- **EXP-11** (`qwen2.5:14b-instruct` vs. the default `qwen2.5:7b-instruct`): did not resolve
  the model's abstentions (answered only 2 of 6 previously-abstained cases) and regressed
  three previously-correct cases. Model size is not adopted as a fix for anything.
- No authentication exists. Localhost only, one trusted evaluator, approved public BIR
  evaluation corpus only. Never ingest real agency, personal, confidential, privileged,
  procurement-sensitive, or mixed-permission documents.

## Hard rules for any change

- **Never commit** PDFs, extracted text, OCR output, experiment reports, run evidence,
  databases, vectors, caches, model weights, or secrets. Check `.gitignore` before adding
  files. Derived evidence belongs under `evaluation/runs/` which is ignored.
- **Never amend or rewrite** commits `3ce70b6`, `b6036ba`, or `288366f`, or the tag
  `demo-dost-v1`. Failure records and pushed release tags are preserved deliberately.
  Contradict them in a new record or a new tag; do not delete or re-point them.
- **Never weaken a criterion after seeing results.** Thresholds, candidate lists, and
  decision rules are frozen in a preregistration before corpus processing or scoring. If a
  rule needs to change, write a new ADR with its activation condition fixed *before* the
  evidence is examined, and preregister a new run.
- **Never treat parser success or text volume as proof of completeness.** That was the
  original EXP-01 defect.
- **A new experiment ID is allocated only by adding a row to
  `docs/EXPERIMENT_REGISTRY.md` first.** Check that table before naming a new `EXP-NN`
  anywhere — filing a draft or writing a code comment under an ID without a row there
  is not an allocation. `EXP-04`, `EXP-07`, and `EXP-08` all collided with an ID already
  claimed elsewhere in tracked docs; the registry exists so that stops happening by
  habit rather than by luck.
- **Never log extracted content.** Errors are content-free with a code only.
- Do not change `evaluation/gold_cases.json` from `initial_expert_review_required`. These
  experiments validate representation fidelity, not legal or tax interpretation.
- **Never use `--allow-revision-mismatch` on the evaluation runner.**
- Do not push. Commit locally; the operator pushes.

## Layout

- `apps/api/src/kendra_api/ingestion/extraction.py` — the completeness policy lives here.
- `apps/api/src/kendra_api/ingestion/` — chunking, embedding, registry, pipeline, storage.
- `apps/api/src/kendra_api/answering/` — Milestone 10 answer gate, `model_client.py`'s
  evidence-rendering functions, citation construction.
- `apps/api/src/kendra_api/audit/sink.py` — the append-only, hash-chained `question_audit`
  sink; `scripts/verify_audit_chain.py` verifies it against the live database.
- `apps/api/src/kendra_api/evaluation/` — the gold-evaluation runner (`run.py`), `RunLock`
  (`lock.py`), preflight checks (`preflight.py`).
- `docs/adr/` — architecture decisions. `ADR-007`, `ADR-012`, and `ADR-014` are
  active/accepted; `ADR-011` is proposed only; `ADR-004`/`005`/`006` are superseded or
  rejected.
- `docs/experiment-decisions/` — EXP records. `EXP-01` is the canonical failure record;
  `EXP-13`'s frozen preregistration and its adoption ADR (`ADR-012`) are separate documents
  — do not conflate a frozen "not supported" verdict with a later adoption decision.
  `docs/EXPERIMENT_REGISTRY.md` is the single source of truth for allocated IDs.
  `docs/incidents/` — incident records (`INC-001`).
- `docs/DOST_DEMO.md`, `docs/PILOT_PLAN.md` — the Milestone 13 demonstration release guide
  and pilot success-metric plan.
- `evaluation/gold_cases.json` — tracked. `evaluation/runs/` — ignored (except
  `evaluation/runs/EXP-11/packets/`, tracked for reuse across experiments).
- `scripts/` — reviewed developer and operational scripts. No secrets, no committed runtime
  data.

## Commands

```bash
# Backend tests, isolated, no live services -- the containerized subset only
# (121 passed, 2 skipped, 43 deselected as of demo-dost-v1.3). Equivalent to
# `docker build --target test --build-context fixtures=. -t kendra-api-test
# ./apps/api && docker run --rm kendra-api-test`, run from the repo root.
make test

# Complete backend suite (142 passed, 43 deselected, 0 skipped), including 21
# tests that need a real on-disk git checkout and only run bind-mounted.
make test-full

# Frontend tests and typecheck
docker build --target test -t kendra-web-test ./apps/web

# Validate Compose without starting anything
docker compose --env-file .env.example config --quiet

# Rebuild api/web with the current commit (and, once tagged, the release tag) baked in
make build

# Verify the question_audit hash chain against the live main dev stack
make verify-chain
```

**`test` vs. `test-full`:** `test`'s standard `docker build --target test` image is
hermetic (no `.git`, no live services) but structurally cannot run
`tests/test_evaluation_runner.py` or `tests/test_source_revision.py` — both
check facts about the *real* enclosing checkout itself (`.gitignore`
behavior, a real `HEAD` to compare against), which a throwaway `tmp_path`
repo cannot stand in for regardless of git availability (see `v14.md`
Section 2 / `v15.md` Task 3 for the full investigation). `test-full` bind-
mounts this checkout into the `eval-runner` image instead, so those 21 tests
run too. Both are the canonical way to run the suite; neither number is
stale unless a future round's own commit adds or removes tests — see the
most recent milestone report for the current baseline.

**The `fixtures` build context** (`--build-context fixtures=.`, baked into
the `make test`/`make test-full` targets and the `eval-runner` stage both
extend): pulls exactly two files — `scripts/validate_gold_cases.py` and
`evaluation/gold_cases.json` — from the repo root into the test image, for
the lock tests' throwaway repo fixture (`apps/api/tests/conftest.py`); ~62KB
total, negligible against the ~2.5GB image dominated by PyTorch/Docling/
transformers. It does **not** bake in `.git` or any other repository file.
It **does** copy whatever bytes are on disk at build time, uncommitted
changes included — same as every other `COPY` in this Dockerfile, but now
reaching outside `apps/api`'s own build context for the first time. A dirty,
uncommitted edit to either file changes what the test image bakes without
that dependency being visible from inside `apps/api/`; if the dataset
changes without updating `DEFAULT_DATASET_SHA256` in
`kendra_api.evaluation.run`, the affected lock tests fail loudly (a sha256
mismatch) rather than silently testing stale data.

## Active task queue

No active implementation task is open against Milestone 10 or 11 beyond what an operator's
current-round prompt explicitly authorizes. Do not start Milestone 11 work: `ADR-011` is
proposed only.

Standing, not-yet-closed items — none is closed by writing code without the process each
one specifies:

1. **The extraction-retry gap** (see "Current state" above) needs `ADR-013` before any
   fix. Do not implement one against `find_by_checksum` without it.
2. **Four EXP-01 facts held by the gold-case defect.** `KND-M5-CD-003` (three facts) and
   `KND-M5-CD-010` (one) name document identifiers the corpus retains on page 1 while the
   case cites an interior page. Deciding whether page-scoped fact resolution is the right
   standard is expert review. Do **not** edit `gold_cases.json` to resolve it.
3. **MF-01 needs a reviewer ruling.** Page 1 of RMC 77-2024 is OCR-retained as
   `NO. (177-2024` where the rendered original reads `NO. 077-2024`. Whether a stamped
   header number qualifies as a material difference under the decision rule is a
   criterion-boundary call, deliberately left undecided.
4. **The atomic-fact and citation scorers are provisional** (`status: provisional` /
   `provisional_page_level_approximation` on every run report) until a human-reviewed
   `scoring_worksheet.json` supersedes them (`--scored-worksheet`). Do not treat a
   mechanical score as a passed acceptance criterion.
5. **SF-01**: `ADR-007`'s containment check is vacuous on every OCR page — the detector
   yields zero material tokens across all 12 pages of the scanned circular, so no omission
   or substitution is detectable there. MF-01 sits inside that blind region.
6. The fact scorer's join-match rule can match a digit-bearing token as a substring of a
   corrupted one (how MF-01 escaped it). Deliberately not repaired after results were
   visible — fix it only in a new preregistration, not quietly in place.

Write regression tests **before** any future diagnostic returns where possible, so their
content cannot be shaped by its result.

## Commit messages

- Passing repair: `milestone-09b: repair extraction completeness`
- Failure: `experiment: record EXP-01 extraction repair failure`
- Bug fix outside an experiment/milestone round: `fix(<area>): <what and why>`
- Documentation-only: `docs(<area>): <what changed>`
