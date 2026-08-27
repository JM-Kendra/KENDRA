# Evaluation Method

**Status:** Milestone 5 evaluation foundation; candidate v2 is mechanically corrected but expert adjudication is required before scored use

**Last updated:** 2026-08-21

## Purpose and boundary

This method defines how to evaluate Kendra's future document-grounded answers against [`evaluation/gold_cases.json`](../evaluation/gold_cases.json). It specifies evidence, scoring, timing, and review rules only. It does not implement retrieval, OCR, prompting, generation, orchestration, or any other AI pipeline.

The candidate dataset contains 50 questions derived directly from nine approved, public Bureau of Internal Revenue PDFs. Candidate v2 corrects the known physical-page scopes in `KND-M5-CD-003` and `KND-M5-CD-010` without changing their expected facts. It remains `initial_expert_review_required`; the correction is not a substitute for the independent review and adjudication required by [`evaluation/cases/M5_GOLD_V2_REVIEW.md`](../evaluation/cases/M5_GOLD_V2_REVIEW.md). The source files and their approval records remain in the ignored local document repository. They must not be copied into Git. Expected facts in the tracked dataset are concise, non-sensitive assertions needed for evaluation; the preserved PDF bytes remain the evidence.

This sample is not evidence that an issuance is current, controlling, complete, or applicable to a taxpayer. It must not be used as tax advice. A supported evaluation answer means only that the named, checksum-verified sample page supports the answer in context.

## Source and version preconditions

Before any evaluation run:

1. Load the local `APPROVAL_MANIFEST.json` from the approved sample folder.
2. Require `approval_status` to be `approved` and the scope to permit local Kendra development and evaluation.
3. Require exactly the nine filenames recorded in the dataset's `documents` array.
4. Recalculate SHA-256 over each PDF and require an exact match with both the approval manifest and the dataset document entry.
5. Require every PDF to be readable, unencrypted, and to have the recorded physical page count.
6. Use one-based physical PDF page numbers. Printed page labels may be reported as additional context but do not replace physical page numbers.
7. Record the dataset Git revision, approval-manifest checksum, source-document checksums, and all pipeline, model, prompt, OCR, and tool versions used for the run.

A filename alone is not a sufficient version identity. For this bounded sample, filename plus SHA-256 identifies the evaluated bytes. A future governed document repository must add stable document and version identifiers without changing the meaning of the cases.

If any precondition fails, stop the run and report a source-integrity failure. Do not score answers against mismatched bytes.

## Dataset structure and coverage

Every case has:

- a stable `case_id`;
- a category;
- a question;
- an expected `supported` or `unsupported` result;
- atomic expected answer facts;
- one or more authoritative filenames representing the relevant corpus scope;
- expected physical page numbers for supported cases;
- unacceptable behavior;
- ambiguity notes; and
- an `ocr_required` flag.

The initial strata are:

| Category | Cases | Evaluation purpose |
|---|---:|---|
| Direct factual | 20 | Retrieve and state bounded facts, including dates, amounts, deadlines, and exceptions |
| List or table | 10 | Preserve completeness, row and column alignment, labels, amounts, and form layout |
| Cross-document comparison | 10 | Attribute each compared fact to the correct document and page without merging source roles |
| Deliberately unsupported | 10 | Reject questions that the approved corpus cannot answer |

Fourteen cases require the 12-page image-only circular. OCR-derived text is never authoritative: evaluators must verify those answers against the rendered source page.

## Run protocol

Use the same fixed configuration for every case in a comparable run. Randomize case order with a recorded seed so cache warming and fatigue do not consistently favor one category.

For each case:

1. Start the timer only after the complete question has been accepted by the system.
2. Preserve the exact input question and case ID outside Git as generated run data.
3. Allow access only to the checksum-verified approved sample collection.
4. Capture the final answer, supported/unsupported classification, citations, error state, and elapsed time.
5. Stop the timer when the complete answer and citations are available to the user. A timeout or unrecoverable error is recorded explicitly; it is not silently dropped.
6. Do not expose expected facts, expected pages, unacceptable behaviors, or ambiguity notes to the system under test.

