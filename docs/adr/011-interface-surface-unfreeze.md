# ADR-011: Interface surface unfreeze — upload, request modes, and score exposure

**Status:** Proposed. **Not accepted and not activated.**
**Date drafted:** 2026-08-21
**Amends:** `MVP_SPEC.md` Section 3 (freeze determination, where the upload definition sits),
Section 7.1 (request contract), and Section 7.2 (citation object), and `ADR-002` on the
document-store trust boundary.
**Spec state while this is proposed:** MVP_SPEC remains **frozen**. This record does not
perform the unfreeze; Section 7 specifies the edits to apply once it is accepted.
**Related:** [ADR-010](010-verified-span-answering.md), proposed — answer mode. That record
carries its own unfreeze requirement for Section 7.2's response shape. The two are independent
and neither substitutes for the other.

> **Why this record exists.** MVP_SPEC anticipated one of these changes by name. Line 44:
> *"Adding browser upload would widen write privileges and change ADR-002's trust boundary;
> that change requires an ADR update and makes this specification unfrozen until reviewed."*
> Section 11 then prescribes the procedure. This record is step 3 of that procedure. It is
> written **before** any Milestone 11 interface code, so the boundary is settled by decision
> rather than discovered by implementation.

## 1. What is being asked for

A planned Milestone 11 interface requires three things the frozen specification does not
permit:

1. **Document upload from the browser**, with progress and processing status.
2. **Quick and Deep local modes**, and **optional document selection** — both new request
   fields.
3. **A relevance score displayed per citation.**

Each is assessed separately below. They are not equally safe, and this record does not treat
them as a single yes.

## 2. Upload — permitted only with the approval gate preserved

### 2.1 What the current boundary actually is

Admission today runs through a trusted-operator CLI that requires an **intake manifest**
carrying `expected_sha256`, `expected_page_count`, `approval_scope`, `provenance_reference`,
and `approval_status`. That manifest is not paperwork. It is the mechanism by which
*"approved public BIR evaluation corpus only"* is enforced against bytes rather than against
intention.

A browser upload endpoint removes that mechanism. Combined with the standing constraint that
**no authentication exists**, anything able to reach the loopback port could write to the
document repository.

### 2.2 Decision proposed

Browser upload is permitted **only if an approval attestation is recorded with the version**.
The UI must, before admission:

1. compute and display the SHA-256 of the submitted bytes;
2. require the operator to enter the `approval_scope` and `provenance_reference` for the
   document;
3. require an explicit, typed attestation that the document is within the approved public
   evaluation corpus and is not agency, personal, confidential, privileged, or
   procurement-sensitive material; and
4. persist attestation text, operator-supplied fields, and timestamp in the durable
   version manifest alongside the existing fields.

Admission continues to fail closed on checksum, page-count, media-type, size, and
path-containment violations exactly as it does now. **No validation is removed.** Upload adds
a path to admission; it does not add an exception to it.

### 2.3 Residual risk, stated not hidden

This is **weaker than the status quo** and must not be recorded as equivalent. The CLI manifest
requires the operator to have prepared an approval record in advance; a typed attestation can
be clicked through in the moment. The control degrades from *prepared evidence of approval* to
*contemporaneous assertion of approval*.

It is proposed as proportionate **only** under the standing scope — localhost, one trusted
evaluator, public corpus. It does not survive a change to that scope. Any multi-user,
networked, or real-document deployment must restore a prepared-manifest gate or an
authenticated approval role, and this record is not authority for either.

## 3. Request modes and document selection — split decision

### 3.1 Document selection: accept

Narrowing a question to an operator-chosen document **reduces** the failure surface. It cannot
introduce evidence that admission would otherwise have excluded, and it directly addresses the
cross-document contamination shape observed on 2026-08-21.

Constraint: selection may only **narrow** the candidate set within the active generation set.
It may never widen it, never reach a non-active generation, and never bypass admission. An
empty or unresolvable selection yields `insufficient_evidence`, not an unfiltered search.

### 3.2 Quick and Deep modes: accept the field, reject the framing

The mechanism is acceptable. The naming is not.

**EXP-02 has never been run.** Neither `top_k` nor the candidate threshold has ever been
selected by evidence; both are engineering defaults. Shipping two modes named *Quick* and
*Deep* to non-technical government staff asserts that one is more thorough — that is, more
likely to be correct — when no measurement supports the claim for either configuration.

Proposed constraint: the field is permitted as a **latency and breadth control only**. Until
EXP-02 selects a configuration:

- neither mode may be described, labelled, ordered, or styled as more accurate, more
  complete, more reliable, or more thorough;
