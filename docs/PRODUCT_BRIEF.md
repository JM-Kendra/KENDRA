# Product Brief: Traceable Government Document Search

**Status:** Discovery brief; not yet field-validated

**Last updated:** 2026-08-15

## Evidence standard

This brief uses two labels:

- **Verified input** means the statement is explicitly documented in the project brief or an existing repository policy. It does not mean it has been confirmed through user research, observation, or operational data.
- **Assumption** means a working hypothesis that must be tested with users, documents, workflow observation, or pilot evidence before it becomes a product requirement.

Current evidence is limited to:

1. the problem statement supplied for this research on 2026-08-10; and
2. the repository's [source-of-truth policy](source-of-truth-policy.md).

No user interviews, field observations, workflow measurements, document samples, security classifications, or agency policies were supplied. Accordingly, the proposed user, workflow, pains, risks, and targets below remain assumptions unless explicitly marked otherwise.

## Problem definition

### Verified inputs

- Government personnel must search regulations, circulars, memoranda, procurement documents, and scanned records.
- Some documents may be confidential.
- Internet connectivity may be unreliable.
- Answers must be traceable to an authoritative page.
- Kendra is intended to be an offline, citation-verifiable document intelligence platform for Philippine government offices. This is documented project intent, not evidence of user demand or technical feasibility.
- The original document version—not extracted text, OCR output, chunks, or an index—is authoritative evidence. A verifiable citation must resolve to a stable document identifier, exact version or checksum, and location in that version. Source versions must not be silently replaced.

### Problem hypothesis

Staff spend avoidable time locating the controlling passage for an official task and reconstructing enough provenance for another person to verify it. Fragmented storage, scans, uncertain document status, confidentiality constraints, and poor connectivity may make that work slow and error-prone. This hypothesis has not yet been observed in the field.

## Primary user

**Assumption — primary user:** A Philippine government **action officer or technical analyst** who prepares or reviews an official recommendation, response, procurement action, or internal decision and must support it from an office-authorized document corpus.

The title is intentionally provisional. The defining characteristics are that this person:

- is accountable for the accuracy of a work product;
- searches across more than one of the named document classes;
- must show the exact evidence to a reviewer or approver;
- may handle restricted material; and
- must sometimes work without dependable internet access.

Records officers, legal officers, procurement officers, auditors, approvers, and IT/security administrators are possible secondary or adjacent users. Research must determine whether one of them is actually the primary user or whether the workflows are too different to share one product definition.

## Exact job to be done

**Assumption:**

> When I am preparing or checking an official government action, help me find the currently applicable passage in the documents I am authorized to use and assemble an answer whose exact source page and version a reviewer can independently verify, within the time available and even when the internet is unavailable, without disclosing restricted information.

“Currently applicable” is itself a risky assumption: document effectivity, amendments, supersession, and local applicability may require expert judgment that a search system cannot determine on its own.

## Current manual workflow

The following is a workflow hypothesis, not an observed process:

1. The officer receives a question or task and determines its subject, deadline, jurisdiction, relevant date, and confidentiality.
2. The officer identifies likely document types, issuers, repositories, file shares, email threads, physical files, or colleagues who may hold the source.
3. The officer searches filenames, folders, document registers, PDF text, OCR text where available, or pages through scans manually.
4. The officer opens candidate documents and checks title, issuer, document number, date, effectivity, amendments or supersession, completeness, and access marking.
5. The officer reads the relevant pages and cross-references related documents to determine what passage supports the work product.
6. The officer records or copies the answer and its provenance—at minimum the document identity and page—and may save a screenshot, excerpt, link, or copy for review.
7. A reviewer or approver reopens the source, verifies the passage and context, and asks for further research if the support is incomplete or ambiguous.
8. The officer finalizes the work product and retains whatever evidence or audit trail the office requires.

Research must document actual variations, handoffs, tools, workarounds, review rules, and time spent at each step.

## Pain points to validate

All items in this section are assumptions.

- **Discovery friction:** Relevant material may be split across shared drives, document systems, email, local devices, or paper, with inconsistent names and metadata.
- **Scanned-document friction:** Image-only or poor-quality scans may make keyword search ineffective and force page-by-page review.
- **Authority ambiguity:** Finding a matching passage does not prove that the document is complete, authentic, in force, applicable, or the latest authorized version.
- **Citation reconstruction:** Staff may find text without retaining the exact page, version, and context needed for independent verification.
- **Cross-document reasoning:** Amendments, implementing circulars, exceptions, and procurement attachments may require several documents to answer one question.
- **Connectivity interruptions:** A remote service or cloud-held source may be unavailable during the task.
- **Confidentiality constraints:** Staff may be unable to upload restricted documents or queries to an external service, even when doing so would be convenient.
- **Duplicated effort:** Staff and reviewers may repeat searches because prior research is hard to locate or trust.
- **Review burden:** Reviewers may spend substantial time retracing how an answer was produced instead of checking a clear evidence trail.

## Consequences of an incorrect answer