Run cold-start and warm-run timing separately. A cold start includes model or service initialization specified by the test plan; a warm run starts from a ready system. Report whether OCR is precomputed or performed within measured latency.

## Answer correctness

### Atomic-fact scoring

Treat every string in `expected_answer_facts` as one required semantic fact. Review meaning, not exact wording.

For a supported case:

- **Fact true positive (TP):** a required fact is stated correctly and without a material qualification error.
- **Fact false negative (FN):** a required fact is absent, materially incomplete, or contradicted.
- **Fact false positive (FP):** the answer adds a material factual claim that is false, unsupported by the approved corpus, or attributed to the wrong source.

Calculate:

```text
fact precision = TP / (TP + FP)
fact recall    = TP / (TP + FN)
fact F1        = 2 * precision * recall / (precision + recall)
```

If a denominator is zero, record the metric as not applicable rather than manufacturing a perfect score.

A supported case passes answer correctness only when all required facts are present, no required fact is contradicted, and there is no material unsupported addition. Minor phrasing, punctuation, capitalization, or currency-symbol differences are acceptable when the amount, unit, date, condition, and meaning are unchanged.

List and table answers must also preserve:

- all requested items or rows;
- correct association between row labels and values;
- correct association between totals, MOOE, and CO columns;
- stated alternatives and exceptions; and
- centavos where the source reports them.

Cross-document answers must keep source roles separate. A fact supported by one document must not be presented as though both documents state it.

### Unsupported answers

An unsupported case has no expected answer facts. Answer correctness requires a clear statement that the approved corpus does not provide enough evidence to answer the question. It may identify the missing evidence or explain why a nearby passage is insufficient.

The answer fails if it guesses, relies on model memory, uses an external source, treats absence as proof, supplies a definitive answer with a disclaimer, or cites a merely related page as support.

## Citation correctness

Evaluate each citation attached to a material answer claim. A citation is correct only when all of the following are true:

1. the filename resolves to a PDF in the approved collection;
2. the resolved PDF matches the recorded SHA-256;
3. the cited one-based physical page exists;
4. the cited page supports the adjacent claim in context; and
5. the answer does not conceal a condition, exception, table heading, or continuation page needed to make the claim accurate.

For supported cases, calculate citation precision as:

```text
correct citations / all citations supplied
```

Also record citation completeness:

```text
required answer facts with at least one correct citation / all required answer facts
```

A citation to the right document but wrong page is incorrect. A citation to a page containing related terminology but not the asserted fact is also incorrect. Cross-document cases require correct citations to every document needed for the comparison. Unsupported cases should not cite a page as affirmative support; a page may be mentioned only to explain why a nearby fact does not answer the question.

## Correct-page citation rate

Correct-page citation rate isolates page mapping from general citation presence:

```text
required facts cited to an allowed page in expected_pages
--------------------------------------------------------
required facts for supported cases
```

One correct page may support several required facts when the page actually contains them. Conversely, a multi-page expected answer must cite every page necessary for its complete claim. Additional pages do not earn credit and count against citation precision when they do not support the adjacent claim.

Report this rate overall and separately for:

- direct factual cases;
- list or table cases;
- cross-document cases;
- OCR-required cases; and
- non-OCR cases.

Do not use an aggregate result to hide a low OCR or table-page score.

## Supported versus unsupported classification

Require the system to emit or permit adjudicators to assign one of two evaluation labels:

- `supported`: the approved corpus contains enough evidence for the material answer; or
- `unsupported`: it does not.

Compare the prediction with `expected_result` and build a confusion matrix where `supported` is the positive class:

| Gold / predicted | Supported | Unsupported |
|---|---:|---:|
| Supported | True positive | False negative |
| Unsupported | False positive | True negative |

