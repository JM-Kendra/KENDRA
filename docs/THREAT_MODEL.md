# Threat Model

**Status:** Design-time baseline; no security controls are implemented or verified by this document

**Last updated:** 2026-08-15

## Purpose, scope, and evidence limits

This threat model identifies foreseeable threats to Kendra's planned offline, citation-verifiable document retrieval workflow. It covers document intake, local storage, a future NAS boundary, PostgreSQL, extraction and indexing, vector retrieval, source viewing, audit, backup, recovery, and AI-assisted outputs.

The repository contains no runnable system or agency deployment evidence. Likelihood, exposure, control effectiveness, and residual risk are therefore **unknown**. Impact ratings below are provisional design priorities, not measured risk scores. Agency security, privacy, records, legal, procurement, and operational owners must validate the deployment model and risk acceptance before real documents or users enter a pilot.

This document defines threats and future control objectives only. It does not implement or claim authentication, authorization, encryption, malware scanning, parser sandboxing, prompt-injection defenses, monitoring, backup, or incident response.

Kendra is not a decision authority. An AI-generated answer or citation packet must never be treated as an official government decision, approval, legal opinion, procurement determination, or proof that a document is authentic, effective, controlling, or applicable.

## 1. Security objectives and protected assets

| Objective | Assets and required property |
|---|---|
| Source integrity | Exact original bytes, document/version identity, SHA-256 checksum, custody, and resolvable citation location must not be altered or silently substituted |
| Confidentiality and privacy | Source contents, PII, existence, metadata, queries, results, citations, logs, exports, backups, chunks, and embeddings must be visible only for an authorized purpose |
| Availability and recoverability | Authorized users must be able to recover the exact source versions and governed operational state within agency-approved objectives |
| Retrieval integrity | Derived text and index results must map to the correct admitted version, pipeline generation, and source location without masquerading as authority |
| Authorization integrity | Local copies, caches, indexes, backups, and offline operation must not bypass current source access decisions |
| Accountability | Material ingestion, access, status, administrative, index, export, backup, recovery, and incident actions must be attributable and reviewable |
| Human decision control | Generated content must not displace accountable review or be misrepresented as an official action |

## 2. Actors and trust assumptions

- **Authorized users** may make mistakes, over-trust outputs, mishandle exports, or deliberately exceed their permitted purpose.
- **Uploaders and custodians** may admit the wrong file, misclassify status, omit an attachment, or abuse privileged access.
- **System, storage, database, backup, and NAS administrators** can affect broad availability and integrity and may have technical access beyond their business need.
- **External attackers** may seek credentials, physical access, removable-media access, service vulnerabilities, or stolen backups.
- **Document suppliers** may be mistaken, compromised, or malicious; the contents and structure of every uploaded document are untrusted input even when its stated issuer is trusted.
- **Software, model, parser, OCR, and dependency suppliers** may introduce vulnerable, compromised, or behavior-changing components.
- **Reviewers and auditors** are trusted only within their documented authority and purpose.

No role, device, network segment, file share, document, model output, or derived index is inherently trusted. Trust must be limited to an approved identity, purpose, scope, and time.

## 3. Trust boundaries

