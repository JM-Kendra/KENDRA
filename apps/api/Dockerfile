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

# `git` is needed by tests/test_evaluation_lock.py and
# tests/test_evaluation_source_revision_preflight.py, which exercise the real
# evaluation runner's git-based preflight against a throwaway repository built
# fresh in `tmp_path` (tests/conftest.py's `repo_root` fixture) rather than
# resolving an on-disk `.git` checkout from wherever this test file happens to
# live -- the latter only ever worked when pytest ran against a live checkout,
# never inside this isolated build.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir ".[test]"

COPY tests ./tests

# The lock tests' throwaway repo also needs the real gold-dataset validator
# and dataset file that kendra_api.evaluation.dataset loads dynamically by
# path at `<repo_root>/scripts/validate_gold_cases.py` -- neither lives under
# this image's own build context (./apps/api). Pulled in from a second, named
# build context (see README.md/CLAUDE.md's build command: `--build-context
# fixtures=.` from the repository root) rather than widening this image's
# build context to the whole repository just for two files.
COPY --from=fixtures scripts/validate_gold_cases.py ./tests/fixtures/gold_dataset/scripts/validate_gold_cases.py
COPY --from=fixtures evaluation/gold_cases.json ./tests/fixtures/gold_dataset/evaluation/gold_cases.json

CMD ["python", "-m", "pytest", "-q"]

FROM test AS eval-runner

# The gold-evaluation runner (kendra_api.evaluation.run) must resolve
# `git rev-parse HEAD` inside a container that bind-mounts the repository --
# which Git refuses by default ("detected dubious ownership") when the
# mount's owning uid differs from the container's. Baked here rather than
# passed per-invocation (GIT_CONFIG_* env vars, or `git config --global` at
# runtime) so a plain container run never needs the retry Milestone 13's
# first release round hit. `*` is safe specifically because this image's only
# use is mounting one operator-chosen repo checkout for evaluation -- it is
# not a general-purpose Git tool image. `git` itself is already installed in
# the `test` stage this extends.
RUN git config --system --add safe.directory '*'

ENTRYPOINT ["python", "-m", "kendra_api.evaluation.run"]

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
