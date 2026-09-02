.PHONY: build test test-full verify-chain check-template

# Rebuilds api/web with KENDRA_SOURCE_REVISION (both images) and, once the
# current commit is tagged, KENDRA_RELEASE_TAG (api) / NEXT_PUBLIC_KENDRA_GIT_COMMIT
# (web) baked in (Dockerfile ARG->ENV; see docker-compose.yml's build.args), so a
# plain `docker compose up` afterward reports them without a manual export.
# `git describe` fails harmlessly (empty tag) on an untagged commit.
# Run this instead of a bare `docker compose build api web` on a normal rebuild.
build:
	KENDRA_SOURCE_REVISION=$$(git rev-parse HEAD) \
	KENDRA_RELEASE_TAG=$$(git describe --tags --exact-match HEAD 2>/dev/null || true) \
	NEXT_PUBLIC_KENDRA_GIT_COMMIT=$$(git rev-parse HEAD) \
	docker compose build api web

# The containerized subset: no live services, no git-dependent tests beyond
# what a throwaway tmp_path repo can satisfy (tests/conftest.py's `repo_root`
# fixture). `--build-context fixtures=.` pulls scripts/validate_gold_cases.py
# and evaluation/gold_cases.json from the repo root into the image for that
# fixture -- see CLAUDE.md's "fixtures build context" note. Run from the repo
# root. Expect 120 passed, 2 skipped, 43 deselected.
test:
	docker build --target test --build-context fixtures=. -t kendra-api-test ./apps/api
	docker run --rm kendra-api-test

# The complete backend suite, including the 21 tests that only run against a
# real, on-disk git checkout (tests/test_evaluation_runner.py,
# tests/test_source_revision.py -- see v14.md/v15.md Task 0b) -- bind-mounts
# this checkout itself rather than a throwaway repo. Expect 141 passed, 43
# deselected, 0 skipped.
test-full:
	docker build --target eval-runner --build-context fixtures=. -t kendra-api-eval-runner ./apps/api
	docker run --rm --entrypoint python -v "$$(pwd)":/repo -w /repo/apps/api kendra-api-eval-runner -m pytest -q

# Verifies the question_audit hash chain against the LIVE main dev stack.
# `docker compose exec api python scripts/verify_audit_chain.py` (as CLAUDE.md
# used to document) does not work: the api runtime image never COPYs
# scripts/ in, and the container's read_only rootfs blocks `docker cp` as a
# workaround. `docker compose run` instead reuses the api service's own
# image, network, and environment (including .env, loaded by compose
# automatically -- no credentials hard-coded here) while bind-mounting
# scripts/ read-only and overriding the entrypoint; --no-deps skips starting
# postgres/qdrant/ollama, which are already running on the main stack.
verify-chain:
	docker compose run --rm --no-deps --entrypoint python -v "$$(pwd)/scripts:/scripts:ro" api /scripts/verify_audit_chain.py

# Renders docker-compose.yml against .env.example (what a fresh clone actually
# gets, not this workstation's own long-lived .env) and pins the four values a
# fresh from-scratch drill has twice failed on so far. Checks the VALUE, not
# just presence -- round 4's failure was a wrong value present
# (KENDRA_EXTRACTION_COMPLETENESS_POLICY resolved to the pre-ADR-007 default),
# which a presence-only grep would have passed. Meant to run before every
# future drill so a stale template never again costs ~17 minutes of model
# staging before the failure surfaces at ingestion.
check-template:
	@rendered="$$(docker compose --env-file .env.example --profile ingestion config)"; \
	status=0; \
	check() { \
		if echo "$$rendered" | grep -qE "$$1"; then \
			echo "OK   $$2"; \
		else \
			echo "FAIL $$2"; \
			status=1; \
		fi; \
	}; \
	check 'KENDRA_EXTRACTION_COMPLETENESS_POLICY: native-primary-detection-v1' \
		'KENDRA_EXTRACTION_COMPLETENESS_POLICY = native-primary-detection-v1 (ADR-007)'; \
	check 'KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT: "?0\.90"?' \
		'KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT = 0.90'; \
	check 'KENDRA_ANSWER_MODEL: qwen2\.5:7b-instruct' \
		'KENDRA_ANSWER_MODEL = qwen2.5:7b-instruct'; \
	check 'KENDRA_EMBEDDING_MODEL: bge-m3' \
		'KENDRA_EMBEDDING_MODEL = bge-m3'; \
	exit $$status