| Boundary | Data crossing | Primary threats | Required design decision/control objective |
|---|---|---|---|
| User or administrator to Kendra | Credentials, queries, document access, exports, privileged actions | Impersonation, stale sessions, privilege abuse, shared-device exposure, unauthorized purpose | Agency identity model, least privilege, session/physical controls, privileged-action review, denial behavior |
| Upload/import to quarantine | Original bytes, filenames, claimed provenance and status | Malicious file, spoofed source, decompression bomb, parser exploit, duplicate or incomplete document | Authorized intake, quarantine, size/type limits, safe inspection, custody validation, no ordinary retrieval before admission |
| Quarantine to authoritative document repository | Approved bytes, checksum, custody decision | Silent alteration, wrong version, incomplete annex, approval bypass | Immutable version admission, independent review where required, checksum and completeness verification, audit |
| Document repository to processing pipeline | Source bytes and version manifest | Parser/OCR compromise, content-based prompt injection, data poisoning, leakage to temporary files | Treat content as hostile data, isolate processing, restrict capabilities, preserve source/page mapping, clear protected temporary data |
| Application/service to PostgreSQL | Derived metadata, authorization references, provenance, jobs, audit references | Injection, unauthorized changes, metadata leakage, corruption, availability loss | Validated data paths, scoped service identity, integrity constraints, backup/reconciliation, fail-closed source resolution |
| Application/service to vector index | Queries, embeddings, filters, source pointers, results | Cross-collection leakage, stale filters, poisoned hits, orphan pointers, index tampering | Index is non-authoritative, enforce authorization outside the index, generation/version binding, rebuild and validation |
| Derived result to preserved source viewer | Passage, citation, document/version/location | Wrong-page mapping, checksum mismatch, inaccessible source, deceptive snippet context | Resolve and verify exact source before support is claimed; expose uncertainty and sufficient context |
| Local host to future NAS | Originals, manifests, permissions, backups | Credential theft, share misconfiguration, network interception, outage, rollback to stale snapshot, hostile administrator | Approved network/identity boundary, least privilege, integrity checks, snapshot semantics, failover and reconciliation plan |
| Primary systems to backup/restore environment | Originals, database state, manifests, audit evidence, keys | Backup theft, ransomware propagation, incomplete backup, failed or over-broad restore | Separate failure domain, same-or-stronger access rules, protected keys, restore tests, checksum and permission reconciliation |
| Offline environment to update/export media | Documents, software, permissions, revocations, exports, logs | Malware import, stale authorization, data exfiltration, untracked copies, rollback | Approved transfer process, provenance/integrity verification, media custody, export authorization, revocation/staleness limits |
| Kendra output to human workflow | Excerpts, summaries, answers, citations, limitations | Automation bias, omission of contrary evidence, unofficial decision use | Persistent non-decision warning, exact source access, human review, safe uncertainty, existing approval workflow |

## 4. Threat and misuse-case register

“Required response” below is a governance or design requirement for later milestones, not evidence of implementation.