These are severity hypotheses; their likelihood and relevance vary by workflow and must be validated with legal, procurement, records, audit, and operational personnel.

- An official action may rely on a superseded, incomplete, or inapplicable rule.
- A procurement decision may be delayed, challenged, disallowed, or repeated.
- Funds, staff time, or public services may be misallocated or delayed.
- A person or supplier may receive inconsistent treatment or an incorrect decision.
- The agency may face audit findings, administrative or legal exposure, missed deadlines, or reputational harm.
- Restricted information may be disclosed to an unauthorized person or external system.
- A plausible but unsupported answer may create false confidence and propagate into later memoranda or decisions.

The product must therefore optimize for verifiable support and safe uncertainty, not merely fast or fluent answers.

## Why offline operation matters

### Verified inputs

- Connectivity may be unreliable.
- Documents may be confidential.
- The project describes itself as intended for offline operation.

### Assumptions to validate

- Loss of internet access occurs often enough, and for long enough, to block time-sensitive document research.
- Some offices prohibit or discourage transmitting particular documents, excerpts, metadata, or queries to external services.
- The necessary authorized source corpus can be made available in the relevant offline environment and kept current through an approved process.
- “Offline” may mean disconnected workstation, agency local network, intermittent synchronization, or fully air-gapped site; these modes are not interchangeable.

Offline operation matters only if the full core task remains possible in the intended disconnected environment: locating evidence, opening the exact source page, and verifying provenance. Offline capability must not be used to bypass access controls, retention rules, classification policy, or source-version governance.

## What the system must never do

The first two constraints are directly supported by the existing source-of-truth policy. The others are proposed safety boundaries that require agency validation.

1. **Never present derived text as authoritative evidence** when it cannot resolve to the exact source document version and location.
2. **Never silently replace a source version** or make an old citation resolve to changed bytes.
3. **Never invent a passage, page, document, version, status, or citation.**
4. **Never state or imply that a document is current, controlling, authentic, or applicable without evidence sufficient for that claim.**
5. **Never hide uncertainty or provide a definitive answer when the available authorized sources do not support one;** it must clearly indicate that support was not found or is ambiguous.
6. **Never reveal the existence, metadata, contents, excerpts, queries, or search history of restricted material to an unauthorized user or system.**
7. **Never bypass source permissions because a copy, OCR result, index entry, cache, or prior answer is locally available.**
8. **Never transmit restricted content to the public internet or an external model or service unless an explicit agency policy and authorization allow it.**
9. **Never alter the preserved original document or allow OCR, summarization, or human annotation to masquerade as the original text.**
10. **Never combine claims from multiple documents in a way that conceals which source supports each claim.**
11. **Never treat a generated answer as legal, procurement, records, or policy approval;** accountable personnel retain the decision and review role.

## Pilot outcomes and provisional success measures

Targets below are assumptions for planning, not validated commitments. Before the pilot, the team must define a representative, permission-safe task set, an expert-adjudicated answer key, severity classes, and a measured manual baseline.

| Outcome | Measure | Provisional pilot target |
|---|---|---|
| Faster evidence finding | Median time from receiving a task to opening the first page that an expert adjudicator accepts as relevant, compared with the same users' manual baseline | At least 40% lower |
| Faster supported completion | Median time to produce a review-ready answer with its evidence trail, compared with baseline | At least 30% lower |
| Exact traceability | Share of submitted answer claims whose citation resolves to the preserved source version and exact supporting page | 100% |
| Evidence correctness | Share of cited claims for which expert reviewers agree that the cited page supports the claim in context | At least 95%; 100% for pilot-defined critical claims |
| Safe failure | Share of tasks with absent, insufficient, conflicting, or unauthorized evidence where the system avoids a definitive unsupported answer | 100% for the adjudicated pilot set |
| Offline task completion | Share of designated core tasks completed while network access is disabled, using the pre-authorized local corpus | At least 95% |
| Offline containment | Unexpected external network requests during designated offline tests | Zero |
| Permission containment | Unauthorized documents, excerpts, metadata, or prior-user search history exposed in results or logs during adversarial access tests | Zero |
| Review efficiency | Median reviewer time to verify source support, compared with baseline | At least 30% lower |
| User task success | Participants who complete the core task without facilitator intervention after onboarding | At least 80% by the end of the pilot |

Results must be segmented by document type, scan quality, language, confidentiality level, connectivity mode, and task severity. An aggregate score must not conceal a dangerous failure mode.

## Scope discipline

The discovery scope is limited to the documented workflow: finding authorized documents, identifying relevant passages, preserving source identity and page-level provenance, supporting review, and completing that work under the required connectivity and confidentiality conditions.

No broader capability—such as drafting official decisions, automating approvals, replacing records management, predicting outcomes, or providing general-purpose chat—should enter scope unless field evidence shows it is necessary to complete this job safely.

## Decision needed after discovery

Proceed to a pilot only if research confirms a recurring, high-cost search-and-verification workflow; identifies a coherent primary user and corpus; establishes an agency-approved confidentiality and offline operating model; and yields a representative evaluation set with accountable expert adjudicators.