- the interface must state plainly that the modes differ in how much evidence is searched and
  how long that takes, and that neither has been shown to produce better answers; and
- no default may be presented as "recommended".

This constraint lapses only when a frozen EXP-02 result supports a different statement.

The diagnostic in progress at drafting time shows per-question latency ranging from roughly 15
to 200 seconds on the evaluation hardware, so a genuine latency control is useful on its own
terms and does not need an accuracy claim to justify it.

## 4. Relevance score — reject numeric display, permit rank

MVP_SPEC Step 9 places scores in the **internal** evidence set and states they are
*"diagnostic relevance signals, not support declarations."* Section 7.2's citation object
carries no score field. That omission is a decision, not an oversight.

Displaying a number to non-technical staff invites reading it as a probability that the answer
is correct. It is not. It is a vector similarity between a question embedding and a chunk
embedding, and it carries no information about whether the cited passage supports the claim
beside it. `KND-M5-UN-002` is the demonstration: a confidently-cited, checksum-valid,
correctly-paginated answer whose claim its own excerpt did not support. A high similarity score
attached to that citation would have made a false answer look better, not worse.

**Proposed: no numeric score, no percentage, no bar, no colour scale, no star rating.** The
citation list may show **ordinal position** — first, second, third — which conveys retrieval
order without implying calibrated confidence.

What the interface should surface instead, because it is real information about reliability:

- `extraction_method`, with OCR-derived text visibly labelled as derived assistance, per
  ADR-003; and
- the rendered original page as the verification target, which the content endpoint now makes
  reachable.

If a reviewer decides a numeric score must be shown regardless, that requires its own record
stating who the number is for and what they are expected to do with it. This record does not
grant it.

## 5. What this record does not do

- It does not unfreeze anything by itself. MVP_SPEC stays frozen until this is accepted and
  Section 7's edits are applied.
- It does not authorise ingestion of any real agency, personal, confidential, privileged,
  procurement-sensitive, or mixed-permission document. That prohibition is untouched.
- It does not add authentication, and it is not a substitute for it.
- It does not alter the answer contract, the exact unsupported text, the citation identity
  fields, or the admission validations.
- It does not affect EXP-01, EXP-03, EXP-05, or the Milestone 10 gate.

## 6. Evaluation-case impact

MVP_SPEC Section 11 step 4 requires affected evaluation cases to be revised. Assessed:

- **Upload** changes no evaluation case. The 50 cases are questions against an admitted corpus
  and are indifferent to how admission occurred.
- **Document selection** changes no existing case, because selection defaults to the full
  active generation set and the existing cases exercise that default. Cases that exercise
  selection specifically would be **new** cases, and `evaluation/gold_cases.json` may not be
  edited — it remains `initial_expert_review_required`, and adding cases is expert review, not
  engineering.
- **Modes** change no case, provided the frozen evaluation configuration continues to run one
  recorded mode. An acceptance run may not mix modes across cases.

## 7. Specification edits required on acceptance

Applied only when this record is accepted, per MVP_SPEC Section 11:

1. Mark `MVP_SPEC.md` **Not frozen**, with the reason and this record's identifier.
2. Section 3, line 44 — revise the upload definition to admit a browser path carrying the
   attestation in Section 2.2 of this record, retaining the statement that ordinary runtime
   API writes to the document repository are still excluded. Note that this line sits inside
   the *freeze determination* itself, so editing it is by construction an unfreeze.
3. Section 7.1 — add `document_ids` (optional, narrowing only) and `mode` (optional, latency
   and breadth only) to the accepted request fields, and revise *"Only the fields above are
   accepted in the first MVP"* accordingly.
4. Section 7.2 — **no change.** No score field is added.
5. `ADR-002` — record the widened write path and the attestation that replaces the prepared
   manifest on that path.
6. `DATA_GOVERNANCE.md` and `THREAT_MODEL.md` — record the degraded approval control from
   Section 2.3 and the loopback-exposure consequence of upload without authentication.
7. Re-freeze only after review, per Section 11 step 5.

## 8. If this record is rejected

Milestone 11 must be built within the frozen surface: no browser upload, no new request
fields, no score display. That yields a usable evidence-inspection interface — question,
answer, citations, original-page rendering, export — and omits upload, modes, and selection.
Say so in the milestone record rather than building the wider surface and describing it as
compliant.

## 9. Scope

Localhost only, one trusted evaluator, approved public BIR evaluation corpus only. No
authentication exists and none is implied. Nothing here relaxes the prohibition on real agency,
personal, confidential, privileged, procurement-sensitive, or mixed-permission documents.