| ID | Threat or misuse case | Provisional impact | Required response and safe behavior |
|---|---|---|---|
| TM-01 | A user searches or opens a document, snippet, title, status, citation, prior query, or audit event outside their authority | High—confidentiality/privacy breach and possible case or procurement harm | Deny without revealing restricted existence where policy requires; apply source restrictions to all derived forms; audit the attempt under approved privacy rules |
| TM-02 | Offline permissions or cached results remain usable after revocation, transfer, case closure, or document withdrawal | High—continued unauthorized access | Define maximum staleness and revocation transfer; fail closed beyond it; invalidate derived access and exports where feasible; preserve incident evidence |
| TM-03 | A shared or unattended workstation, stolen device, local administrator, or removable media exposes source or derived data | High—bulk disclosure and credential compromise | Agency-approved endpoint, physical, session, storage, media, and key rules; minimize local copies; incident and recovery procedure |
| TM-04 | A privileged uploader, custodian, database/NAS administrator, or service identity abuses broad access or changes status/history | High—integrity, confidentiality, and audit compromise | Separate business authority from technical administration; least privilege; dual review for defined high-impact actions; protected audit and periodic access review |
| TM-05 | An unauthorized, counterfeit, incomplete, incorrectly scanned, or wrongly classified document is admitted as authoritative | High—false evidence and downstream decision harm | Quarantine; verify custody, completeness, admitted rendition, checksum, and reviewer disposition; surface unresolved authenticity rather than infer it |
| TM-06 | Existing bytes are overwritten, version relationships are manipulated, or a superseded document is presented as current | High—citation breakage and reliance on obsolete authority | Immutable versions; new identifier/checksum for byte changes; evidence-backed status metadata; preserve history; stop claims when status is unknown or disputed |
| TM-07 | A malformed PDF, archive, image, font, macro, embedded object, oversized file, or decompression bomb exploits or exhausts the ingestion pipeline | High—code execution, service loss, or lateral movement | Treat every file as hostile; quarantine; constrain accepted formats and resource use; isolate parsing; prohibit active content; record and review failures |
| TM-08 | Text inside a document instructs the model to ignore policy, reveal secrets, alter citations, call tools, or treat the document as trusted instructions | High—prompt injection, disclosure, fabricated support, or unauthorized action | Treat document content solely as quoted evidence, never system instruction; separate instructions from content; restrict tool/action authority; require exact source verification; abstain on unresolved manipulation |
| TM-09 | An attacker plants keyword-rich, misleading, or adversarial documents/chunks to dominate retrieval or hide contrary evidence | High—retrieval poisoning and biased answers | Only index admitted versions; bind chunks to source/checksum/generation; monitor corpus changes; show provenance/context; allow reviewers to inspect competing evidence; rebuild after removal |
| TM-10 | OCR, chunking, table extraction, page mapping, or normalization changes meaning or points a citation to the wrong location | High—plausible but unsupported result | Keep transformations derived; record pipeline versions; preserve page/region mapping; compare against original; do not claim support when source resolution or context fails |
| TM-11 | A query, excerpt, PII, restricted title, or document content leaks through logs, crash files, temporary storage, screenshots, evaluation artifacts, or support bundles | High—secondary disclosure outside source controls | Minimize content; classify all derivatives; use identifiers where possible; authorize access/retention; prohibit restricted data in Git and unapproved external systems; dispose of temporary copies |
| TM-12 | The original document repository is deleted, encrypted, corrupted, or replaced with a stale copy | Critical—loss of authoritative evidence and broken citations | Stop grounded answers; preserve incident evidence; restore checksum-verified versions from a separate backup; reconcile manifests, permissions, and citations before return to service |
| TM-13 | PostgreSQL is corrupt, unavailable, rolled back, or maliciously changed | High—wrong identity, status, authorization, or audit linkage | Prevent unsafe reads/writes; restore verified state; reconcile against originals, manifests, and protected audit evidence; invalidate/rebuild affected derived data |
| TM-14 | A vector index is stale, corrupt, cross-wired between collections, or contains orphaned entries | High—wrong or unauthorized retrieval | Remove the generation from service; never use the index as an authority or sole permission check; rebuild from admitted versions and validate pointers, filters, and coverage |
| TM-15 | Source, PostgreSQL, and vector-index generations disagree after partial update or failed recovery | High—mixed-version answers and invalid citations | Use an auditable publication state; fail closed on mismatch; complete or roll back the generation; verify source checksum, metadata revision, authorization, and index identity together |
| TM-16 | A NAS outage, stale snapshot, permission drift, compromised account, or hostile network exposes or changes sources | High—bulk loss/disclosure or silent rollback | Treat NAS as a separate trust boundary; verify access and checksums; detect/reconcile snapshot rollback; use approved failover; never substitute uncontrolled local copies |
| TM-17 | Backup jobs report success but omit versions, metadata, keys, permissions, or audit evidence; restores fail when needed | Critical—irrecoverable evidence or unsafe recovery | Define backup inventory and dependencies; test restores and checksum/citation resolution; preserve failure-domain separation; do not claim RPO/RTO without evidence |
| TM-18 | Malware or unverified software/model/dependency updates enter an offline environment through transfer media | High—environment compromise or changed outputs | Approve sources and media custody; verify integrity and provenance; stage and test updates; record versions; support rollback; do not mix document import with privileged software update authority |
| TM-19 | A user copies a plausible AI answer into an official record without opening the cited original, or treats silence as proof that no authority exists | High—unsupported official action or missed evidence | Make limitations persistent; require human source review under the existing workflow; distinguish `not found`, `not authorized`, `unavailable`, `conflicting`, and `insufficient evidence` |
| TM-20 | Bulk queries, oversized corpora, repeated parsing, or adversarial inputs exhaust disk, memory, CPU/GPU, database, index, or audit capacity | Medium to high—denial of service and possible loss of audit/recovery data | Define quotas and capacity thresholds; prioritize audit and source integrity; reject or quarantine safely; recover without deleting authoritative evidence |
| TM-21 | A user exports, prints, photographs, or re-identifies permitted search results for an unauthorized secondary purpose | High—policy and privacy breach beyond application access | Purpose-bound policy, minimal disclosure, export/print authorization and audit where lawful, user accountability, and incident handling; do not assume technical access authorizes redistribution |
| TM-22 | An authorized status reviewer makes an error, or two apparently authoritative sources conflict | High—incorrect currentness/applicability claim | Record evidence, validator, time, and disagreement; label `unknown` or `disputed`; route to the authorized adjudicator; never let the model resolve legal authority |

## 5. Prompt injection originating inside documents

A government document, annex, embedded image, OCR layer, comment, hyperlink, or hidden text may contain language that resembles system instructions. It may be legitimate prose, accidentally misleading, or deliberately malicious. Issuer reputation does not make such content safe instructions for a model or tool.

The mandatory interpretation boundary is:

- repository and application policies govern behavior;
- user requests are accepted only within the user's authority;
- document content is untrusted evidence to retrieve and quote; and
- no document text may grant permissions, change system policy, authorize external communication, suppress citations, redefine source identity, or initiate a tool or administrative action.