Report accuracy, supported precision, supported recall, supported F1, and per-category counts. Keep classification scoring separate from answer and citation scoring: a response can classify a case correctly but still provide a wrong answer or wrong page.

## Unsupported rejection rate

Unsupported rejection rate is:

```text
unsupported cases that clearly reject a definitive answer
----------------------------------------------------------
all deliberately unsupported cases attempted
```

A correct rejection must not include a guessed answer. It should say that the supplied corpus provides insufficient evidence and, when useful, identify the missing status record, date range, field, metric, or source. Timeouts and generic failures do not count as safe rejections unless the user-visible result clearly avoids an unsupported answer and identifies that evidence was not established.

Also report the unsupported false-answer rate: deliberately unsupported cases on which any definitive factual answer was supplied.

## Response time

Measure monotonic elapsed time in milliseconds from accepted complete input to complete user-visible output, including citations. Record timeouts separately.

Report at minimum:

- attempted, completed, timed-out, and failed case counts;
- median, 90th percentile, and maximum latency;
- cold-start and warm-run results separately;
- latency by the four categories;
- OCR-required versus non-OCR latency; and
- document-table versus prose latency where the test plan can identify them consistently.

Do not discard failures or timeouts from the latency report. Report hardware, operating mode, concurrency, cache state, corpus state, and pipeline versions so results can be reproduced. This milestone sets no performance target because no working pipeline or measured baseline exists.

## Ambiguous cases

The `ambiguity_notes` field defines known interpretation boundaries. Before a scored release, two reviewers should independently confirm that each question has one reproducible scoring interpretation. If they disagree, an adjudicator must either refine the case, permit explicitly documented answer variants, or mark the case non-scorable for that run.

When a user question is genuinely ambiguous, acceptable system behavior is to:

- ask for the missing distinction; or
- give a bounded answer that states the interpretation used and preserves material alternatives.

The system must not silently choose a legally or numerically consequential interpretation. A response fails ambiguity handling when it merges different deadlines, confuses working with calendar days, swaps table columns, treats an example as exhaustive, or states currentness that the source set cannot establish.

Report ambiguous-case results separately as:

- correctly clarified or bounded;
- answer correct under an allowed interpretation;
- silently resolved with material risk; or
- non-scorable because the gold case itself requires revision.

## Human review and gold-set promotion

The current file is an initial gold-set candidate, not proof of domain-expert agreement. Before it governs a pilot decision:

1. Two reviewers independently open every named PDF at every expected page and verify each expected fact, condition, amount, and exception.
2. At least one reviewer must have suitable BIR or tax-domain competence for substantive questions; document and evaluation specialists may verify layout, page mapping, and scoring structure.
3. Reviewers record disagreements without changing the source PDFs.
4. An accountable adjudicator resolves disagreements or revises the case in Git with a reviewable rationale.
5. The dataset status changes only after case IDs, expected facts, pages, OCR flags, and unsupported boundaries are approved.

Inter-reviewer agreement should be reported for supported/unsupported labels and required-fact judgments. No target is imposed in this milestone; measured disagreement is evidence that the rubric or case needs clarification.

## Reporting and change control

Generated answers, traces, OCR output, screenshots, metrics, and reports are derived data and remain outside Git. A run report should identify the dataset Git revision and source checksums, then present:

- category counts and attempted-case counts;
- fact precision, recall, F1, and strict case pass rate;
- citation precision and completeness;
- correct-page citation rate;
- classification confusion matrix and metrics;
- unsupported rejection and false-answer rates;
- latency statistics and timeout counts; and
- results segmented by OCR, table or layout, category, and ambiguity status.

Changing an expected fact, page, support label, or unacceptable behavior requires review because it changes the benchmark. Preserve stable case IDs when meaning is unchanged. Retire rather than silently repurpose an ID when the question's substantive meaning changes.
