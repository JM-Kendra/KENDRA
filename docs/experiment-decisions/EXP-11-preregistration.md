# EXP-11 — model comparison on facts-in-context-but-abstained cases

**Status:** **FROZEN, 2026-09-01, at commit `19192da8469f8ee0a8bdf1e791969056e8e3232d`.**
This is the frozen copy of `evaluation/EXP-11_PREREG_DRAFT.md` at that commit's
content, verbatim in Sections 1–10 below — nothing in those sections may be
reworded after this freeze, per this project's rule that criteria are locked
before evidence is examined. The pre-freeze draft remains at
`evaluation/EXP-11_PREREG_DRAFT.md` with a pointer to this file; it is not
deleted or redirected, so the drafting history stays visible.

**Amendment A1, recorded 2026-09-01** (see the end of this file, after Section
10, for its full text): corrects how Stage 0's evidence packets are sourced
(a persisted, one-time-captured file set, not live retrieval on every run) and
formalizes decoding seed as a controlled variable now that
`OllamaAnswerModel` sends one. Sections 1–10 remain verbatim and unreworded, as
required by the freeze above; Amendment A1 supersedes only the specific Section
4/5 mechanism details it names, additively. The Stage 0 run this freeze
originally covered (`20260901T014805Z-0bcc9dd7`) is marked superseded under A1
— retained, not deleted.

**Amendment A2, recorded 2026-09-01** (see the end of this file, after
Amendment A1, for its full text): defines a three-trial repetition scheme for
Stage 1's frozen-packet run — each of the 6 Stage-0-qualified cases, in each
arm, is run three times, and a case counts as "answered" only if all three
trials return `supported` with at least one valid citation. Per-arm flip rate
(how often a case's three trials disagree) is recorded as a byproduct, not a
scoring criterion. **Section 8's decision-rule threshold (N, N−1-of-N) is
unchanged** — A2 changes what "a case answered" means per Section 7's already-
qualitative scoring rule; it does not change how many of the N qualified cases
must be answered.

**What freezing this covers, precisely.** Stage 0 (Section 4) — its mechanism,
reproduction criterion, and classification mapping — is fully specified and its
harness (`apps/api/src/kendra_api/evaluation/stage0.py`) is implemented and
hermetically tested as of this commit. Freezing locks that specification before
Stage 0 is run against the live model, which is the point: the classification
rule cannot be adjusted after seeing which bucket a case lands in. **Stage 1
(the `B0` vs `B1_LARGER` comparison, Sections 5–8) is frozen in the same sense
— its scoring and decision rules may not be reworded after a candidate runs —
but three of its own prerequisites remain genuinely open, not satisfied by this
freeze, and are carried forward rather than silently marked done:**

| Original "Requires before freezing" item | Status at this freeze |
|---|---|
| 1. Registry entry confirmed current | **Satisfied.** `docs/EXPERIMENT_REGISTRY.md` lists `EXP-11` with no unresolved collision as of this date. |
| 2. `B1_LARGER` pinned by exact tag and digest | **Open.** Still only proposed (`qwen2.5:14b-instruct`), not pinned. Gates Stage 1 only — Stage 0 does not use `B1_LARGER` at all. |
| 3. Stage 0's harness implemented and its hermetic test passing | **Satisfied.** `apps/api/src/kendra_api/evaluation/stage0.py` and `apps/api/tests/test_stage0.py` exist and pass as of commit `19192da`. |
| 4. Reviewer confirmation on frozen-packet methodology | **Open.** Gates Stage 1 only. |
| 5. Local resource check for a 14B-class model | **Open.** Gates Stage 1 only. |
| 6. No answering behavior, prompt, or gate threshold changed | **Satisfied so far** — holds as of this freeze; remains a standing constraint on both stages going forward. |

**Consequence: Stage 0 may run under this frozen specification. Stage 1 may
not run until items 2, 4, and 5 above are separately satisfied and recorded.**
This freeze does not retroactively claim those three items are done — they are
listed open, deliberately, rather than swept into "frozen" as if satisfied.

---

The remainder of this document is Sections 1 through 10 of
`evaluation/EXP-11_PREREG_DRAFT.md`, copied verbatim at the commit named above.

## 1. Question and decision

**Does a larger local model answer the gold cases where `qwen2.5:7b-instruct`
abstained despite every required fact already being present in the retrieved
context — restricted to the subset Stage 0 (Section 4) confirms reproduce and
are genuinely a model decision to abstain, not a gate rejection, a schema-parsing
failure, or a non-reproducing result — without introducing new false answers on
the cases that were correctly handled or on the unsupported stratum?**

Produces: a reviewed decision record (once registered) stating whether model
size, on this narrow evidence, plausibly explains the generation-side
abstentions `evaluation/M12_FINDINGS.md` part (d) found — or whether it does
not, and the cause lies elsewhere (prompt construction, decoding settings, or
the answering contract itself). It does **not** select a production model. See
Section 8.

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
first by reproduction and then by classification, before Stage 1's model
comparison (Section 6) ever runs.**

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
miss, see `M12_FINDINGS.md` parts (b), (d), and (e)), not a generation decision,
so a larger model cannot be expected to answer them correctly from the same
retrieval output, and scoring them here would conflate a retrieval problem with
the generation question this experiment asks. And `KND-M5-UN-002` — its defect
(temporal-boundary overclaiming, part (a)) is a different failure mode than
abstention-despite-evidence and is tracked separately as a proposed
verification-contract rule, not a model-comparison question.

