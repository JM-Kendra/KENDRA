# EXP-04 (draft, identifier collision unresolved) — model comparison on facts-in-context-but-abstained cases

**Status:** DRAFT. **Not frozen and not a registration.** Written per the requester's
instruction; not run. It becomes a real registration only after the identifier
collision below is resolved and every item in *Requires before freezing* is
satisfied, checksummed **before either candidate is run**.
**Drafted:** 2026-09-01.

> ## Identifier collision — unresolved, read this first
>
> **`EXP-04` is already assigned.** `docs/EXPERIMENT_PLAN.md` Section 6 defines
> `EXP-04 — Local Qwen model selection`: "Which of two pinned, workstation-suitable
> Ollama-compatible Qwen-family variants or quantizations can meet the structured
> grounded-answer and bounded latency contract locally?" It has its own decision
> artifact target (`docs/experiment-decisions/EXP-04.md`), its own gates
> (structured-schema validity, unknown-evidence-ID rejection, unsupported
> false-answer rate, warm/cold latency ceilings, memory pressure), and its own
> prerequisite chain (EXP-02 passed; Milestone 10 generation/validation capability
> available). This draft studies something narrower and different: whether a
> larger model answers the specific 7 cases `evaluation/M12_FINDINGS.md` part (d)
> found had every required fact already in the retrieved context, when
> `qwen2.5:7b-instruct` still abstained. It does not measure schema validity,
> unknown-ID rejection, or latency/memory ceilings, and it is not a model-selection
> decision.
>
> This project has an established precedent for calling out an identifier
> collision rather than quietly resolving it — see the EXP-07 collision noted in
> `KENDRA_MIGRATION_HANDOFF.md`. Filing this under the requested filename follows
> that precedent: the collision is recorded, not resolved, here. Options for the
> reviewer: (a) assign a new identifier — `EXP-08` is the next number not already
> taken by a defined or drafted experiment as of this date (EXP-05, 06, 07 are all
> in use or reserved); or (b) explicitly fold this study into EXP-04's existing
> scope as a preliminary/component run, with that decision recorded in
> `EXPERIMENT_PLAN.md` itself, not assumed here. Neither is decided by this draft.

## 1. Question and decision

**Does a larger local model answer the 7 gold cases where `qwen2.5:7b-instruct`
abstained despite every required fact already being present in the retrieved
context, without introducing new false answers on the cases that were correctly
handled or on the unsupported stratum?**

Produces: a reviewed decision record (once registered under whichever identifier
the collision above resolves to) stating whether model size, on this narrow
evidence, plausibly explains the generation-side abstentions `M12_FINDINGS.md`
part (d) found — or whether it does not, and the cause lies elsewhere (prompt
construction, decoding settings, or the answering contract itself). It does
**not** select a production model. See Section 7.

## 2. Frozen candidate matrix

