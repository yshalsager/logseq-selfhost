# syntax=docker/dockerfile:1.7
FROM debian:trixie-slim AS build
ARG LOGSEQ_REF=master
ARG MISE_VERSION=v2026.4.11

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
RUN --mount=type=cache,target=/root/.cache/yarn mise exec -- yarn install --frozen-lockfile
RUN --mount=type=cache,target=/root/.m2/repository mise exec -- npm run build:node-adapter
RUN mise exec -- npm prune --omit=dev
RUN mkdir -p /tmp/runtime-data

FROM gcr.io/distroless/nodejs24-debian12:nonroot
WORKDIR /app

COPY --chown=nonroot:nonroot --from=build /src/deps/db-sync/package.json /app/package.json
COPY --chown=nonroot:nonroot --from=build /src/deps/db-sync/yarn.lock /app/yarn.lock
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