## 4. Stage 0 — diagnostic classification (read-only, in-process, no audit persistence)

**Purpose.** From outside the answering contract, all 7 candidate cases look
identical: `response_status: "insufficient_evidence"`, zero citations. That
conflates several genuinely different loci in
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

**Reproduction criterion — checked before classification.** Before a case is
sorted into any of the classification buckets below, Stage 0 must first confirm
that replaying `B0_BASELINE` against that case's frozen evidence packet
reproduces the same external outcome the M12 clean run
(`evaluation/runs/M12-gold/20260831T125331Z-0bcc9dd7`) recorded for it: a
`response_status` of exactly `"insufficient_evidence"`. All 7 candidate cases
had that exact status in the clean run (that is how they were selected into this
set in the first place; see Section 3), so reproduction here means: **does the
same status come back again**, on this replay, under the same settings.

**Settings, frozen and recorded here (not assumed):**

- **Decoding temperature: `0`.** The only decoding option
  `apps/api/src/kendra_api/answering/model_client.py`'s `OllamaAnswerModel`
  currently sets on every request.
- **No model-generation seed exists to match.** `OllamaAnswerModel` passes no
  `seed` parameter to Ollama; none is recorded anywhere in the current
  implementation. This is stated explicitly rather than inventing a seed value
  the code does not have. Temperature `0` narrows but does not guarantee
  bit-identical output across separate invocations (backend/GPU floating-point
  nondeterminism can still vary a run) — which is exactly why this criterion
  exists rather than being assumed.
