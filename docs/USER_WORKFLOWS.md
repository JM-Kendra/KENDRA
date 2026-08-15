# User Roles and Workflow Hypotheses

**Status:** Discovery artifact; not field-validated

**Last updated:** 2026-08-15

## Evidence boundary and flagging convention

No interviews, workflow observations, agency policies, document samples, access matrices, or approval charts are available. The roles and workflows below are research hypotheses derived from the documented Kendra problem space; they are not descriptions of any particular agency.

- **REPOSITORY CONSTRAINT** — established by the existing [product brief](PRODUCT_BRIEF.md) or [source-of-truth policy](source-of-truth-policy.md). It still does not prove how an agency works.
- **CONFIRM** — must be confirmed, narrowed, or rejected by an actual employee of the pilot agency and, where appropriate, checked against written policy or observed work.

Unless a statement is explicitly labeled **REPOSITORY CONSTRAINT**, every role, trigger, document set, workflow step, decision, approval, consequence, and access rule in the role maps is labeled **CONFIRM**. No title below implies statutory authority, delegated authority, or an approval right.

## Cross-role boundary

**REPOSITORY CONSTRAINT:** Kendra is intended to help authorized personnel find document evidence and preserve exact source provenance. A verifiable citation must resolve to a stable document identifier, exact version or checksum, a location within that version, and the pipeline or Git revision that produced the cited representation. Derived text, including OCR output, is not authoritative evidence.

**REPOSITORY CONSTRAINT:** Kendra must not treat a generated result as records, legal, procurement, policy, or operational approval. Document status, applicability, substantive interpretation, release, and final action remain human decisions unless future agency evidence establishes a narrower, lawful system role.

## Role 1: Records officer

**CONFIRM — role hypothesis:** A records officer or locally equivalent custodian receives requests to locate an office record, establish which preserved copy or version should be consulted, and provide permitted access or a traceable reference. Confirm the actual title, responsibilities, authority, and frequency of this work.

| Workflow element | Hypothesis requiring agency confirmation |
|---|---|
| Trigger for using the system | **CONFIRM:** An employee, reviewer, auditor, or other permitted requester asks for a named record or evidence about a subject, date, transaction, or document history. Confirm who may submit each request and whether urgent, public, audit, legal-hold, or internal requests follow different paths. |
| Documents involved | **CONFIRM:** Possible materials include document registers, memoranda, circulars, correspondence, scanned records, transmittal or routing records, version histories, retention schedules, and access or classification instructions. Confirm the authoritative repository and accepted evidence for every in-scope class. |
| Current steps | **CONFIRM:** The officer may (1) receive and clarify the request; (2) determine requester identity, purpose, scope, and access; (3) search registers, repositories, shared folders, or physical holdings; (4) compare identifiers, dates, versions, attachments, and status; (5) inspect the original or preserved rendition; (6) prepare a permitted copy, reference, or “not found” response; and (7) record the handoff or escalation. Observe real cases to confirm steps, order, tools, queues, and exceptions. |
| Decisions made by the user | **CONFIRM:** The officer may decide which candidate record matches the request, whether the record is complete, which version is appropriate to surface, whether access or release is permitted, and when another custodian or authority must decide. Confirm which of these are decisions, recommendations, or prescribed checks. |
| Expected output | **CONFIRM:** A located record or permitted copy, a stable reference to the exact version and location, relevant provenance or status metadata, and an explicit outcome such as found, not found, access not established, or needs escalation. Confirm the required format, metadata, delivery channel, and audit trail. |
| Required approvals | **CONFIRM:** Unknown. Determine whether retrieval, viewing, copying, release, redaction, declassification, disposal, or access exceptions require approval; identify the responsible role and written basis for each. Do not infer approval authority from the “records officer” title. |
| Consequences of failure | **CONFIRM:** Possible consequences include returning the wrong or incomplete version, failing to locate a required record, disclosing restricted information, delaying a service or review, weakening an audit trail, or mishandling retention or legal-hold obligations. Validate actual incidents, likelihood, severity, and escalation requirements. |
| Information-access restrictions | **CONFIRM:** Determine whether access is controlled by document, collection, case, purpose, role, office, time, classification, privacy status, or physical custody. Confirm whether an unauthorized user may learn that a record exists and whether snippets, metadata, citations, queries, logs, and derived text inherit source restrictions. |

## Role 2: Frontline employee

**CONFIRM — role hypothesis:** A frontline employee or locally equivalent service staff member handles a citizen-facing or internal request and consults office-authorized guidance before preparing a response, completing a step, or referring the matter. Confirm whether this role searches documents directly or relies on a specialist.

