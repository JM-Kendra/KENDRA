# ADR-010: Verified-span answering and the entailment boundary

**Status:** Proposed. **Not accepted and not activated.**
**Date drafted:** 2026-08-21
**Amends:** [ADR-003](003-grounded-answering.md) *Server-enforced grounded answering with safe
abstention*, accepted — the **answer-mode selection only**. The retrieval gate, the admission
chain through server records, server-owned citation construction, the prompt-injection
boundary, the typed safe-response table, and the exact unsupported text are untouched and
remain in force exactly as written.
**Active contract while this is proposed:** ADR-003, unchanged in every respect.
**Related:** the Milestone 10 prototype at commit `666ba8e`, which sits behind
`KENDRA_ANSWERING_ENABLED` and is off by default. This record proposes changing what that
prototype is permitted to emit; it does not ratify the prototype.

> **Disclosure.** This record was drafted **with the 2026-08-21 live-run result in hand** —
> specifically the `KND-M5-UN-002` failure described in Section 1. That ordering is stated
> plainly. The failure is what establishes that the entailment gap is *reachable in practice*
> rather than a theoretical limitation already noted in ADR-003; without it this record would
> be speculation. The mitigation for that ordering is that the decision in Section 3 is
> argued from **what the API can and cannot mechanically verify**, not from which claim
> happened to be wrong. No rule below names a case, a document, a word, or a question class
> observed in that run, and Section 4 is written to be evaluated blind across all 50 cases.

## 1. What the run established

The Milestone 10 prototype answered `KND-M5-UN-002`, a deliberately unsupported case, with
`status: supported`. The claim asserted that one regulation **"is superseded by"** another.
Its two citations resolved to real pages whose excerpts state only that the second regulation
**"amends the transitory provisions"** of the first.

Every server-side control in ADR-003 passed while this happened:

- the citation was built by the API from its own records, not by the model;
- the source checksum matched the admitted version;
- the physical page was correct and one-based;
- the original was present and resolvable;
- the evidence belonged to an active generation;
- every material claim carried at least one admitted evidence ID.

A second, quieter instance appeared in the same run: a supported answer attached two
citations to one claim where only one of the two excerpts contained the claim's content. The
extra citation was decorative. Citation precision is required to be 100% by MVP_SPEC Step 11.

## 2. Why more validation cannot close it

ADR-003 requires that *every material claim has validated evidence*. The implementation
enforces exactly that: a claim must reference an admitted evidence ID. What it cannot enforce
is that the referenced evidence **entails** the claim.

That is not an implementation shortfall. ADR-003 already records the boundary — *"BGE-M3
similarity and model-selected evidence still do not prove semantic entailment; expert
evaluation remains necessary."* The run demonstrates that the boundary is not a corner case:
a fluent, well-cited, checksum-valid, correctly-paginated answer can carry a claim the cited
text does not support, and no metadata check anywhere in the chain will see it.

Strengthening validation therefore cannot fix this, because everything validatable already
passed. The only remaining lever is to **reduce what the model is permitted to author** until
the residue is something the API can check by construction.

## 3. Decision proposed (conditional)

Adopt a frozen `verified-span-answering-v1` answer mode.

### 3.1 Every material claim is a verified span

A supported answer's claims are no longer model-authored prose. Each claim must be a
**contiguous verbatim span of one cited excerpt**, and the API verifies it by exact string
containment against the server-owned evidence text before the claim may be returned. A claim
whose text is not found in a cited excerpt is discarded and the answer falls to
`insufficient_evidence`.

The model's task narrows from *"state what the evidence shows"* to *"select the span that
answers this."* Span selection remains model judgment; span **fidelity** becomes a mechanical
property the API can prove.

### 3.2 Citation precision is enforced, not requested

A citation may be attached to a claim only if that citation's excerpt is the one containing
the claim's span. Attaching an evidence ID that does not contain the span is a validation
failure, not a stylistic flaw. This closes the decorative-citation instance in Section 1
without a separate rule.

### 3.3 Synthesis strata return evidence packets, not prose

Cross-document comparison cannot be expressed as a single verbatim span by definition, since
no one document contains the comparison. For strata requiring synthesis the API returns a
**retrieval-only evidence packet**: the competing admitted passages, each with its own
server-built citation, presented side by side with source roles kept separate and **no
generated connective claim**. The reviewer draws the conclusion.