| Candidate | Model | Selectable |
|---|---|---|
| `B0_BASELINE` | `qwen2.5:7b-instruct` (already pinned as this deployment's default `KENDRA_ANSWER_MODEL`) | No — reference only, reproduces the abstentions under study |
| `B1_LARGER` | **proposed:** `qwen2.5:14b-instruct` — same model family and prompt/instruction lineage as the baseline, differing only in parameter count, minimizing confounds from switching model families. **Not yet confirmed by the reviewer; must be pinned by exact tag and digest before freezing (Requires-before-freezing item 1).** | Yes, pending confirmation |

`B0` is never selectable — it is the configuration whose abstentions are under
study, matching the convention `EXP-05-preregistration-draft.md` §2 uses for its
own non-selectable baseline.

## 3. Input contract — frozen candidate case set

**Exactly these 7 case IDs, no more, no fewer:**
`KND-M5-CD-004`, `KND-M5-CD-005`, `KND-M5-DF-005`, `KND-M5-DF-008`,
`KND-M5-DF-009`, `KND-M5-DF-017`, `KND-M5-DF-020`.

This is the "facts in context, model abstained anyway" set from
`evaluation/M12_FINDINGS.md` part (d) — established by a prior, independent,
read-only diagnostic that never ran `B1_LARGER` and could not have been shaped by
its results. Using this set here is not evidence-after-the-fact selection for
*this* experiment: which cases belong to it was fixed before `B1_LARGER` was even
proposed as a candidate.

**Plus, unconditionally, as a non-regression check:** all 10 `deliberately_unsupported`
cases (`KND-M5-UN-001` through `KND-M5-UN-010`) and the 36 gold cases *not* in the
7-case set above and *not* among the 13 false negatives this run's `M12_FINDINGS.md`
already accounts for. A larger model that fixes the 7 but breaks previously-correct
cases, or answers an unsupported case falsely, has not demonstrated anything this
experiment would credit — see Section 6.

**Excluded, deliberately:** the 6 other false negatives from the same run
(`KND-M5-CD-006`, `KND-M5-CD-009`, `KND-M5-CD-010`, `KND-M5-DF-012`,
`KND-M5-LT-003`, `KND-M5-LT-007`) — those have a documented content-availability
gap (a cross-document retrieval limit or a chunk-density miss), not a generation
decision, so a larger model cannot be expected to answer them correctly from the
same retrieval output, and scoring them here would conflate a retrieval problem
with the generation question this experiment asks. And `KND-M5-UN-002` — its
defect (temporal-boundary overclaiming, part (a)) is a different failure mode
than abstention-despite-evidence and is tracked separately as a proposed
verification-contract rule, not a model-comparison question.

## 4. Controlled variables

Retrieval configuration (`top_k=8`, `score_threshold=0.5`), the frozen retrieved
evidence packet *already captured* for each of the 7 candidate cases in this run's
diagnostic (re-retrieval is not repeated per candidate — see Section 5, this
removes retrieval variance as a confound entirely), the `bge-m3` embedding model,
the ADR-007 `native-primary-detection-v1` extraction policy under which the
corpus was ingested, decoding temperature `0` (the answering client's only
currently-set decoding option — no seed is recorded in
`apps/api/src/kendra_api/answering/model_client.py` as of this draft; if `B1`'s
serving path exposes one, Requires-before-freezing item 2 pins it), per-request
timeout, concurrency of one, and the source revision the corpus was ingested and
this diagnostic was run under (`0bcc9dd7d0aaf7bd370e8d3eb60303a42e8ef91c`). Only
the answer model varies.

**Why the evidence packet is frozen rather than re-retrieved per candidate:** this
experiment's question is specifically about generation given known-sufficient
context, not about whether a larger model's own embedding/retrieval behavior
differs (it wouldn't — both candidates would use the same `bge-m3` retriever
regardless of answer-model size, since retrieval and generation are separate
components in this architecture; `apps/api/src/kendra_api/answering/service.py`
wires one retriever and one model per request, and only the model is swapped
between candidates here). Freezing the packet also makes the comparison exactly
about the 7 cases' documented context, eliminating any possibility that a
retrieval-side difference gets misread as a generation-side one.

## 5. Procedure

1. Confirm and pin `B1_LARGER`'s exact tag and digest (Requires-before-freezing
   item 1).
2. For each of the 7 candidate cases, replay the exact evidence packet already
   captured in this run's diagnostic (same chunks, same order, same claim-eligible
   evidence IDs) through `B1_LARGER` via the same answering contract path
   `B0` used, without a live retrieval call.
3. Run `B1_LARGER` against the full 50-case gold set live (real retrieval, not the
   frozen packet) for the non-regression check in Section 3, under the same
   `top_k`/`score_threshold`/corpus as the run this draft is based on.
4. Record `status`, `claims`, `citations`, `duration_ms`, and any error for every
   case, both frozen-packet and live runs, exactly as `CaseRunResult` already does.
5. Score per Section 6. No case is retried, averaged, or best-of-N selected.

## 6. Scoring rule — frozen

