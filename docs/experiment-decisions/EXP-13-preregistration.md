# EXP-13 — evidence rendering: per-chunk document label and page

**Status:** **FROZEN, 2026-09-02, at commit `6a3170ddd9ad4a7890c826b919c2b0369c500c97`**
(the commit that landed `evaluation/EXP-13-preregistration-draft.md`'s
content, verbatim below in Sections 1–10 aside from the review edits recorded
immediately below — nothing in those sections may be reworded after this
freeze, per this project's rule that criteria are locked before evidence is
examined). The pre-freeze draft remains at
`docs/experiment-decisions/EXP-13-preregistration-draft.md` with a pointer to
this file; it is not deleted or redirected, so the drafting history stays
visible — matching how `EXP-11-preregistration.md` treats
`evaluation/EXP-11_PREREG_DRAFT.md`.

## Review edits made at freeze (stated explicitly, not silent)

The draft's own "Requires before freezing" list named four open items. All
four are resolved here, at freeze time, as follows — this *is* the review:

1. **Item 1 (label source) — resolved: the raw `filename` verbatim, not a
   human title.** `Evidence`/`SourceRecord` carry no human-readable title
   field, and adding one would be a data-model change beyond
   "`render_evidence` changes only" (the implementation constraint given for
   this round). `R1_LABELED`'s label is therefore `Evidence.filename`
   (e.g. `RR_11_2024_Invoicing_Amendments.pdf`) and `Evidence.page`,
   unmodified, exactly as they already flow into `render_evidence` today.
   This is noisier and further from how questions name documents ("RR No.
   11-2024") than a human title would be — stated plainly, not glossed over,
   since it bears on how to read a pass or a fail below: a case answered
   correctly with the raw filename as its only structural handle is a
   *stronger* result than one that needed a hand-curated title to work, and a
   case that still fails is not proof a human title wouldn't have helped.
   **Section 2 below reflects this resolution directly** (edited from the
   draft's `{human_document_label}` placeholder to the actual
   `{filename}` this freeze commits to).
2. **Item 2 (implementation + tests) — satisfied.**
   `render_evidence_with_labels()` and `detect_label_leak()` are implemented
   in `apps/api/src/kendra_api/answering/model_client.py`
   (`KENDRA_EVIDENCE_RENDERING=current|labeled`, default `current`,
   byte-identical to pre-EXP-13 behavior), with
   `apps/api/tests/test_model_client_rendering.py` (11 tests: both modes'
   exact byte output, `OllamaAnswerModel`'s mode selection including its
   default, and the label-leak detector's true/false cases) passing —
   99→110 tests passed in the isolated `docker build --target test` image
   (0 failed).
3. **Item 3 (methodology reviewer confirmation) — confirmed.** Testing via
   the same frozen-packet/live-non-regression split EXP-11 Stage 1 used is
   accepted for this question; no objection raised.
4. **Item 4 (no answering-behavior change beyond the one rendering
   function) — confirmed, checked directly.** `SYSTEM_INSTRUCTION` is
   unmodified (verified by diff); `_run_pipeline`'s gate logic in
   `apps/api/src/kendra_api/answering/service.py` is unmodified; the only
   change is `render_evidence_with_labels` (new function, `render_evidence`
   itself untouched) plus the `KENDRA_EVIDENCE_RENDERING` selector wired
   through `config.py`/`main.py`/`docker-compose.yml`, defaulting to
   `current` everywhere.

No other edits were made. Sections 1–10 below are otherwise the draft's own
text.

---

The remainder of this document is Sections 0 through 10 of
`docs/experiment-decisions/EXP-13-preregistration-draft.md`, at the commit
named above, with only the Section 2 edit named in review-edit item 1 applied.

## 0. What prompted this

A read-only inspection of `render_evidence()` (`apps/api/src/kendra_api/answering/model_client.py`)
against `KND-M5-CD-004`'s persisted evidence packet
(`evaluation/runs/EXP-11/packets/KND-M5-CD-004.json`, captured under EXP-11
Amendment A1) found:

- `render_evidence()`'s output for every evidence item is exactly
  `<evidence id="ev-N">\n{text}\n</evidence>` — no filename, title, page, or
  any other document-identifying label of any kind. This is confirmed, not
  inferred: the actual rendered output for the packet's first three items
  was printed verbatim and contained nothing but the opaque `ev-N` id and
  quoted chunk text.
- **None of `KND-M5-CD-004`'s 8 evidence chunks — including the actual
  `RMC No. 77-2024` chunks themselves — mention "RMC" or "77-2024" anywhere
  in their own body text.** Checked directly across all 8 items, not just the
  three printed. The only place the string "RMC No. 77-2024" appears anywhere
  in the constructed prompt is in the user's own question text.

`KND-M5-CD-004`'s question is *"Do RR No. 11-2024 and RMC No. 77-2024 state
the same CAS or CBA enhancement deadline and extension limit?"* —
`M12_FINDINGS.md` part (d) already established that the required facts are
present, often verbatim, in this case's retrieved context, and that the model
abstains anyway. `M12_FINDINGS.md` part (g), added alongside this freeze,
records the conclusion this inspection supports: the six EXP-11 candidate
cases' original abstentions were correct, safe behavior given this rendering,
not an unexplained defect. This draft's hypothesis: **the model may be unable
to attribute which evidence item belongs to which named document at all**,
since nothing in its input — not the rendering, not the chunk text — ever
states the name the question is asking about for that document. A model that
cannot tell which of 8 undifferentiated quoted blocks came from "RMC No.
77-2024" cannot safely claim that document says anything, regardless of
whether the right facts are technically present somewhere in the block.

This is a *different* candidate explanation from EXP-11's own hypothesis
(model size). It does not depend on EXP-11's outcome (Stage 1 found the
hypothesis there not supported) and is not a retry of it — a different
variable is manipulated here: rendering, not model choice.

## 1. Question and decision

**Does giving the model an explicit per-chunk document label and page in
`render_evidence()`'s output change whether it answers the same
facts-in-context-but-abstained cases it currently declines — without
introducing new false answers, new fabricated-citation risk, or a regression
on the rest of the gold set?**

Produces a reviewed decision record stating whether the current metadata-free
rendering plausibly explains the generation-side abstentions, on this narrow
evidence — or whether it does not. It does **not** by itself authorize
changing `render_evidence()` in production; see Section 8.

## 2. Frozen candidate matrix

| Candidate | Rendering | Selectable |
|---|---|---|
| `R0_CURRENT` | `render_evidence()` unchanged: `<evidence id="ev-N">{text}</evidence>`, no document identity of any kind. Already the deployment's default (`KENDRA_EVIDENCE_RENDERING=current`). | No — reference only, reproduces the abstentions under study |
| `R1_LABELED` | `<evidence id="ev-N" document="{filename}" page="{page}">{text}</evidence>` — `Evidence.filename` verbatim (not a human title — see review edit 1 above) and the 1-based physical page, both server-supplied from the same admitted `Evidence` data `render_evidence()` already receives, added to the rendering only. Selected via `KENDRA_EVIDENCE_RENDERING=labeled`. | Yes |

`R0` is never selectable — matching `EXP-11-preregistration.md` Section 2's
own convention for its non-selectable baseline.

**Both candidates run on the same answer model** (`qwen2.5:7b-instruct`, this
deployment's current default) — this experiment varies rendering, not model
choice, so it stays orthogonal to `EXP-04`/`EXP-11`'s own question.

## 3. Input contract — frozen candidate case set

**The same 6 cases EXP-11 Stage 1 found eligible under its frozen decision
rule:** `KND-M5-CD-004`, `KND-M5-CD-005`, `KND-M5-DF-005`, `KND-M5-DF-008`,
`KND-M5-DF-009`, `KND-M5-DF-020` — the "facts in context, model abstained
anyway" cases that also reproduced and classified `model-abstained` under
EXP-11 Stage 0. `KND-M5-DF-017` remains excluded (EXP-11's own reproduction
criterion). Reusing this exact set, rather than drafting a new one, keeps this
experiment's result directly comparable to EXP-11 Stage 1's own frozen-packet
comparison — same cases, same known facts-present precondition, only the
rendering changes.

**Evidence packets:** loaded exclusively from the same persisted files EXP-11
Amendment A1 already froze — `evaluation/runs/EXP-11/packets/<case_id>.json`
(packet set hash `65d868b1bc712fdfa1099798e46d2bb54f8236ba692babc8d807b75b1e6aca2c`
as committed). No live retrieval for either candidate. `R1_LABELED` reuses
the packet's already-captured `filename`/`page` fields to build its label —
it does not need to retrieve anything new, only render what is already there
differently.

**Non-regression set: 37 cases** (10 `deliberately_unsupported` +  27 other
gold cases not in the 7-case candidate set or the 6 other-false-negative
cases) — the corrected figure from `EXP-11-preregistration.md`'s 2026-09-01
erratum, used directly here rather than the frozen text's own "36," since
this is a new document not bound by that erratum's constraint against
rewording Section 3.

## 4. Mechanism (in-process, same family as EXP-11 Stage 0/1)

1. **In-process**, via `answer_question()` directly — the same mechanism
   `apps/api/src/kendra_api/evaluation/stage0.py` and EXP-11 Stage 1's own
   trial runner used, not the HTTP API, for the frozen-packet comparison.
2. **`R1_LABELED`'s rendering change is isolated to a new function**, not an
   edit to `render_evidence()` in place — `render_evidence_with_labels()`
   alongside the existing one, so `R0_CURRENT` remains provably identical to
   current production behavior throughout this experiment (no shared code
   path that could let a labeling bug leak into the unlabeled candidate).
3. **`SYSTEM_INSTRUCTION` is unchanged for both candidates.** Its existing
   rule — "Never write filenames, page numbers, checksums, paths, URLs, or
   document status. Refer to evidence only by the supplied evidence_id
   values." — already governs model *output* regardless of what the rendered
   *input* contains. `R1_LABELED` tests whether giving the model a label to
   read changes its ability to answer; it is not proposing to relax the rule
   against the model asserting one in its own claims.
4. **Real admission, `InMemoryAuditSink` only** — same as EXP-11 Stage 0/1;
   nothing from this experiment's frozen-packet comparison reaches the real
   `question_audit` table.
5. **Three trials per case, per arm** (A2's scheme, reused directly): 6 cases
   × 2 arms × 3 trials = 36 calls for the frozen-packet comparison.

## 5. Controlled variables

Same as `EXP-11-preregistration.md` Section 5, plus A1(b)/this deployment's
current decoding settings (`temperature: 0`, `num_ctx: 8192`, `seed: 0`) —
identical across both arms. Only the evidence rendering varies.

## 6. Procedure

1. Implement `render_evidence_with_labels()` behind a flag the trial runner
   selects explicitly per arm (not a global config change) — satisfied, see
   review edit 2.
2. For each of the 6 cases, in each arm, run 3 trials via `answer_question()`
   against the same frozen packet, varying only which rendering function
   builds the evidence block.
3. Run `R1_LABELED` live against the full 50-case gold set (real retrieval,
   `KENDRA_ANSWERING_ENABLED=true`, model switched via `.env`/env override and
   restored after, exactly as EXP-11 Stage 1's non-regression check did) for
   the 37-case non-regression check in Section 3.
4. Score per Section 7. No case is retried, averaged, or best-of-N selected.

## 7. Scoring rule — frozen

**On the 6 qualified cases (frozen-packet run), per A2's scheme exactly:** a
case counts as **answered**, in a given arm, only if **all three trials**
return `status == "supported"`, carry at least one valid citation, and pass
Section 7-style human fact-completeness review against
`expected_answer_facts` — the same three-part bar EXP-11 Amendment A2 defined,
reused verbatim rather than redefined. Per-arm flip rate recorded as a
byproduct, not scored, also per A2(c)'s convention.

**New check specific to this experiment, on every `R1_LABELED` trial
regardless of case:** no claim's `text` may contain the label string
(document name or page) this experiment adds to the rendering — checked via
`detect_label_leak()`. This is checked in addition to, not instead of, the
existing admission-based citation-construction guarantee (`_run_pipeline`
still builds every citation from a real, registry-resolved `SourceRecord`,
never from model output) — the concern here is narrower: that seeing a label
in its input could tempt the model to *echo* it in prose, which the existing
gate does not by itself forbid at the claim-text level the way it forbids
unresolvable evidence_ids. **Any trial where a claim's text contains the
label content is recorded as a new defect for `R1_LABELED`, regardless of
whether the underlying claim was otherwise correct** — a labeling leak is
disqualifying on its own.

**On the non-regression set (37 cases, live run):** identical rule to
`EXP-11-preregistration.md` Section 7's second paragraph — every previously-
correct case retains its classification and correctness; every unsupported
case returns a safe rejection with no false answer. `KND-M5-UN-002`'s
pre-existing, separately-tracked defect (`M12_FINDINGS.md` part (a)) is not
scored as a new regression if it persists unchanged, matching how EXP-11
Stage 1 treated it.

## 8. Decision rule — frozen

Let **N = 6** (fixed; unlike EXP-11 Section 8, this experiment's case set is
not itself subject to a reproduction/classification step — it inherits
EXP-11 Stage 0's already-qualified set directly).

- `R1_LABELED` supports the hypothesis only if it answers at least **5 of the
  6** qualified cases (the same N−1-of-N tolerance EXP-11 Section 8 used at
  N=6) **and** produces zero label-leak defects (Section 7) **and** the
  non-regression set shows zero regressions and zero new unsupported false
  answers.
- Any regression, any label leak, or falling short of 5/6 fails the
  hypothesis outright — matching EXP-11 Section 8's own "a regression fails
  the hypothesis outright" language, extended here to the label-leak check
  this experiment adds.

**This is not an authorization to change `render_evidence()` in production**
either way — a pass would establish only that labeling plausibly helps on
this narrow evidence, not that it is safe or sufficient to ship; that remains
a separate decision requiring its own review, matching how EXP-11 Section 8
treated a pass on its own hypothesis as not a model-selection decision. **Per
the requester's explicit instruction, `R1_LABELED`/`labeled` is not adopted
as the default regardless of this experiment's outcome — this run reports and
stops.**

## 9. What this would and would not establish

A pass would establish that, on these 6 cases' already-sufficient context, an
explicit per-chunk document label lets the same-sized model answer where it
previously abstained, without introducing a labeling-leak defect or
regressing the rest of the gold set. It would **not** establish:

- that rendering is the *only* variable that matters — EXP-11's model-size
  question and any prompt-wording variable remain untested by this
  experiment;
- anything about the 6 cases excluded from EXP-11's own candidate set, or
  `KND-M5-DF-017`;
- that `render_evidence()` should actually change in production — see
  Section 8;
- anything about `EXP-01`, `EXP-03`, or Milestone 10's own blocked status,
  all of which remain unaffected regardless of this experiment's outcome.

## 10. Failure behavior

A failed or inconclusive run is recorded, not repaired or rerun with
softened criteria — matching `EXP-11-preregistration.md` Section 10 exactly.
