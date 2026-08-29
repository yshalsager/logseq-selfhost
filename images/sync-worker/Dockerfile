# syntax=docker/dockerfile:1.25@sha256:0adf442eae370b6087e08edc7c50b552d80ddf261576f4ebd6421006b2461f12
FROM debian:trixie-slim@sha256:020c0d20b9880058cbe785a9db107156c3c75c2ac944a6aa7ab59f2add76a7bd AS build
ARG LOGSEQ_REF=master
ARG MISE_VERSION=v2026.8.14

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/root/.local/bin:$PATH
ENV MISE_YES=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    xz-utils \
  && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://mise.run | MISE_VERSION="${MISE_VERSION}" sh

WORKDIR /tooling
COPY mise.toml /tooling/mise.toml
RUN --mount=type=cache,target=/root/.npm \
    mise trust /tooling/mise.toml \
  && mise install \
  && mkdir -p /tmp/wrangler \
  && cp -a "$(mise where wrangler)/." /tmp/wrangler/

WORKDIR /src
RUN git init . \
  && git remote add origin https://github.com/logseq/logseq.git \
  && git fetch --depth 1 origin "${LOGSEQ_REF}" \
  && git checkout --detach FETCH_HEAD

COPY mise.toml /src/mise.toml
RUN mise trust /src/mise.toml

WORKDIR /src/deps/db-sync
RUN mise exec -- corepack enable
RUN --mount=type=cache,target=/root/.local/share/pnpm/store mise exec -- pnpm install --frozen-lockfile --ignore-workspace
RUN --mount=type=cache,target=/root/.m2/repository mise exec -- pnpm run release
RUN mise exec -- pnpm run build:api-docs
COPY images/sync-worker/wrangler.selfhost.toml /src/deps/db-sync/worker/wrangler.selfhost.toml
RUN cd worker \
  && mise exec -- wrangler deploy --dry-run \
    --config wrangler.selfhost.toml \
    --outdir /tmp/sync-worker

FROM node:24-bookworm-slim@sha256:3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03

LABEL org.opencontainers.image.description="Self-hosted Logseq Sync Worker image (semantic REST and MCP APIs)"

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/worker /data/home /data/wrangler \
  && mkdir -p /app/worker/.wrangler/tmp /app/worker/node_modules/.mf \
  && chown -R node:node /app /data

WORKDIR /app/worker

COPY --chown=node:node --from=build /tmp/sync-worker/entry.js /app/worker/sync-worker.mjs
COPY --chown=node:node --from=build /src/deps/db-sync/worker/migrations /app/worker/migrations
COPY --from=build /tmp/wrangler /opt/wrangler
COPY --chown=node:node images/sync-worker/wrangler.selfhost.toml /app/worker/wrangler.selfhost.toml
COPY --chmod=755 --chown=node:node images/sync-worker/scripts/start.sh /usr/local/bin/start-sync-worker.sh

ENV HOME=/data/home
ENV PATH=/opt/wrangler/bin:$PATH
ENV CLOUDFLARE_INCLUDE_PROCESS_ENV=true
ENV WRANGLER_LOG=info
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

USER node:node
EXPOSE 8787

CMD ["/usr/local/bin/start-sync-worker.sh"]