- **The M12 clean run's `--seed 20260831` is not a model seed and is not
  replicated here.** It governs only the *case order* the original run
  processed cases in (`random.Random(seed).shuffle(ordered_cases)` in
  `kendra_api.evaluation.run`'s `_amain`). Stage 0 calls `answer_question()`
  once per case, directly, outside that shuffle loop; case order plays no role
  in a single case's generation and is not something Stage 0 needs to
  replicate.
- **Corpus and source revision:** the same ingested corpus and
  `0bcc9dd7d0aaf7bd370e8d3eb60303a42e8ef91c` source revision the clean run and
  the `M12_FINDINGS.md` part (d) diagnostic both used.

**If a case's replay does not reproduce `"insufficient_evidence"`** — the model
now returns `supported`, `conflicting_evidence`, or anything else — that case is
classified **`not-reproduced`** and skips the rest of Stage 0's classification
entirely. A nondeterministic base case cannot support a clean "model size
explains this" comparison: forcing a classification onto an unstable outcome
would misrepresent it as settled when it isn't, and comparing `B1_LARGER`
against a baseline result that doesn't even reproduce itself would not be a
meaningful comparison.

**Capture per case**, written to
`evaluation/runs/EXP-11/<run-id>/stage0_cases.jsonl` (git-ignored under the
existing `/evaluation/runs/` rule — no new ignore entry needed):

- `case_id`
- `reproduced` — whether this replay's `response_status` matched the clean
  run's recorded status for this case (`true`/`false`)
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
  `schema-invalid` / `other` / `not-reproduced` (see mapping below)

**Classification mapping, frozen — and corrected against the real code, not
assumed.** `_run_pipeline`'s branches do not all return the same external
status; only some of them return `"insufficient_evidence"`, which is the only
status that can satisfy this reference set's reproduction criterion at all.
This was checked directly (`apps/api/tests/test_stage0.py`'s
`test_scripted_schema_invalid` first assumed the opposite and had to be
corrected) rather than assumed from the branch names:

| Internal branch | External status | Reachable when reproduced=true? | `classification` |
|---|---|---|---|
| Admission fails entirely, no unresolved source | `insufficient_evidence` | Yes | `other` |
| Admission fails entirely, with an unresolved source | `source_unavailable` (503) | **No** | n/a — always `not-reproduced` |
| `model.generate()` raises | `system_error` | **No** | n/a — always `not-reproduced` |
| `_parse_model_output` returns `None` (schema invalid) | `system_error` | **No** | n/a — always `not-reproduced` |
| Model's own JSON has `status: "insufficient_evidence"` | `insufficient_evidence` | Yes | `model-abstained` |
| Model's JSON has `status: "conflicting_evidence"` | `conflicting_evidence` | **No** | n/a — always `not-reproduced` |
| Model's JSON has `status: "supported"` but a claim is discarded (empty/oversized claim list, missing `text`/`evidence_ids`, an unknown `evidence_id`) | `insufficient_evidence` | Yes | `gate-rejected` |
| Model's JSON has `status: "supported"` and every claim validates | `supported` | **No** | n/a — always `not-reproduced` |

**Practical consequence: `schema-invalid` is a defined classification value
that is not reachable for this candidate set.** All 7 cases in Section 3 have
a reference status of exactly `"insufficient_evidence"` (that is how they were
selected). A schema-invalid reply always externally resolves to
`"system_error"` instead — a different status — so it can never pass the
reproduction check and will always be recorded as `not-reproduced`, not
`schema-invalid`. The *reason* is not lost, though: `gate_decision` still
records `"schema_invalid"` on that case's row, carried independently of the
top-level `classification`. `apps/api/src/kendra_api/evaluation/stage0.py`
keeps `schema-invalid` in its `Classification` type only because the module's
`reference_status` parameter is not hardcoded to `"insufficient_evidence"` and
could in principle be applied to a different reference set in the future — not
because this experiment's own 7 cases can ever produce it as a top-level
label.

The reproduction check is evaluated first, independent of and prior to the
internal-trace classification — a case that reproduces `"insufficient_evidence"`
externally can still internally be a `gate-rejected` case rather than a
genuine `model-abstained` one (both branches return `"insufficient_evidence"`
externally via `_unsupported()`), which is exactly why the internal trace is
captured at all and not inferred from `final_status` alone.

**Updated decision rule — Stage 1 (Section 6, the `B0` vs `B1_LARGER`
comparison) runs only on cases both reproduced and classified
`model-abstained`.** A case classified `not-reproduced`, `gate-rejected`,
`schema-invalid`, or `other` is not a model-choice question: a bigger model
cannot be credited for fixing an unstable baseline, a gate rejection, or a
JSON-parsing failure that has nothing to do with willingness to answer. Those
are recorded as their own findings, separate from the model-comparison
question, and are explicitly out of Stage 1's scope. **If Stage 0 finds zero
cases both reproduce and classify `model-abstained`, Stage 1 does not run at
all, and this draft's hypothesis (Section 1) is void by construction, not
failed** — see Section 9.

## 5. Controlled variables (Stage 1)

Retrieval configuration (`top_k=8`, `score_threshold=0.5`), the frozen retrieved
evidence packet already captured for each Stage-0-qualified case (re-retrieval is
not repeated per candidate — this removes retrieval variance as a confound
entirely), the `bge-m3` embedding model, the ADR-007
`native-primary-detection-v1` extraction policy under which the corpus was
ingested, decoding temperature `0` (see Section 4's settings; no seed exists to
pin — if `B1`'s serving path exposes one, Requires-before-freezing item 3 pins
it), per-request timeout, concurrency of one, and the source revision the corpus
was ingested and this diagnostic was run under
(`0bcc9dd7d0aaf7bd370e8d3eb60303a42e8ef91c`). Only the answer model varies
between `B0` and `B1_LARGER`.

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
   Record every case's reproduction result and, where reproduced, its
   classification.
2. Confirm and pin `B1_LARGER`'s exact tag and digest (Requires-before-freezing
   item 2).
