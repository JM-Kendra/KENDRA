# EXP-08 (claimed, draft, not frozen) — model comparison on facts-in-context-but-abstained cases

**Status:** DRAFT. **Claimed, not frozen, not a registration.** Written per the
requester's instruction; not run. It becomes a real registration only after
every item in *Requires before freezing* is satisfied, checksummed **before
either candidate is run**.
**Drafted:** 2026-09-01. **Renamed from `EXP-04_PREREG_DRAFT.md` on 2026-09-01**
after `EXP-04` was found to already name a different, broader experiment (Local
Qwen model selection, `docs/EXPERIMENT_PLAN.md` Section 6). This experiment feeds
that experiment's model-selection question — a narrow signal about whether model
size explains specific generation-side abstentions — rather than replacing or
substituting for it. See `docs/EXPERIMENT_PLAN.md`'s new registration note
(Section 9) for the claim record.

> ## A second identifier collision — also unresolved, read this first
>
> **`EXP-08` is also already taken.** `docs/ARCHITECTURE.md`'s experiment table
> (row `EXP-08`) reserves it for *"Is publication atomic across PostgreSQL and
> Qdrant?"* — generation-publication transactionality and reconciliation,
> completely unrelated to model comparison. This draft was renamed to `EXP-08` on
> explicit instruction; the rename does not resolve this collision, it documents
> it, following the same precedent applied to the `EXP-04` collision this draft
> previously recorded (and matching this project's existing, still-open `EXP-07`
> collision: `EXP-07-preregistration-draft.md`'s OCR-render question vs.
> `ARCHITECTURE.md`'s "is the build offline" `EXP-07`).
>
> Checked before writing this: `EXP-09` and `EXP-10` are also reserved in
> `ARCHITECTURE.md`'s table ("Are parser limits adequate for hostile input?" and
> "Does the storage abstraction survive a mount change?", respectively).
> **`EXP-11` is the first number with no hit anywhere in tracked docs** as of this
> date — the candidate for reassignment if the reviewer wants a collision-free
> identifier rather than a recorded one.

## 1. Question and decision

**Does a larger local model answer the gold cases where `qwen2.5:7b-instruct`
abstained despite every required fact already being present in the retrieved
context — restricted to the subset Stage 0 (Section 4) confirms are genuinely a
model decision to abstain, not a gate rejection or a schema-parsing failure —
without introducing new false answers on the cases that were correctly handled
or on the unsupported stratum?**

Produces: a reviewed decision record (once registered under whichever identifier
the collision above resolves to) stating whether model size, on this narrow
evidence, plausibly explains the generation-side abstentions
`evaluation/M12_FINDINGS.md` part (d) found — or whether it does not, and the
cause lies elsewhere (prompt construction, decoding settings, or the answering
contract itself). It does **not** select a production model. See Section 8.

## 2. Frozen candidate matrix

