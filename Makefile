.PHONY: build

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