3. For each case Stage 0 classified `model-abstained` (implying `reproduced ==
   true`), replay the exact frozen evidence packet (same chunks, same order,
   same claim-eligible evidence IDs) through `B1_LARGER` via the same
   in-process mechanism Stage 0 used, without a live retrieval call.
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

Let **N** be the number of cases Stage 0 both reproduces and classifies
`model-abstained` (N ≤ 7).

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
  classifies `not-reproduced`/`gate-rejected`/`schema-invalid`/`other` — those
  have a documented or distinct cause, not a "model chose to abstain" one;
- anything about `KND-M5-UN-002`'s temporal-boundary defect (part (a)) — a
  different failure mode, tracked separately;
- a production model decision — see Section 8;
- that EXP-01, EXP-03, or Milestone 10 may proceed. All three remain blocked
  regardless of this experiment's outcome, per `docs/milestones/M12_STATUS.md`.

## 10. Failure behavior

A failed or inconclusive run is recorded, not repaired or rerun with softened
criteria. If Stage 0 cannot complete for a case (model unavailable, timeout), that
case is recorded as incomplete with its cause and excluded from N — it is not
counted as any of the five classifications. If `B1_LARGER` cannot be obtained
or run locally (model unavailable, resource exhaustion, timeout), the Stage 1
attempt is recorded as incomplete with its cause; an incomplete run is not
evidence for or against the hypothesis.

---

## Amendment A1 — 2026-09-01

**Status:** Recorded and effective 2026-09-01, at the commit named in
`docs/EXPERIMENT_REGISTRY.md`'s `EXP-11` row for this amendment. Additive only.
**Sections 1–10 above remain verbatim, unreworded, per the freeze.** This
amendment supersedes specific mechanism details in Sections 4 and 5 (named
below) without editing their text, and does not touch the frozen decision rule
(Section 8) or scoring rule (Section 7) in any way.

**Why.** `evaluation/M12_FINDINGS.md` part (f) (the pre-Stage-1 truncation
check) found that the Stage 0 run this freeze originally covered
(`evaluation/runs/EXP-11/20260901T014805Z-0bcc9dd7/`) did not follow Section 4
mechanism item 2 as written: instead of a static, pinned evidence packet
captured once from `M12_FINDINGS.md` part (d)'s diagnostic, it used evidence
"freshly re-fetched via the real `QdrantRetriever`" on each run — a live
retrieval call, the exact thing Section 4 item 2 forbids. That check also
found no machine-readable record of part (d)'s own captured chunks was ever
persisted anywhere, so no chunk-identical replay could be verified against any
artifact, for either that run or part (d) itself. This amendment closes both
gaps going forward without rewording the sections that named the original
(unmet) requirement.

### A1(a) — Evidence packets: captured once, persisted, loaded from disk

**Supersedes Section 4 mechanism item 2 and Section 5's "frozen retrieved
evidence packet" language, which named the requirement but not a durable
mechanism for meeting it.**

Each of the 7 candidate cases' evidence (Section 3) is captured **exactly
once** via live retrieval (real `QdrantRetriever`, `top_k=8`,
`score_threshold=0.5`, real `bge-m3` embedder, against the
`0bcc9dd7d0aaf7bd370e8d3eb60303a42e8ef91c` source revision) and persisted to
`evaluation/runs/EXP-11/packets/<case_id>.json`, one file per case, containing:

- `case_id`, `question`, `captured_at` (UTC timestamp of capture), `source_revision`,
  `retrieval_config` (`top_k`, `score_threshold`, `embedding_model`);
- `evidence`: an ordered array, each entry an `order` index (0-based, the
  order `render_evidence()` will render and `ev-N` numbering will follow) plus
  every field of `kendra_api.answering.models.Evidence` (`evidence_id`,
  `text`, `document_id`, `version_id`, `filename`, `page`, `chunk_id`,
  `source_sha256`, `processing_run_id`, `extraction_method`,
  `generation_id`) — the full set needed to reconstruct a faithful `Evidence`
  object and to pass real admission (`_admit` needs `version_id`), not only
  the chunk id/text/order this amendment's own name for the file emphasizes.