| Candidate | Model | Selectable |
|---|---|---|
| `B0_BASELINE` | `qwen2.5:7b-instruct` (already pinned as this deployment's default `KENDRA_ANSWER_MODEL`) | No — reference only, reproduces the abstentions under study |
| `B1_LARGER` | **proposed:** `qwen2.5:14b-instruct` — same model family and prompt/instruction lineage as the baseline, differing only in parameter count, minimizing confounds from switching model families. **Not yet confirmed by the reviewer; must be pinned by exact tag and digest before freezing (Requires-before-freezing item 2).** | Yes, pending confirmation |

`B0` is never selectable — it is the configuration whose abstentions are under
study, matching the convention `EXP-05-preregistration-draft.md` §2 uses for its
own non-selectable baseline.

## 3. Input contract — frozen candidate case set

**Exactly these 7 case IDs, no more, no fewer, going into Stage 0:**
`KND-M5-CD-004`, `KND-M5-CD-005`, `KND-M5-DF-005`, `KND-M5-DF-008`,
`KND-M5-DF-009`, `KND-M5-DF-017`, `KND-M5-DF-020`.

This is the "facts in context, model abstained anyway" set from
`evaluation/M12_FINDINGS.md` part (d) — established by a prior, independent,
read-only diagnostic that never ran `B1_LARGER` and could not have been shaped by
its results. Using this set here is not evidence-after-the-fact selection for
*this* experiment: which cases belong to it was fixed before `B1_LARGER` was even
proposed as a candidate. **Stage 0 (Section 4) narrows this 7-case set further,
by classification, before Stage 1's model comparison (Section 6) ever runs.**

**Plus, unconditionally, as a non-regression check on Stage 1:** all 10
`deliberately_unsupported` cases (`KND-M5-UN-001` through `KND-M5-UN-010`) and
the 36 gold cases *not* in the 7-case set above and *not* among the 13 false
negatives this run's `M12_FINDINGS.md` already accounts for. A larger model that
fixes some of the 7 but breaks previously-correct cases, or answers an
unsupported case falsely, has not demonstrated anything this experiment would
credit — see Section 7.

**Excluded, deliberately, from Stage 0 and Stage 1 alike:** the 6 other false
negatives from the same run (`KND-M5-CD-006`, `KND-M5-CD-009`, `KND-M5-CD-010`,
`KND-M5-DF-012`, `KND-M5-LT-003`, `KND-M5-LT-007`) — those have a documented
content-availability gap (a cross-document retrieval limit or a chunk-density
miss, see `M12_FINDINGS.md` part (e)), not a generation decision, so a larger
model cannot be expected to answer them correctly from the same retrieval
output, and scoring them here would conflate a retrieval problem with the
generation question this experiment asks. And `KND-M5-UN-002` — its defect
(temporal-boundary overclaiming, part (a)) is a different failure mode than
abstention-despite-evidence and is tracked separately as a proposed
verification-contract rule, not a model-comparison question.

## 4. Stage 0 — diagnostic classification (read-only, in-process, no audit persistence)

**Purpose.** From outside the answering contract, all 7 candidate cases look
identical: `response_status: "insufficient_evidence"`, zero citations. That
conflates three genuinely different loci in
`apps/api/src/kendra_api/answering/service.py`'s `_run_pipeline`, and Stage 1's
model comparison only makes sense for one of them. Stage 0 re-runs the *current*
baseline (`qwen2.5:7b-instruct`) with real generation against each case's frozen
evidence packet and records exactly where each one actually resolves, before any
larger model is considered.

**Mechanism — must be exactly this:**

1. **In-process, not through the API.** Calls
   `kendra_api.answering.service.answer_question()` directly in a Python
   process — never an HTTP request to a running `api` container, and never
   through `scripts/run_gold_evaluation.py` / `kendra_api.evaluation.run`'s HTTP
   evaluation client. This is the same pattern
   `apps/api/src/kendra_api/evaluation/fake_model.py` already uses for the
   hermetic M12 test tier, substituting a real model for its scripted one.
2. **Reconstructed context, not live retrieval.** The `retriever` argument is a
   static, in-memory stand-in (the same shape as `fake_model.py`'s
   `_StaticRetriever`) seeded with exactly the evidence chunks
   `M12_FINDINGS.md` part (d)'s diagnostic already captured for each of the 7
   cases — no live Qdrant query, no live embedding call, so retrieval variance
   is not a confound here either.
3. **Real generation.** The `model` argument is the real `OllamaAnswerModel`,
   pointed at the live Ollama instance's `qwen2.5:7b-instruct` — the one part of
   the pipeline Stage 0 does not fake, since the point is to see the model's
   actual raw output given context already confirmed sufficient.
4. **Real admission, in-memory audit only.** The `registry` argument is the real
   `PostgresSourceRegistry` (read-only `SELECT`s against
   `document_versions`/`index_generations`; the evidence's `version_id`s are
   real, already-ingested corpus rows, so admission is exercised faithfully, not
   faked). The `audit` argument is `InMemoryAuditSink`
   (`apps/api/src/kendra_api/audit/sink.py`, already used by the hermetic
   tier) — this satisfies `answer_question()`'s own hard invariant that every
   call writes exactly one audit record before returning, but that record lives
   only in Stage 0's own process memory and is discarded on exit. **Nothing is
   written to the real Postgres `question_audit` table.** Stage 0's harness must
   not construct or hold a `PostgresAuditSink`.
5. **Read-only otherwise.** No `INSERT`/`UPDATE` anywhere; no ingestion, no
   schema change, no collection mutation.

**Capture per case**, written to
`evaluation/runs/EXP-08/<run-id>/stage0_cases.jsonl` (git-ignored under the
existing `/evaluation/runs/` rule — no new ignore entry needed):

- `case_id`
- `raw_model_output` — the exact string `model.generate()` returned, before
  `_parse_model_output` touches it
- `schema_valid` — whether `_parse_model_output(raw_model_output)` returned a
  payload (`true`) or `None` (`false`)
- `gate_decision` — the specific `_run_pipeline` branch reached (e.g.
  `"insufficient_evidence_from_model"`, `"claim_missing_text"`,
  `"claim_unknown_evidence_id"`, `"claims_empty_or_oversized"`,
  `"schema_invalid"`, `"admission_failed"`) and, where applicable, which
  claim/evidence_id triggered it
- `final_status` — the `AnswerOutcome.response.status` that would reach a caller
- `classification` — one of `model-abstained` / `gate-rejected` /
  `schema-invalid` / `other` (see mapping below)

**Classification mapping, frozen:**

| Path through `_run_pipeline` | `classification` |
|---|---|
| Model's own JSON has `status: "insufficient_evidence"` | `model-abstained` |
| Model's JSON has `status: "supported"` with claims, but is discarded (empty/oversized claim list, a claim missing `text` or `evidence_ids`, an `evidence_id` not in the admitted set) | `gate-rejected` |
| `_parse_model_output` returns `None` (not valid JSON, not a dict, or missing/misshaped `status`/`claims`/`limitations`) | `schema-invalid` |
| `status: "conflicting_evidence"`, or every candidate fails `_admit` | `other` — recorded faithfully, not forced into the three requested buckets |

**Updated decision rule — Stage 1 (Section 6, the `B0` vs `B1_LARGER`
comparison) runs only on whichever of the 7 cases Stage 0 classifies
`model-abstained`.** A case Stage 0 classifies `gate-rejected` or
`schema-invalid` is not a model-choice question: a bigger model cannot be
credited for fixing a gate rejection or a JSON-parsing failure that has nothing
to do with willingness to answer. Those are recorded as their own finding,
separate from the model-comparison question, and are explicitly out of Stage
1's scope — carried forward for a different kind of fix (a schema-validity
check, or the gate's own claim-validation logic), not a bigger model. **If Stage
0 finds zero cases classify `model-abstained`, Stage 1 does not run at all, and
this draft's hypothesis (Section 1) is void by construction, not failed** — see
Section 9.

## 5. Controlled variables (Stage 1)

Retrieval configuration (`top_k=8`, `score_threshold=0.5`), the frozen retrieved
evidence packet already captured for each Stage-0-qualified case (re-retrieval is
not repeated per candidate — this removes retrieval variance as a confound
entirely), the `bge-m3` embedding model, the ADR-007
`native-primary-detection-v1` extraction policy under which the corpus was
ingested, decoding temperature `0` (the answering client's only currently-set
decoding option — no seed is recorded in
`apps/api/src/kendra_api/answering/model_client.py` as of this draft; if `B1`'s
serving path exposes one, Requires-before-freezing item 3 pins it), per-request
timeout, concurrency of one, and the source revision the corpus was ingested and
this diagnostic was run under (`0bcc9dd7d0aaf7bd370e8d3eb60303a42e8ef91c`). Only
the answer model varies between `B0` and `B1_LARGER`.

**Why the evidence packet is frozen rather than re-retrieved per candidate:**
this experiment's question is specifically about generation given
known-sufficient context, not about whether a larger model's own
embedding/retrieval behavior differs (it wouldn't — both candidates use the same
`bge-m3` retriever regardless of answer-model size; retrieval and generation are
separate components, and only the model is swapped between candidates here).
Freezing the packet also makes the comparison exactly about the qualifying
cases' documented context, eliminating any possibility that a retrieval-side
difference gets misread as a generation-side one.

## 6. Procedure

1. Run Stage 0 (Section 4) against `B0_BASELINE` for all 7 cases in Section 3.
   Record every case's classification.
2. Confirm and pin `B1_LARGER`'s exact tag and digest (Requires-before-freezing
   item 2).