ADR-003 already reserved both halves of this decision as deferred alternatives — *"Extractive
answers only — Deferred"* and *"Retrieval-only evidence packets — Retained as a fallback and a
possible safer mode for higher-risk tasks."* This record activates them; it does not invent
them.

### 3.4 A derived property, claimed as such

Under 3.1 a currentness or applicability claim can only be returned if some admitted document
literally states that status in text. No bespoke question classifier is introduced, and none
should be: a keyword rule written now would be shaped by the observed failure. The abstention
on such questions is a **consequence** of the span rule, not a mechanism of its own.

Residual risk, stated rather than hidden: a span that reads as a status statement in isolation
could still be selected out of context. The span rule bounds fabrication; it does not
establish that a faithfully quoted sentence answers the question asked.

## 4. Activation condition (fixed at drafting time)

This ADR may be accepted **only if all five hold** on a single preregistered run, evaluated in
full before any part of the result is used to revise this record:

1. **Span fidelity is total.** Every material claim in every supported answer across all 50
   cases is a contiguous verbatim span of one of its own citations, verified by exact string
   containment. **Zero** claims are exempted, waived, or hand-classified as acceptable
   paraphrase.
2. **The unsupported stratum is clean.** All 10 deliberately unsupported cases return
   `insufficient_evidence` with the exact 51-character sentence, zero claims, and zero
   citations. No case may be reclassified, re-scoped, or moved to another stratum after the
   run begins.
3. **Citation precision is 100%.** Every citation attached to a claim contains that claim's
   span. Zero decorative citations across all supported answers.
4. **No synthesis leaks into a supported status.** Every cross-document comparison case
   returns either an evidence packet or `insufficient_evidence`. Any comparison case returning
   `supported` with a generated connective claim fails this condition outright.
5. **The run is reproducible.** Two consecutive executions under one recorded configuration
   and seed produce identical statuses, identical spans, and identical citation sets for all
   50 cases. Non-determinism fails the condition; it is not averaged, retried, or
   best-of-selected.

If any condition fails, Section 8 applies.

## 5. What this record does not claim

- **It does not address OCR fidelity.** A verbatim span quoted from corrupted OCR text is
  still corrupted. SF-01, MF-01, and the measured 8.8% digit-substitution rate on the 12
  scanned pages are untouched by anything here. This record closes an **inference** gap; the
  **fidelity** gap remains open under [ADR-008](008-ocr-fidelity-and-detection.md) and
  [ADR-009](009-ocr-render-and-model-fidelity.md), both proposed and neither activated.
- **It does not unblock EXP-01.** EXP-01 remains inconclusive. Four facts remain held by the
  gold-case page-scoping defect and MF-01 still awaits a reviewer ruling.
- **It does not unblock EXP-03 or Milestone 10.** Those gates are unchanged. Acceptance of
  this record would establish only that the answering surface cannot fabricate an inference,
  never that the text beneath it is faithful to the preserved source.
- **It does not establish answer quality.** A system that abstains on every question satisfies
  conditions 2 through 5 trivially. Condition 1 is a fidelity floor, not a usefulness measure;
  recall and usefulness are separate questions requiring their own preregistration.
- **It does not select retrieval configuration.** `top_k` and the candidate threshold remain
  unselected because EXP-02 has never been run. They are engineering defaults in the
  prototype and no recall claim may be made from them.

## 6. Regression coverage required before activation

Written and committed **before** the run, so their content cannot be shaped by its result:

1. A claim whose text is not a substring of any cited excerpt is rejected, and the response
   falls to `insufficient_evidence` with the exact sentence.
2. A claim that is a substring of a *non-cited* admitted excerpt is rejected; containment must
   hold against the citation actually attached.
3. A span altered by a single character, by whitespace normalization, or by re-casing is
   rejected. Containment is byte-exact against the stored evidence text.
4. A claim assembled from two non-adjacent fragments of one excerpt is rejected as
   noncontiguous.
5. A comparison case never returns `supported` with a generated connective claim.
6. An evidence packet carries every citation field required by MVP_SPEC Step 11 and no
   model-authored metadata.
7. The exact unsupported sentence, its length, and its empty claim and citation arrays are
   unchanged from ADR-003 and MVP_SPEC Section 7.3.

## 7. Preregistration required before the run

