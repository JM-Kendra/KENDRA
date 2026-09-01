.PHONY: build

# Rebuilds api/web with KENDRA_SOURCE_REVISION baked into the image (Dockerfile's
# `runtime` stage ARG->ENV; see docker-compose.yml's `api` build.args), so a plain
# `docker compose up` afterward reports the real revision without a manual export.
# Run this instead of a bare `docker compose build api web` on a normal rebuild.
build:
	KENDRA_SOURCE_REVISION=$$(git rev-parse HEAD) docker compose build api web