| Workflow element | Hypothesis requiring agency confirmation |
|---|---|
| Trigger for using the system | **CONFIRM:** A request, case, application, inquiry, or unusual fact pattern requires the employee to check a rule, procedure, eligibility condition, documentary requirement, deadline, or escalation path. Confirm the actual recurring triggers and which are safe for a pilot. |
| Documents involved | **CONFIRM:** Possible materials include regulations, circulars, memoranda, service manuals, procedure guides, approved forms, checklists, advisories, and scanned office issuances. Confirm which sources are authoritative, current, locally applicable, and permitted for the role. |
| Current steps | **CONFIRM:** The employee may (1) record the request and relevant facts; (2) identify the issue and applicable service context; (3) search available guidance or ask a colleague; (4) open candidate sources; (5) compare the passage with the case facts and check document status; (6) prepare a response, next step, or referral with supporting evidence; and (7) obtain review when required. Observe real work to confirm steps, handoffs, time pressure, and workarounds. |
| Decisions made by the user | **CONFIRM:** The employee may decide which guidance appears relevant, whether the available evidence is sufficient, whether the case fits a routine path, and when to pause or refer it. Confirm which determinations the employee is authorized to make and which must remain with a supervisor or specialist. |
| Expected output | **CONFIRM:** A concise evidence packet for the employee—candidate passage, exact source version and location, enough surrounding context to verify it, and a clear indication of insufficient, conflicting, unavailable, or unauthorized evidence. Confirm whether the operational output is a response, checklist, case note, referral, or another artifact. |
| Required approvals | **CONFIRM:** Unknown. Identify which responses, exceptions, denials, certifications, transactions, referrals, or case actions require supervisory or specialist review. Do not assume routine frontline work is approval-free. |
| Consequences of failure | **CONFIRM:** Possible consequences include inconsistent service, an incorrect requirement or next step, missed deadlines, avoidable repeat visits or rework, delayed public service, unsupported commitments, privacy exposure, or escalation of a preventable dispute. Validate actual frequency, severity, and affected parties. |
| Information-access restrictions | **CONFIRM:** Determine whether the employee may search only public guidance, internal procedures, assigned cases, or particular collections. Confirm the treatment of personal data, case files, restricted issuances, search history, cached results, printed material, and access during offline operation. |

## Role 3: Policy, procurement, or legal reviewer

**CONFIRM — role-family hypothesis:** A policy, procurement, or legal reviewer—or a locally equivalent specialist—checks a proposed action or work product against authoritative sources and records supported comments or a recommendation. These may be three materially different roles and workflows; research must split them if their sources, duties, controls, or risks differ.

| Workflow element | Hypothesis requiring agency confirmation |
|---|---|
| Trigger for using the system | **CONFIRM:** A draft policy, memorandum, procurement action, contract-related document, recommendation, response, exception, protest, audit issue, or disputed case is submitted for specialist review. Confirm the in-scope review event, initiator, deadline, and risk tier. |
| Documents involved | **CONFIRM:** Possible materials include laws, implementing rules, regulations, circulars, memoranda, procurement records, solicitation and bid documents, contracts, technical specifications, prior opinions, audit guidance, delegations, and the draft under review. Confirm which classes can lawfully share a corpus and which authority or register establishes currentness. |
| Current steps | **CONFIRM:** The reviewer may (1) clarify the proposed action and review question; (2) identify jurisdiction, date, material facts, and required standard; (3) locate candidate authorities and case-specific documents; (4) verify source identity, status, completeness, and access; (5) read passages in context and cross-reference amendments, exceptions, annexes, or related instruments; (6) document supported findings, uncertainty, and requested revisions; and (7) route the work product under the applicable review process. Observe actual reviews to confirm sequence, depth, collaboration, and rework. |
| Decisions made by the user | **CONFIRM:** The reviewer may assess relevance, currentness, applicability, conflict, sufficiency of support, material risk, need for further facts, and whether to recommend clearance, revision, escalation, or another action. Confirm the exact decision rights for each role; Kendra must not make these determinations on the reviewer’s behalf. |
| Expected output | **CONFIRM:** A review packet containing claim-level source references, exact versions and locations, relevant context, conflicts or gaps, and human-authored findings or comments. Confirm whether the accepted artifact is a review note, legal opinion, procurement recommendation, redline, clearance, checklist, or other record. |
| Required approvals | **CONFIRM:** Unknown and likely workflow-specific. Identify who may issue, concur in, clear, sign, or approve each output; which reviews are mandatory; whether segregation of duties applies; and what written delegation supports those roles. Do not infer hierarchy or authority from a job title. |
| Consequences of failure | **CONFIRM:** Possible consequences include relying on an obsolete or inapplicable authority, unsupported policy or procurement action, delay, rework, challenge, disallowance, audit finding, unequal treatment, financial loss, legal or administrative exposure, or disclosure of protected information. Validate actual failure modes, likelihood, materiality, and stop conditions by workflow. |
| Information-access restrictions | **CONFIRM:** Determine whether access is limited by case assignment, procurement stage, privilege or confidentiality, personal or supplier information, deliberative status, office, purpose, or need to know. Confirm whether cross-case search is permitted and how citations, excerpts, annotations, queries, logs, and prior work products are protected. |