3. For each case Stage 0 classified `model-abstained`, replay the exact frozen
   evidence packet (same chunks, same order, same claim-eligible evidence IDs)
   through `B1_LARGER` via the same in-process mechanism Stage 0 used, without a
   live retrieval call.
4. Run `B1_LARGER` against the full 50-case gold set live (real retrieval, not
   the frozen packet) for the non-regression check in Section 3, under the same
   `top_k`/`score_threshold`/corpus as the run this draft is based on.
5. Record `status`, `claims`, `citations`, `duration_ms`, and any error for every
   case, both frozen-packet and live runs, exactly as `CaseRunResult` already
   does.
6. Score per Section 7. No case is retried, averaged, or best-of-N selected.

## 7. Scoring rule — frozen

**On the Stage-0-qualified cases (frozen-packet run):** a case counts as
**answered** only if `status == "supported"` and every one of that case's
`expected_answer_facts` is judged present by a human reviewer reading the
model's claim text against the fact — the same mechanical-scoring distrust this
project applies everywhere else (`docs/EVALUATION_METHOD.md`;
`M12_FINDINGS.md` part (c)) applies here too: no substring/token-overlap
auto-scorer decides this. A case that returns `supported` with an incomplete or
incorrect claim does not count as answered; it counts as a new defect, recorded,
not credited.

