# Tests

Application tests live with their service boundaries in `apps/api/tests/` and `apps/web/src/**/*.test.ts`. Cross-application acceptance definitions and non-sensitive synthetic fixtures may be added here in later milestones.

Milestone 9 ingestion tests generate digital and scanned PDFs only in pytest temporary directories. Generated PDFs, OCR output, and extracted text remain untracked. Question-answering tests are intentionally not part of this milestone.

Test output, caches, generated reports, and copied government documents do not belong in Git. The exact containerized commands are in the root `README.md`.
