# Assumptions Register

**Status:** Requires interviews and field validation

**Last updated:** 2026-08-15

## How to use this register

An assumption is not a requirement or a fact. Each assumption below must be confirmed, narrowed, or rejected using the stated evidence. Interview opinions alone are insufficient where observation, document inspection, policy review, logs, or task measurement are available.

The only verified inputs currently available are:

- personnel search regulations, circulars, memoranda, procurement documents, and scanned records;
- documents may be confidential;
- connectivity may be unreliable;
- answers must be traceable to an authoritative page; and
- the repository requires citations to resolve to a stable document identifier, exact version or checksum, and source location, while treating OCR and indexes as derived rather than authoritative.

“Verified input” here means documented in the supplied brief or [source-of-truth policy](source-of-truth-policy.md), not independently confirmed in an agency.

## Assumptions requiring validation

| ID | Working assumption | Why it matters / risk if wrong | Validation evidence needed |
|---|---|---|---|
| U1 | The primary user is an action officer or technical analyst preparing or reviewing an official work product. | The wrong primary user would distort the task, language, controls, and pilot recruitment. | Interviews across candidate roles; observation of at least 8–12 real or recently completed research tasks; identify who searches, who decides, and who is accountable. |
| U2 | One primary workflow spans regulatory, memorandum, procurement, and scanned-record research. | These may be separate jobs with incompatible authority, review, and security needs. | Compare task maps, sources, handoffs, and acceptance criteria by role and document class. Split the product definition if materially different. |
| U3 | The user, rather than a records or legal specialist, performs most source discovery. | The actual bottleneck may be a handoff or service queue rather than search. | Shadow end-to-end cases and measure active work and wait time by role. |
| J1 | The core job is to produce a review-ready answer with exact page-level support. | Users may instead need only document retrieval, a complete case file, or formal legal interpretation. | Critical-incident interviews based on actual recent tasks; collect de-identified outputs and reviewer acceptance criteria. |
| J2 | Exact page is the accepted citation unit for all source types. | Some records may use section, clause, annex, paragraph, folio, image region, or no stable pagination. | Inspect representative originals and current citation practice; obtain records/legal guidance. |
| J3 | “Currently applicable” status can be established from available evidence. | If amendment, effectivity, or authenticity data is absent, the task cannot be safely completed as framed. | Trace document lifecycle and status-checking for a stratified sample; identify authoritative status owners and registers. |
| W1 | The manual workflow resembles the eight-step flow in [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md). | Improvements cannot be measured against an invented workflow. | Contextual inquiry and screen/desk observation; map variants, tools, rework, queues, and workarounds. |
| W2 | Search and evidence verification consume enough time to justify intervention. | The principal delay may occur elsewhere, such as approvals or document access requests. | Time-on-task study over representative cases; distinguish active search, waiting, reading, verification, and approval time. |
| W3 | Reviewers independently reopen source material and check citations. | If review is absent or purely procedural, adoption and safety controls need a different operating model. | Observe reviews; inspect redacted review comments and standard operating procedures; interview approvers. |
| W4 | Prior research is duplicated because it is difficult to locate or trust. | Reuse may be prohibited, rare, or not valuable because questions are highly specific. | Diary study and case sampling; measure repeated queries and conditions under which prior work is accepted. |
| D1 | Relevant documents are fragmented across repositories, email, local storage, and paper. | A single authoritative repository could make federation unnecessary; undocumented stores may be out of scope. | Repository inventory, access-path mapping, and observed retrieval attempts for real cases. |
| D2 | Scan quality and missing text layers are frequent material barriers. | OCR-related work may have low value if most active documents are born-digital and searchable. | Stratified corpus sample; measure image-only share, text extraction quality, language, layout, and task success. |
| D3 | A bounded, office-authorized corpus can cover most pilot tasks. | An unbounded or frequently changing corpus undermines offline completeness and evaluation. | For recent cases, list every relied-on source and its origin; measure corpus coverage and update frequency. |
| D4 | Originals have stable identifiers, versions, checksums, or enough metadata to create reliable provenance. | Citation guarantees are infeasible if originals and versions cannot be distinguished. | Records inventory and duplicate/version analysis; review document-control procedures. |
| D5 | Page images or equivalent preserved renditions are permitted in the target environment. | Page verification may conflict with storage, copyright, classification, or retention rules. | Written records, legal, privacy, and information-security review. |
| D6 | The corpus contains languages and mixed-language content that can be covered by one evaluation approach. | Performance may differ sharply across English, Filipino, regional languages, tables, stamps, and handwriting. | Corpus profiling and task testing segmented by language and content type. |
| C1 | Connectivity outages materially interrupt time-sensitive research. | “Unreliable” may be rare, predictable, or irrelevant to the actual work location. | Connectivity logs where permitted; two-week user diary; frequency, duration, location, and task impact. |
| C2 | The required offline mode is known and supportable. | A laptop with intermittent sync, an agency LAN, and a fully air-gapped site have different constraints. | Site/network assessment and security-architecture decision for each pilot location. |
| C3 | Authorized source updates can reach the offline environment within an acceptable time. | Stale documents could make offline answers more dangerous than no answer. | Map update ownership, approval, transfer, revocation, and maximum tolerated staleness; test an update cycle. |
| S1 | Some source content or query text may not be sent to public cloud services. | The actual rule may be stricter, looser, or classification-dependent; an incorrect assumption can block or expose the pilot. | Written classification, privacy, records, procurement, and information-security policies plus responsible-officer sign-off. |
| S2 | Access rules can be expressed and enforced at document or collection level in the pilot. | Paragraph-, case-, purpose-, or time-based restrictions may require a different control model. | Permission model review; role-to-document access matrix; adversarial access scenarios. |
| S3 | Search results, snippets, citations, logs, and prior queries inherit the sensitivity of their sources. | Metadata and derived artifacts may leak restricted facts even when originals are protected. | Data-classification decision and threat-model workshop; inspect logging and audit requirements. |
| S4 | Local/offline copies are permitted on the intended devices or servers. | Confidentiality does not automatically mean local storage is allowed. | Written endpoint, encryption, removable-media, physical-security, retention, and disposal requirements. |
| R1 | Exact source support is more important than a fluent answer. | Users may prefer speed until a failure occurs, affecting behavior and pilot interpretation. | Forced-choice task studies, review observations, and analysis of actual acceptance/rejection decisions. |
| R2 | Users will accept an explicit “not enough evidence” result. | Pressure for completion may lead users to bypass or mistrust safe failure. | Scenario interviews and observed pilot behavior on deliberately unanswerable or conflicting cases. |
| R3 | Expert adjudicators can agree whether a page supports a claim. | Low inter-rater agreement makes evaluation targets unreliable and exposes genuine policy ambiguity. | Double-blind adjudication of the pilot set; measure agreement and resolve rubric gaps. |
| R4 | Document status and substantive interpretation remain human-accountable decisions. | Stakeholders may expect automation to make determinations it cannot safely make. | Governance interviews and written responsibility/RACI review with legal, procurement, records, and approving officials. |
| P1 | A 30–40% time reduction is both material and achievable without reducing correctness. | Arbitrary targets may overstate value or reward unsafe speed. | Establish baseline distribution, value of staff time, minimum worthwhile improvement, and pilot feasibility. |
| P2 | A representative, permission-safe evaluation set can be assembled. | Without it, the pilot cannot measure accuracy, confidentiality, or offline performance credibly. | Data-governance approval; sampling plan by task, source, sensitivity, scan quality, and language. |
| P3 | The provisional accuracy and safe-failure targets in the product brief match task severity. | A single threshold may be unacceptable for high-impact decisions and excessive for low-risk discovery. | Risk-tier tasks with accountable domain owners; define material-error classes and thresholds per tier. |

## Validation sequence

1. **Workflow and user:** Resolve U1–U3, J1–J3, and W1–W4 before fixing a product boundary.
2. **Corpus and authority:** Resolve D1–D6 before making claims about coverage, citation feasibility, or currentness.
3. **Operating environment:** Resolve C1–C3 and S1–S4 before selecting a pilot site or moving any real documents.
4. **Evaluation and value:** Resolve R1–R4 and P1–P3 before agreeing to pilot acceptance criteria.

An assumption is considered validated only when the evidence, date, agency context, participant/sample, and decision owner are recorded. Contradictory evidence should remain visible rather than being averaged into a vague conclusion.