No new experiment identifier is created. `ARCHITECTURE.md` already reserves **EXP-05** for
exactly this question — *"Does the two-stage grounding gate reject unsupported output?"*,
deciding *"structured response schema, validation rules, abstention wording, and fail-closed
behavior."* Span containment is a validation rule and a schema constraint, so it belongs
inside EXP-05 rather than beside it. Conditions 1, 3 and 4 of Section 4 extend EXP-05's stated
scope from the unsupported stratum to the supported strata; that widening must be recorded in
the preregistration and approved, not assumed here.

> **Identifier hazard, raised not resolved.** `EXP-07` is currently double-booked.
> `ARCHITECTURE.md` reserves it for *"Is the build genuinely offline?"*, while
> `docs/experiment-decisions/EXP-07-preregistration-draft.md`, gated by ADR-009, uses it for
> OCR render resolution and recognition model. That draft notes `EXPERIMENT_PLAN.md` lists
> only EXP-01 through EXP-06 and that adding an identifier needs reviewer approval; the
> `ARCHITECTURE.md` reservations for EXP-07 through EXP-10 appear to have been missed. This
> record does not renumber anything. The collision is the reviewer's to resolve before either
> EXP-07 is frozen.

The EXP-05 preregistration must be frozen before the corpus is processed, fixing at minimum:
the answer mode under test, the pinned model identity and quantization, the decoding seed and
temperature, `top_k`, the candidate threshold, the chunk policy, the exact span-containment
rule including its normalization stance, the stratum assignment of all 50 cases, and the
scoring procedure.

The known scorer defect must be repaired **in that preregistration** and not after results are
visible: the join-match blob is built in first-occurrence order rather than document order,
and it can match a digit-bearing token as a substring of a corrupted one.

No part of Section 4 may be reworded once the run has begun.

## 8. If the activation condition fails

Close this record as rejected, state which condition failed and on which cases, and leave
ADR-003's answer mode in force unchanged. Do not soften a condition and re-run. Do not carry a
partial result forward as provisional acceptance. EXP-03 and Milestone 10 stay blocked either
way, and the prototype stays behind its flag.

## 9. Specification impact

MVP_SPEC Section 7.2 defines the supported-response shape, and its amendment clause permits
clarification without unfreezing **only** where the change does not alter an observable
acceptance requirement, an API field meaning, or deferred scope. Requiring claims to be
verbatim spans, and returning evidence packets for a whole stratum, alters all three.

This record therefore requires an **explicit specification unfreeze**, not a clarification.
That unfreeze must be recorded before implementation. The exact unsupported text in Section
7.3 is deliberately excluded from the unfreeze and stays byte-identical.

## 10. Alternatives considered

### Add an entailment (NLI) model to score claim against excerpt

Rejected for now. It validates a model with a second model, adds a dependency, latency, and a
threshold that would itself need an experiment to select. It reduces the error rate without
making any property mechanically checkable, so the API still could not *prove* a claim is
supported. ADR-003 already defers a separate entailment model on similar grounds. Reconsider
only if verified spans prove too restrictive to be useful.

### Keep generated prose and add a currentness/applicability classifier

Rejected. The observed failure is one instance of unconstrained paraphrase, and a classifier
aimed at the question class that happened to fail would be a rule shaped by visible results —
the exact practice the repository forbids. It would also leave every other question class
carrying the same unbounded inference risk.

### Require the model to emit a supporting quote alongside its paraphrase

Rejected as a half-measure. The API could verify the quote, but the paraphrase would still be
the user-visible claim and still unverifiable. It creates the appearance of verification while
leaving the failure path open.

### Lower the retrieval threshold or raise `top_k` so comparisons see both documents

Rejected here, and specifically not to be done in response to this run. The cross-document
shortfall observed on 2026-08-21 is a retrieval-coverage question that belongs to EXP-02,
which has never been run. Tuning either value now would be configuration selected against
visible results.

### Retrieval-only for every stratum, no generated answers at all

Retained as the fallback if Section 4 fails on condition 1. It is strictly safer and strictly
less useful. It is not proposed as the primary decision because the milestone's stated purpose
includes local generation, and verified spans preserve a bounded form of it.

## 11. Scope

Localhost only, one trusted evaluator, the approved public BIR evaluation corpus only. No
authentication exists and none is implied by this record. No real agency, personal,
confidential, privileged, procurement-sensitive, or mixed-permission document may be ingested
under this or any other record while that remains true.