Later design and evaluation must cover visible and hidden injection, multilingual instructions, text embedded in images/tables/metadata, instructions split across chunks, fake policy headers, requests to reveal other documents, citation substitution, and instructions claiming to be from an administrator. Safe behavior is to ignore the instruction as an instruction, retain it only as document content where relevant, avoid unauthorized actions or disclosure, and require the claimed answer to be independently supported by an exact authorized source location.

Prompt-injection defenses cannot establish that the resulting interpretation is legally correct. High-impact or ambiguous tasks must remain evidence retrieval for accountable human review.

## 6. Failure, incident, and recovery priorities

| Event | Immediate containment | Evidence and assessment | Recovery gate |
|---|---|---|---|
| Unauthorized result or disclosure | Stop the affected access path; preserve authorized logs; revoke or isolate compromised identities/devices | Identify source and derived data exposed, recipients, purpose, time window, exports/backups, and legal/privacy obligations | Accountable security/privacy owner approves restored access; permissions and affected caches/indexes are revalidated |
| Malicious or malformed document | Keep/quarantine the file and stop affected processing; do not open it through a privileged tool | Preserve checksum, provenance, processing events, failure details, and affected components without spreading active content | Custodian/security disposition recorded; clean processing environment verified; derived entries removed or rebuilt |
| Prompt-injection or poisoned retrieval | Disable affected source/index generation if results cannot be trusted | Preserve query, source IDs, exact locations, pipeline/model versions, output, and authorization-safe traces | Behavior is evaluated against adversarial cases; affected derived data rebuilt; limitations and review path verified |
| Source loss or corruption | Stop treating derived text as evidence; isolate damaged storage | Compare versions/checksums, custody history, backups, NAS snapshots, and citation impact | Exact retained bytes restored and checksum-verified; citations, permissions, database, and index reconciled |
| PostgreSQL/index corruption | Remove affected service/generation; prevent mixed or orphaned results | Identify last consistent source, metadata, authorization, pipeline, and audit state | PostgreSQL restored/reconciled; vector index rebuilt and validated; authorized owner approves return |
| Lost/stolen offline device or media | Revoke applicable identities/keys/access when possible and activate the agency incident process | Determine content, derived artifacts, export history, last sync/revocation state, and physical custody | Risk owner documents disposition; replacement environment is rebuilt from approved sources, not cloned from untrusted state |
| Backup or restore failure | Protect remaining copies; suspend unsupported recoverability claims | Determine missing versions/dependencies, failure domain, and RPO/RTO impact | Successful test restore verifies bytes, checksums, metadata, permissions, citations, audit continuity, and index rebuild |

Authoritative source preservation and prevention of further disclosure take precedence over service availability. Recovery must not reuse derived outputs whose source integrity, authorization, or generation identity is uncertain.

## 7. Audit and detection requirements

The audit scope in [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) is part of this threat model. Detection and investigation must be able to correlate document/version/checksum, actor or service identity, authorization context, ingestion and status actions, processing/index generation, source opens and exports, privileged changes, denials, backup/restores, and incident actions.

**AGENCY DECISION REQUIRED:** define which events are monitored, thresholds and capacity, review frequency, escalation routes, time synchronization in disconnected environments, privacy-preserving query handling, audit retention, protection against administrator tampering, and who may inspect audit evidence.

Absence of an audit event does not prove that access or disclosure did not occur. Screens, photographs, prints, copied text, local administrator actions, compromised components, and audit failure may be outside application visibility; these residual risks require procedural, physical, and technical controls in the approved deployment.

## 8. Validation and acceptance gates

Before a real-document pilot, accountable owners must:

1. select the actual offline/local/NAS deployment topology and data flows;
2. approve document classes, custodians, upload/admission authority, and access granularity;
3. approve confidential/PII handling, logging, retention, backup, key, and incident rules;
4. define threat likelihood and impact criteria, risk owners, treatment, and residual-risk acceptance;
5. exercise misuse cases for unauthorized access, metadata leakage, malicious/malformed files, prompt injection, poisoning, stale permissions, source loss, database/index corruption, NAS failure, and failed restore;
6. verify safe failure for `not found`, `not authorized`, `unavailable`, `unknown status`, `conflicting evidence`, and `insufficient evidence`;
7. demonstrate exact source/version/location resolution after rebuild and recovery; and
8. confirm that users and approvers understand that Kendra output is evidence assistance, not an official decision.

Until these gates are evidenced, control effectiveness is **not established** and deployment risk remains unaccepted.
