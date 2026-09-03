.PHONY: build test test-full verify-chain check-template drill-env answering-on answering-off tag-evidence

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
	check 'KENDRA_SOURCE_REVISION:' \
		'ingest service still passes KENDRA_SOURCE_REVISION through (pipeline_revision provenance)'; \
	exit $$status

# Confirms a drill's own .env (in the current directory, not .env.example)
# actually carries the three drill-specific overrides documented in
# docs/DOST_DEMO.md Sec 10 step 0 -- KENDRA_API_PORT=8001/KENDRA_WEB_PORT=3001
# (so the drill's api/web don't collide with the still-running main dev
# stack's 8000/3000 defaults) and a KENDRA_POSTGRES_PASSWORD that has
# actually been changed from .env.example's own placeholder value (never the
# operator's real password). Checks the VALUE against the required override,
# not just that the key is present -- a presence-only check passes against
# an unmodified copy of .env.example, since it already sets
# KENDRA_API_PORT=8000/KENDRA_WEB_PORT=3000/KENDRA_POSTGRES_PASSWORD=<placeholder>,
# which is exactly the collision round 5's drill hit. Run from inside the
# scratch clone.
# Toggles KENDRA_ANSWERING_ENABLED in .env for the compose project rooted at
# the current directory (the main stack by default; pass
# COMPOSE_PROJECT=<name> to target a non-default project, e.g. a drill's own
# scratch clone under docs/DOST_DEMO.md Section 10 -- `make answering-on
# COMPOSE_PROJECT=kendra-recovery-drill`), recreates api, and waits for
# health's own `status: ready` (same idiom as Section 10 step 6/7) rather
# than a fixed sleep. A bare `sed -i 's/^KEY=.*/KEY=val/' .env` is a silent
# no-op when the key is missing from .env -- that gap is exactly what stalled
# round 1 of demo-dost-v1.3 hardening -- so this replaces the line if
# present and appends it if absent. Prints answering_enabled from health and
# exits non-zero if it doesn't match.
define set-answering
if grep -qE '^KENDRA_ANSWERING_ENABLED=' .env; then \
	sed -i "s/^KENDRA_ANSWERING_ENABLED=.*/KENDRA_ANSWERING_ENABLED=$(1)/" .env; \
else \
	echo "KENDRA_ANSWERING_ENABLED=$(1)" >> .env; \
fi; \
proj_flag=""; \
if [ -n "$(COMPOSE_PROJECT)" ]; then proj_flag="-p $(COMPOSE_PROJECT)"; fi; \
docker compose $$proj_flag up -d --force-recreate api; \
host=$$(grep -E '^KENDRA_API_BIND_HOST=' .env | tail -1 | cut -d= -f2-); host=$${host:-127.0.0.1}; \
port=$$(grep -E '^KENDRA_API_PORT=' .env | tail -1 | cut -d= -f2-); port=$${port:-8000}; \
timeout 60 bash -c "until curl -sf http://$$host:$$port/api/v1/health | grep -Eq '\"status\":[[:space:]]*\"ready\"'; do sleep 2; done"; \
actual=$$(curl -s http://$$host:$$port/api/v1/health | python3 -c "import json,sys; print(str(json.load(sys.stdin)['answering_enabled']).lower())"); \
echo "answering_enabled: $$actual"; \
if [ "$$actual" != "$(1)" ]; then echo "FAIL: expected $(1), got $$actual"; exit 1; fi
endef

answering-on:
	@$(call set-answering,true)

answering-off:
	@$(call set-answering,false)

# Mechanical ADR-014 one-commit check: candidate (HEAD), drill's
# report.json source_revision, drill's pipeline_revision.txt (Section 10
# step 8a), and release's report.json source_revision must all be the same
# commit -- EQUAL is the precondition for creating a release tag; see
# scripts/tag_evidence.sh and docs/DOST_DEMO.md Section 10's "Tag step".
# Usage: make tag-evidence TAG=<name> DRILL=<run-dir> RELEASE=<run-dir>
tag-evidence:
	@scripts/tag_evidence.sh "$(TAG)" "$(DRILL)" "$(RELEASE)"

drill-env:
	@if [ ! -f .env ]; then echo "FAIL no .env in $$(pwd)"; exit 1; fi; \
	echo "--- .env differences from .env.example ---"; \
	diff .env.example .env || true; \
	echo "--- required drill-specific overrides ---"; \
	status=0; \
	template_password=$$(grep -E '^KENDRA_POSTGRES_PASSWORD=' .env.example | cut -d= -f2-); \
	if grep -qE '^KENDRA_API_PORT=8001$$' .env; then \
		echo "OK   KENDRA_API_PORT=8001"; \
	else \
		echo "FAIL KENDRA_API_PORT is not overridden to 8001"; \
		status=1; \
	fi; \
	if grep -qE '^KENDRA_WEB_PORT=3001$$' .env; then \
		echo "OK   KENDRA_WEB_PORT=3001"; \
	else \
		echo "FAIL KENDRA_WEB_PORT is not overridden to 3001"; \
		status=1; \
	fi; \
	env_password=$$(grep -E '^KENDRA_POSTGRES_PASSWORD=' .env | cut -d= -f2-); \
	if [ -n "$$env_password" ] && [ "$$env_password" != "$$template_password" ]; then \
		echo "OK   KENDRA_POSTGRES_PASSWORD changed from the .env.example placeholder"; \
	else \
		echo "FAIL KENDRA_POSTGRES_PASSWORD is still the .env.example placeholder (or unset)"; \
		status=1; \
	fi; \
	exit $$status