A `MANIFEST.sha256` file in the same directory lists each packet file's own
SHA-256 (`sha256  filename`, one per line, sorted by filename); the **packet
set hash** is the SHA-256 of that manifest file's exact bytes — a single value
that changes if any packet file's content changes, is added, or is removed.
Both are checked into the same untracked location as the packets themselves
(see the open question below).

**From this amendment forward, every Stage 0 and Stage 1 run loads evidence
for these 7 cases exclusively from these files.** No run may call
`QdrantRetriever.retrieve()` (or any other live Qdrant/embedding call) for
these cases again. A run that needs to re-derive the packets (e.g., a corpus
re-ingest) must recapture them under a new, explicitly-dated sub-amendment,
not by quietly re-running live retrieval — the same rule Section 5 already
applies to why the packet is frozen at all, now given an actual persistence
mechanism.

**Open question, deliberately not decided by this amendment:** the packets
directory (`evaluation/runs/EXP-11/packets/`) sits under the existing
`/evaluation/runs/` gitignore rule and is therefore untracked, consistent with
every other file previously written under that path (`stage0_cases.jsonl`,
`stage0_summary.md`). Unlike those, this packet set is now load-bearing for
every future Stage 0/Stage 1 run rather than a single run's own output. Whether
that warrants a `.gitignore` carve-out to track it in version control is left
to whoever reviews this amendment — not decided here, so it isn't silently
folded into "additive" scope beyond what was asked.

### A1(b) — Decoding seed: a controlled variable, identical in both arms

**Supersedes Section 4's "No model-generation seed exists to match" bullet and
Section 5's "no seed exists to pin" parenthetical — both were accurate when
written and are now superseded by a code change, not by new evidence about the
old code.**

`apps/api/src/kendra_api/answering/model_client.py`'s `OllamaAnswerModel` now
sends an explicit `seed` option on every `/api/generate` request (commit
`answering: explicit num_ctx and seed`, `docs/EXPERIMENT_REGISTRY.md`-dated
2026-09-01), defaulting to `0` and configurable via `KENDRA_MODEL_SEED`. This
deployment runs with the default (`seed: 0`) unless an operator overrides it.

**Seed is now a controlled variable under Section 5, identical across every
arm this experiment runs:** the Stage 0 rerun under this amendment, and (when
it eventually runs) both `B0_BASELINE` and `B1_LARGER` in Stage 1, all use
`seed: 0` unless a future amendment explicitly changes and records a different
value for all arms at once. A seed is not, by itself, a guarantee of
bit-identical output (backend/GPU floating-point nondeterminism can still
vary a run, same caveat Section 4 already gives temperature `0`) — it narrows
variance further and removes "no seed was ever recorded" as a source of
irreproducibility going forward.

### A1(c) — Original Stage 0 run: superseded, retained

`evaluation/runs/EXP-11/20260901T014805Z-0bcc9dd7/` (its `stage0_cases.jsonl`,
`stage0_summary.md`, and `truncation_check.md`) is marked **superseded** by
this amendment, for the reason given above. It is **not deleted** — the
directory and its contents remain exactly as they were, with a
`SUPERSEDED_BY_A1.md` marker file added inside pointing to the new run
directory this amendment's rerun produces. Every finding already drawn from
that run (`M12_FINDINGS.md` part (f)'s truncation conclusions, the token
counts, the `docker logs` gap) stands as a finding about that specific run and
is not retracted; the run itself is simply no longer the current basis for
Stage 1 eligibility, which the rerun under this amendment now supplies.

### What this amendment does not do

It does not reword Sections 1–10, does not change the candidate case set
(Section 3), does not change the reproduction criterion or classification
mapping (Section 4's tables), does not change the controlled-variable list
beyond adding seed (Section 5), and does not touch the scoring rule (Section
7) or the decision rule (Section 8) in any way. `B1_LARGER`'s pin
(Requires-before-freezing item 2), reviewer confirmation of the
frozen-packet methodology (item 4, now partially addressed by A1(a)'s actual
persistence mechanism but not itself a reviewer sign-off), and the local
resource check (item 5) remain open exactly as before this amendment. Stage 1
is not run by this amendment.

---

## Amendment A2 — 2026-09-01

**Status:** Recorded and effective 2026-09-01. Additive only, layered on top of
Amendment A1. **Sections 1–10 remain verbatim, unreworded.** This amendment
adds a repetition scheme to Section 7's frozen-packet scoring; it does not
reword Section 7's text, and **Section 8's decision rule (the N / N−1-of-N
threshold) is unchanged in every particular** — A2 changes what counts as one
case being "answered," not how many answered cases the threshold requires.

**Why.** Section 4's own settings note (superseded in its literal wording by
A1(b), but the underlying concern it raised is not resolved by adding a seed
alone) already warned that "temperature 0 narrows but does not guarantee
bit-identical output... backend/GPU floating-point nondeterminism can still
vary a run" — and the Stage 0 rerun under A1 confirmed this empirically:
`KND-M5-DF-017` still flipped from `insufficient_evidence` to `supported`
under a fixed `seed: 0`. A single trial per case per arm in Stage 1 would let
exactly this kind of flip decide the hypothesis by chance. A2 adds repetition
to make that risk visible and to raise the bar for what counts as a genuine,
repeatable answer, without touching the threshold that decides the hypothesis.