## Cross-role handoffs to investigate

Each handoff below is a **CONFIRM** hypothesis, not an agency process:

1. **CONFIRM:** A frontline employee may request a source or version check from a records officer when the needed document is missing, ambiguous, or access-controlled.
2. **CONFIRM:** A frontline employee may refer interpretation, exception, procurement, or higher-risk questions to an appropriate reviewer.
3. **CONFIRM:** A reviewer may ask a records officer to authenticate, complete, or trace a document set before relying on it.
4. **CONFIRM:** A records officer may provide evidence and custody metadata without deciding substantive applicability.
5. **CONFIRM:** A reviewer or other authorized official may return the work for more research when support is incomplete, conflicting, or inaccessible.

Research must identify the real initiator, receiving role, information passed, approval state, queue time, rejection reason, and audit record for each observed handoff.

## Smallest workflow worth automating in the MVP

### Proposed boundary

**PROPOSED MVP — CONFIRM:** The smallest candidate is **authorized retrieval of one relevant passage from a bounded, pre-approved corpus, followed by creation of a verifiable citation packet for human review**. “Worth automating” has not been established; select this workflow only after agency employees confirm that it is frequent enough, costly enough, and safe enough to justify a pilot.

The candidate workflow is deliberately assistance, not decision automation:

1. **CONFIRM:** An authorized user enters a document question and, where required, a date, office, document class, or case-safe filter.
2. **REPOSITORY CONSTRAINT:** The system searches only sources the user is authorized to access; a locally available copy or derived index must not bypass source permissions.
3. **REPOSITORY CONSTRAINT:** The system returns a candidate passage only when it can resolve the result to the preserved source identifier, exact version or checksum, and exact location.
4. **REPOSITORY CONSTRAINT:** The user opens the source at that location and judges relevance, context, currentness, and applicability.
5. **CONFIRM:** The user exports or records the agency-accepted citation packet and routes it through the existing review or approval process, if any.
6. **REPOSITORY CONSTRAINT:** If permitted evidence is absent, conflicting, unresolved, or not verifiable, the system must not provide a definitive answer and must communicate the limitation.

### Candidate output

**PROPOSED MVP — CONFIRM:** A candidate packet would contain the query, selected passage with enough context for review, document title and identifier, exact version or checksum, page or other accepted location, provenance, retrieval time, and an explicit limitation/status indicator. Confirm the minimum useful fields, whether query retention is permitted, and the approved export or handoff format.

### Explicit exclusions

The proposed MVP does not:

- determine legal or policy applicability;
- establish that a source is current or controlling without authoritative status evidence;
- approve release, service eligibility, a procurement action, a policy, a legal position, or any other official action;
- replace records custody, a document register, case management, or the agency’s approval workflow;
- search across collections or reveal metadata that the user is not authorized to access; or
- silently convert OCR, an index, a summary, or generated text into authoritative evidence.

## Validation needed before selecting an MVP role

All items below are **CONFIRM** questions for actual employees and accountable policy owners:

1. Which of the three roles performs the candidate retrieval-and-citation task most often?
2. Which single recurring task has sufficient volume and measurable search or review cost?
3. Can that task be bounded to a permission-safe corpus with authoritative version and status evidence?
4. What decisions and approvals must remain outside the system?
5. What is the accepted citation packet, and can a reviewer independently reopen the exact source location?
6. Which failure modes make the task unsuitable for automation or require an immediate human escalation?
7. What written access, privacy, records, security, and offline-storage rules apply to source documents and every derived artifact?
8. What observed manual baseline and reviewer-accepted evaluation set will show whether the workflow is actually worth automating?

Until these questions are answered, the MVP role, corpus, approval path, and operational value remain **unconfirmed**.
