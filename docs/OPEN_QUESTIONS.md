# Open Questions for Discovery

**Status:** Unanswered

**Last updated:** 2026-08-15

These questions convert the assumptions in [ASSUMPTIONS.md](ASSUMPTIONS.md) into a field-research agenda. None should be treated as answered by this document. Questions marked **pilot blocker** must be resolved before real agency documents or users enter a pilot.

## 1. User, accountability, and job

1. **Pilot blocker:** Which role actually performs the search most often, and which role is accountable when the resulting answer is wrong?
2. What are the local job titles for the searcher, reviewer, records custodian, subject-matter expert, and final approver?
3. Which one recurring task creates the highest combination of search volume, time cost, and consequence of error?
4. Do regulatory, circular, memorandum, procurement, and scanned-record searches belong to one workflow or several distinct workflows?
5. What does a “review-ready” result contain today, and who decides that it is sufficient?
6. When must the user retrieve a document only, and when must the user synthesize an answer across documents?
7. Which judgments must remain with legal, procurement, records, audit, or approving officials?

## 2. Current workflow and baseline

1. Walk through the last completed case from request to approved output. What triggered each step and handoff?
2. Where did the user search, in what order, and why did they trust or distrust each source?
3. How much elapsed and active time was spent locating, opening, reading, cross-checking, citing, reviewing, and reworking?
4. What query terms, filename conventions, registers, colleagues, paper files, or personal workarounds were used?
5. How were amendments, supersession, effectivity, authenticity, completeness, and applicability checked?
6. How was the exact supporting page captured and handed to the reviewer?
7. Where did the case stall, repeat a search, or return from review?
8. Which parts of the workflow differ for urgent, routine, confidential, procurement, and audit-related work?
9. What baseline error, rework, and review-return rates can be measured without exposing sensitive content?

## 3. Source authority and citation

1. **Pilot blocker:** For each document class, which repository, custodian, publication, seal/signature, register, or process establishes the authoritative version?
2. **Pilot blocker:** How is a withdrawn, amended, superseded, expired, or revoked document identified, and how quickly is that status propagated?
3. Are page numbers stable across the preserved original, printed copy, scan, and any normalized rendition?
4. Where page numbers are absent or unreliable, what location reference is accepted: section, clause, annex, folio, paragraph, or image region?
5. Are attachments, annexes, tables, marginal notes, stamps, signatures, and handwritten annotations part of the authoritative record?
6. Can reviewers always open the exact cited version, or do permissions and physical custody sometimes prevent it?
7. What metadata is mandatory for a defensible citation in each workflow?
8. How are conflicts between two apparently authoritative documents resolved, and by whom?
9. What should happen when a relevant passage is found but currentness, authenticity, or applicability cannot be established?

## 4. Corpus characteristics

1. How many documents, pages, versions, and new or changed documents are in the intended scope?
2. What proportion is born-digital, image-only, low-quality scan, handwritten, tabular, or contains complex annexes?
3. Which languages, mixed-language patterns, abbreviations, document-number conventions, and historical orthography occur?
4. How often are files incomplete, duplicated, mislabeled, rotated, out of order, or missing pages?
5. Which sources live only in email, personal drives, removable media, physical archives, or systems outside the pilot office's control?
6. What percentage of recent real tasks could be answered from a bounded, office-authorized corpus?
7. What retention, disposal, legal-hold, and records-management rules apply to originals and derived representations?

## 5. Confidentiality, privacy, and security

1. **Pilot blocker:** What classification or sensitivity scheme applies to documents, queries, snippets, citations, answers, logs, and usage metadata?
2. **Pilot blocker:** Who may authorize ingestion, local storage, processing, testing, and user access for each class?
3. **Pilot blocker:** May any document content, query, metadata, or diagnostic information leave the agency network or device? Under what written authority?
4. Are permissions document-level, collection-level, case-level, purpose-bound, time-bound, or more granular?
5. Can a user learn that a restricted document exists even when they cannot open it?
6. What authentication, session, screen-lock, physical-access, encryption, removable-media, backup, and key-management rules apply offline?
7. What audit events must be recorded, who may inspect them, and how long are they retained?
8. What is the incident process for an unauthorized result, lost device, corrupted source, or disclosure in a log?
9. How must access revocation and document withdrawal propagate to disconnected environments?
10. What data may be used for evaluation, demonstrations, screenshots, support, and defect reproduction?

## 6. Offline operating model

1. **Pilot blocker:** Does “offline” mean an intermittently connected workstation, an agency LAN without internet, a transportable deployment, or a fully air-gapped environment?
2. Where will authoritative source copies reside during disconnection, and is that storage authorized?
3. How long must the core workflow operate without any network connection?
4. How often can source, permission, revocation, and software updates be transferred into the environment?
5. Who approves and performs updates, using what media or network path, and how are integrity and provenance checked?
6. What maximum source staleness is acceptable by task type? What happens after that limit?
7. Which dependencies are currently available only online, including identity, document repositories, time sources, or license checks?
8. What degraded behavior is acceptable when a required source or permission update is unavailable?
9. How will an offline test prove that no unintended external request or content transmission occurred?

## 7. Error consequences and safe failure

1. Which wrong-answer scenarios have occurred or nearly occurred, and what caused them?
2. What is the consequence and likelihood of citing a wrong page, wrong version, incomplete context, inapplicable rule, or unauthorized source?
3. Which tasks are too consequential for a generated synthesis and should be limited to evidence retrieval and human review?
4. What wording clearly communicates “not found,” “not authorized,” “conflicting evidence,” “possibly superseded,” and “insufficient evidence” without misleading the user?
5. When is abstention operationally safer, and when could failure to surface partial evidence itself cause harm?
6. Who adjudicates disputed answers during a pilot, and how are disagreements recorded?
7. What events require the pilot to pause immediately?

## 8. Pilot design and measurable value

1. **Pilot blocker:** Which single office, user group, document corpus, and recurring task provide a bounded and representative first pilot?
2. **Pilot blocker:** Can accountable experts create and independently adjudicate a permission-safe task set containing answerable, unanswerable, conflicting, superseded, and unauthorized cases?
3. What manual baseline will be measured, over how many users and tasks, and with what controls for task difficulty and learning effects?
4. What minimum time saving is operationally meaningful without reducing correctness or increasing review burden?
5. What claim-level support threshold is required for each severity tier?
6. How will citation resolvability, page support, currentness checks, safe failure, permission containment, and offline containment be tested separately?
7. Which document types, languages, scan qualities, confidentiality levels, and connectivity modes must be represented and reported separately?
8. What onboarding and support are realistic, and what unassisted task-success level constitutes adoption?
9. Who owns go/no-go decisions, and what thresholds or safety events determine stop, revise, or expand?

## Suggested research evidence

To answer the questions without relying on stated preferences alone, collect a small but diverse evidence set:

- contextual interviews using recent completed cases rather than hypothetical future behavior;
- direct observation of search, citation, handoff, and review;
- redacted or synthetic examples of requests, final work products, citations, and review feedback;
- a repository and document-lifecycle map;
- a stratified, authorized corpus sample for scan and metadata inspection;
- applicable records, privacy, classification, security, procurement, and audit policies;
- measured task timings and review/rework outcomes; and
- a threat-model and pilot-governance workshop with named decision owners.

All research collection must follow the agency's authorization, confidentiality, privacy, retention, and records-handling rules. No restricted source content should be placed in this Git repository.