### A2(a) — Three trials per case per arm

For Stage 1's frozen-packet run (Section 6 procedure, the `B0`/`B1_LARGER`
comparison on the Stage-0-qualified cases), **each case is run three times in
each arm** — same persisted evidence packet (A1(a)), same question, same
decoding settings (`temperature: 0`, `num_ctx: 8192`, `seed: 0` per A1(b)) —
three independent `answer_question()` calls per (case, arm) pair, not a single
call. This applies to both `B0_BASELINE` and `B1_LARGER`; A2 does not single
out one arm for repetition and not the other, since either arm's single-trial
result could otherwise be the one that happens to flip.

### A2(b) — "Answered" requires all three trials to agree, supported, with a citation

**Supersedes Section 7's "a case counts as answered only if `status ==
'supported'` and every one of that case's `expected_answer_facts` is judged
present" — additively: A2 does not remove the human fact-review requirement
Section 7 already states, it adds a stricter repeatability gate in front of
it.**

A case counts as **answered**, in a given arm, only if **all three trials**
satisfy every one of these:

1. `status == "supported"`;
2. at least one valid citation is present (checked directly against the real
   `answer_question()` pipeline: `apps/api/src/kendra_api/answering/service.py`'s
   `_run_pipeline` can only reach `status == "supported"` after every claim's
   `evidence_ids` resolved against admitted evidence and
   `CitationResolver.build()` constructed a citation from a real, registry-resolved
   `SourceRecord` for each one — a "supported" result with zero citations is not
   reachable through this code path, confirmed by reading the function rather
   than assumed; this check is still recorded explicitly per trial rather than
   inferred from status alone, since a future code change could in principle
   decouple the two and A2 does not want that decoupling to go unnoticed);
3. Section 7's existing human fact-review requirement (every
   `expected_answer_facts` entry judged present in the claim text) is
   satisfied.

**Any trial that fails any of the three above** (an abstention, a conflicting-
evidence result, a schema/gate failure, a `supported` result missing a
required fact) makes that case **not answered** in that arm, regardless of
the other two trials' results. A case with two `supported`-and-complete trials
and one abstention is not answered — this is deliberately stricter than "best
of three" or "majority of three."

### A2(c) — Flip rate: recorded, not scored

**Per-arm flip rate** is recorded as a byproduct for every one of the 6
qualified cases in each arm: the fraction of that case's three trials whose
`final_status` differs from the other trials' modal (most common) status for
that case-arm pair (e.g., two `insufficient_evidence` + one `supported` counts
that case as having flipped once, a flip rate of 1/3 for that case in that
arm). An arm's overall flip rate is the mean of its 6 per-case flip rates.
**This number does not enter the decision rule (Section 8) in any way** — it
is reported alongside the answered/not-answered tally as context for reading
the result, consistent with this project's practice of recording observations
separately from the frozen scoring criteria (`stage0_summary.md`'s
"Observations" sections use the same pattern).

### What this amendment does not do

It does not reword Sections 1–10 or Section 7's text, does not change the
candidate case set (Section 3), does not change Section 8's threshold or its
N-dependent branches, does not change the non-regression check (Section 7's
second paragraph, Section 3's non-regression set) beyond the trial count
implied by A2(a) not applying there (the non-regression check is a live,
single-pass run over the full gold set per Section 6 step 4, not a
frozen-packet repeated trial — A2 applies only to the frozen-packet
comparison on the 6 qualified cases). It does not select `B1_LARGER`'s pin,
which remains open exactly as A1 left it.
