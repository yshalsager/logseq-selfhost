# syntax=docker/dockerfile:1.25@sha256:0adf442eae370b6087e08edc7c50b552d80ddf261576f4ebd6421006b2461f12
FROM debian:trixie-slim@sha256:28de0877c2189802884ccd20f15ee41c203573bd87bb6b883f5f46362d24c5c2 AS build
ARG LOGSEQ_REF=master
ARG MISE_VERSION=v2026.6.14

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
RUN mise trust /tooling/mise.toml && mise install

WORKDIR /src
RUN git init . \
  && git remote add origin https://github.com/logseq/logseq.git \
  && git fetch --depth 1 origin "${LOGSEQ_REF}" \
  && git checkout --detach FETCH_HEAD

COPY mise.toml /src/mise.toml
RUN mise trust /src/mise.toml

WORKDIR /src/deps/db-sync
RUN mise exec -- corepack enable

# --ignore-workspace: /src has an ancestor pnpm-workspace.yaml (with
# shamefully-hoist=true, set for the main logseq app's shadow-cljs builds)
# that pnpm picks up even though deps/db-sync isn't a declared workspace
# member. Without this flag, deps/db-sync's dependencies get hoisted and
# symlinked into /src/node_modules/.pnpm instead of a local store, so
# copying only deps/db-sync/node_modules below (as this Dockerfile
# previously did) ships dangling symlinks -- see "Cannot find module 'ws'"
# crash loop. --ignore-workspace forces a fully self-contained install
# scoped to deps/db-sync.
RUN --mount=type=cache,target=/root/.local/share/pnpm/store mise exec -- pnpm install --frozen-lockfile --ignore-workspace
RUN --mount=type=cache,target=/root/.m2/repository mise exec -- pnpm run build:node-adapter
RUN CI=true mise exec -- pnpm prune --prod --ignore-workspace
RUN mkdir -p /tmp/runtime-data

FROM gcr.io/distroless/nodejs24-debian12:nonroot@sha256:14d42e2511532589a7c7e01a753667a74fcc96266e137e8125006b87b0c32d0a
WORKDIR /app
LABEL org.opencontainers.image.description="Self-hosted Logseq Sync Server image (db-sync node adapter)"

COPY --chown=nonroot:nonroot --from=build /src/deps/db-sync/package.json /app/package.json
COPY --chown=nonroot:nonroot --from=build /src/deps/db-sync/pnpm-lock.yaml /app/pnpm-lock.yaml
COPY --chown=nonroot:nonroot --from=build /src/deps/db-sync/node_modules /app/node_modules
COPY --chown=nonroot:nonroot --from=build /src/deps/db-sync/worker /app/worker
COPY --chown=nonroot:nonroot --from=build /tmp/runtime-data /app/data

ENV DB_SYNC_PORT=8787
ENV DB_SYNC_DATA_DIR=/app/data
ENV DB_SYNC_STORAGE_DRIVER=sqlite
ENV DB_SYNC_ASSETS_DRIVER=filesystem
ENV DB_SYNC_LOG_LEVEL=info

USER nonroot:nonroot
EXPOSE 8787

CMD ["worker/dist/node-adapter.js"]
