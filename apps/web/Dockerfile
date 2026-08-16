FROM node:24-bookworm-slim AS dependencies

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS source

COPY . .

FROM source AS test

RUN npm run typecheck && npm test

FROM source AS build

ARG NEXT_PUBLIC_KENDRA_API_BASE_URL=http://127.0.0.1:8000
ENV NEXT_PUBLIC_KENDRA_API_BASE_URL=${NEXT_PUBLIC_KENDRA_API_BASE_URL}

RUN npm run build

FROM node:24-bookworm-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

WORKDIR /app

RUN groupadd --system kendra \
    && useradd --system --gid kendra --home-dir /nonexistent --shell /usr/sbin/nologin kendra

COPY --from=build --chown=kendra:kendra /app/.next/standalone ./
COPY --from=build --chown=kendra:kendra /app/.next/static ./.next/static

USER kendra

EXPOSE 3000

CMD ["node", "server.js"]
