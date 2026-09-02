FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        poppler-utils \
        fonts-dejavu-core \
        tesseract-ocr \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade "pip==26.2.1"

# Docling's local layout models need PyTorch. Use the official CPU wheel index so
# the local ingestion image does not acquire unused CUDA runtime packages.
RUN python -m pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch>=2.2.2,<3" "torchvision>=0,<1"

COPY pyproject.toml ./
COPY src ./src

FROM base AS test

RUN python -m pip install --no-cache-dir ".[test]"

COPY tests ./tests

CMD ["python", "-m", "pytest", "-q"]

FROM base AS runtime

# Baked at build time so a plain `docker compose up` (no export, no rebuild) still
# reports a real revision, not "unknown" -- see docker-compose.yml's `api` build.args.
# Empty by default: a build that doesn't pass one bakes an empty string, which
# resolve_source_revision() treats as not-set and falls through to its next source
# (git in the container, then "unknown") -- never a fabricated commit id. An
# operator-supplied runtime env var (`docker run -e` / `docker compose run -e`, or a
# local compose override) still takes precedence over this baked default, same as
# any other Dockerfile ENV.
ARG KENDRA_SOURCE_REVISION=""
ENV KENDRA_SOURCE_REVISION=${KENDRA_SOURCE_REVISION}

# Same baking pattern as KENDRA_SOURCE_REVISION above, for the release tag
# (e.g. "demo-dost-v1"). Empty by default -- a build taken before tagging (or
# any non-release build) simply has no tag to report; main.py reads this via
# a plain os.environ.get with an empty-string default, never fabricating one.
ARG KENDRA_RELEASE_TAG=""
ENV KENDRA_RELEASE_TAG=${KENDRA_RELEASE_TAG}

RUN python -m pip install --no-cache-dir . \
    && groupadd --system kendra \
    && useradd --system --gid kendra --home-dir /nonexistent --shell /usr/sbin/nologin kendra

USER kendra

EXPOSE 8000

CMD ["python", "-m", "kendra_api.run"]