**On the non-regression set (live run):** every one of the previously-correct
gold cases must retain its prior classification and pass answer correctness
unchanged; every one of the 10 unsupported cases must return
`insufficient_evidence` (or another safe rejection status) with no false answer.
Any regression here is recorded regardless of how `B1_LARGER` performs on the
qualified cases.

## 8. Decision rule — frozen

Let **N** be the number of cases Stage 0 classifies `model-abstained` (N ≤ 7).

- **If N = 0:** this draft's hypothesis is void by construction. Stage 1 does not
  run. Recorded as such, not as a failure.
- **If N = 1:** `B1_LARGER` supports the hypothesis only if it answers that one
  case. No misses are tolerated at N = 1 — "allow one miss" would be vacuous at
  this size.
- **If N ≥ 2:** `B1_LARGER` supports the hypothesis only if it answers at least
  N − 1 of the N qualified cases (the same "at most one miss" tolerance as the
  original 6-of-7 threshold, generalized to whatever N Stage 0 actually
  produces).

**In every case, the non-regression set (Section 7) must show zero regressions
and zero new unsupported false answers**, regardless of N or how many qualified
cases `B1_LARGER` answers. A regression fails the hypothesis outright.

If the threshold above is not met, or a regression occurs, the hypothesis is not
supported on this evidence: the abstentions are not explained by model size
alone, and the generation-side question from `M12_FINDINGS.md` parts (b)/(d)
remains open for a different kind of investigation (prompt wording, the
answering contract's own instruction text, or decoding configuration).

**This is not a model-selection decision either way.** A pass here does not
authorize deploying a larger model, does not touch `KENDRA_ANSWER_MODEL`, and
does not substitute for `EXP-04`'s actual defined scope (schema validity,
unknown-ID rejection, latency and memory ceilings) — that experiment is
unaffected by this one and must still be run for real on its own terms.

## 9. What this would and would not establish

A pass would establish only that, on the Stage-0-qualified cases' already
sufficient context, a larger same-family model answers where the smaller one
abstained, without regressing the rest of the gold set. It would **not**
establish:

- that model size is the *only* variable that matters — prompt wording and
  decoding configuration are not varied here and remain untested;
- anything about the 6 cases excluded in Section 3, or the cases Stage 0
  classifies `gate-rejected`/`schema-invalid`/`other` — those have a
  documented or distinct cause, not a "model chose to abstain" one;
- anything about `KND-M5-UN-002`'s temporal-boundary defect (part (a)) — a
  different failure mode, tracked separately;
- a production model decision — see Section 8;
- that EXP-01, EXP-03, or Milestone 10 may proceed. All three remain blocked
  regardless of this experiment's outcome, per `docs/milestones/M12_STATUS.md`.

## 10. Failure behavior

A failed or inconclusive run is recorded, not repaired or rerun with softened
criteria. If Stage 0 cannot complete for a case (model unavailable, timeout), that
case is recorded as incomplete with its cause and excluded from N — it is not
counted as any of the three classifications. If `B1_LARGER` cannot be obtained
or run locally (model unavailable, resource exhaustion, timeout), the Stage 1
attempt is recorded as incomplete with its cause; an incomplete run is not
evidence for or against the hypothesis.

## Requires before freezing

1. **A collision-free (or explicitly accepted-as-colliding) identifier
   confirmed** by the reviewer — `EXP-11`, or an explicit decision to keep
   `EXP-08` with the collision recorded rather than avoided. Not decided by this
   draft.
2. **`B1_LARGER` pinned by exact tag and digest**, and its decoding
   configuration (temperature, and a seed if its serving path exposes one)
   recorded here before any run.
3. **Stage 0's harness implemented.** Nothing described in Section 4 exists as
   code yet — no script builds the `_StaticRetriever`-equivalent, wires
   `InMemoryAuditSink`, or writes `stage0_cases.jsonl`. This draft specifies the
   contract Stage 0's implementation must satisfy; it does not implement it.
4. **Reviewer confirmation that replaying a frozen evidence packet through a
   different answer model is methodologically acceptable** for this narrow
   question, given `EXP-05-preregistration-draft.md`'s own caution (§3) about
   not letting an easy pass substitute for a harder, more representative test.
5. **Local resource check** — running a 14B-class model locally alongside the
   existing stack (Postgres/Qdrant/Ollama, `qwen2.5vl:7b` already resident on
   this workstation's native Ollama instance) fits available VRAM/RAM without
   destabilizing required services. Not yet checked.
6. **No answering behavior, prompt, or gate threshold changed** to make this
   run possible — per the requester's own instruction for this draft. If
   running `B1_LARGER` (or Stage 0 itself) through the existing contract
   requires such a change, that need is recorded and freezing waits on its own
   review, not folded in silently.