**On the 7 candidate cases (frozen-packet run):** a case counts as **answered**
only if `status == "supported"` and every one of that case's
`expected_answer_facts` is judged present by a human reviewer reading the
model's claim text against the fact — the same mechanical-scoring distrust this
project applies everywhere else (`docs/EVALUATION_METHOD.md`; `M12_FINDINGS.md`
part (c)) applies here too: no substring/token-overlap auto-scorer decides this.
A case that returns `supported` with an incomplete or incorrect claim does not
count as answered; it counts as a new defect, recorded, not credited.

**On the non-regression set (live run):** every one of the 36 previously-correct
gold cases must retain its prior classification and pass answer correctness
unchanged; every one of the 10 unsupported cases must return
`insufficient_evidence` (or another safe rejection status) with no false answer.
Any regression here is recorded regardless of how `B1_LARGER` performs on the 7.

## 7. Decision rule — frozen

**`B1_LARGER` is judged to support the "model size, not the answering contract,
explains these abstentions" hypothesis only if:** it answers (Section 6) at least
6 of the 7 candidate cases, **and** the non-regression set shows zero
regressions and zero new unsupported false answers.

If `B1_LARGER` answers fewer than 6 of 7, or produces any regression, the
hypothesis is not supported on this evidence: the abstentions are not explained
by model size alone, and the generation-side question from `M12_FINDINGS.md`
part (b)/(d) remains open for a different kind of investigation (prompt wording,
the answering contract's own instruction text, or decoding configuration).

**This is not a model-selection decision either way.** A `B1_LARGER` pass here
does not authorize deploying a larger model, does not touch
`KENDRA_ANSWER_MODEL`, and does not substitute for EXP-04's actual defined scope
(schema validity, unknown-ID rejection, latency and memory ceilings) once the
collision above is resolved and that experiment is run for real.

## 8. What this would and would not establish

A pass would establish only that, on these 7 cases' already-sufficient context, a
larger same-family model answers where the smaller one abstained, without
regressing the rest of the gold set. It would **not** establish:

- that model size is the *only* variable that matters — prompt wording and
  decoding configuration are not varied here and remain untested;
- anything about the 6 excluded false negatives (Section 3) — those have a
  documented retrieval-side cause, not a generation-side one;
- anything about `KND-M5-UN-002`'s temporal-boundary defect (part (a)) — a
  different failure mode, tracked separately;
- a production model decision — see Section 7;
- that EXP-01, EXP-03, or Milestone 10 may proceed. All three remain blocked
  regardless of this experiment's outcome, per `docs/milestones/M12_STATUS.md`.

## 9. Failure behavior

A failed or inconclusive run is recorded, not repaired or rerun with softened
criteria. If `B1_LARGER` cannot be obtained or run locally (model unavailable,
resource exhaustion, timeout), the attempt is recorded as incomplete with its
cause; an incomplete run is not evidence for or against the hypothesis.

## Requires before freezing

1. **The identifier collision resolved** by the reviewer — a new ID assigned, or
   this explicitly folded into `EXP-04`'s scope with that decision recorded in
   `docs/EXPERIMENT_PLAN.md`. Not decided by this draft.
2. **`B1_LARGER` pinned by exact tag and digest**, and its decoding
   configuration (temperature, and a seed if its serving path exposes one)
   recorded here before any run.
3. **Reviewer confirmation that replaying a frozen evidence packet through a
   different answer model is methodologically acceptable** for this narrow
   question, given `EXP-05-preregistration-draft.md`'s own caution (§3) about
   not letting an easy pass substitute for a harder, more representative test.
4. **Local resource check** — running a 14B-class model locally alongside the
   existing stack (Postgres/Qdrant/Ollama, `qwen2.5vl:7b` already resident on
   this workstation's native Ollama instance) fits available VRAM/RAM without
   destabilizing required services. Not yet checked.
5. **No answering behavior, prompt, or gate threshold changed** to make this
   run possible — per the requester's own instruction for this draft. If
   running `B1_LARGER` through the existing contract requires such a change,
   that need is recorded and freezing waits on its own review, not folded in
   silently.
