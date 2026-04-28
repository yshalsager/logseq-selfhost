# syntax=docker/dockerfile:1.23@sha256:2780b5c3bab67f1f76c781860de469442999ed1a0d7992a5efdf2cffc0e3d769
FROM debian:trixie-slim@sha256:cedb1ef40439206b673ee8b33a46a03a0c9fa90bf3732f54704f99cb061d2c5a AS build
ARG LOGSEQ_REF=master
ARG MISE_VERSION=v2026.4.18

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

WORKDIR /src/deps/publish
RUN mise exec -- corepack enable
RUN --mount=type=cache,target=/root/.local/share/pnpm/store mise exec -- pnpm install --frozen-lockfile
RUN mkdir -p /tmp/publish-runtime-node-modules \
  && cp -a "$(readlink -f node_modules/mldoc)" /tmp/publish-runtime-node-modules/mldoc
RUN --mount=type=cache,target=/root/.m2/repository mise exec -- pnpm run release

FROM node:24-bookworm-slim@sha256:03eae3ef7e88a9de535496fb488d67e02b9d96a063a8967bae657744ecd513f2
ARG WRANGLER_VERSION=latest

LABEL org.opencontainers.image.description="Self-hosted Logseq Publish image (Wrangler local runtime)"

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g "wrangler@${WRANGLER_VERSION}" \
  && mkdir -p /app/worker /data/home /data/wrangler \
  && mkdir -p /app/worker/.wrangler/tmp /app/worker/node_modules/.mf \
  && chown -R node:node /app /data

WORKDIR /app/worker

COPY --chown=node:node --from=build /tmp/publish-runtime-node-modules /app/worker/node_modules
COPY --chown=node:node --from=build /src/deps/publish/worker /app/worker
COPY --chown=node:node images/publish/wrangler.selfhost.toml /app/worker/wrangler.selfhost.toml

ENV HOME=/data/home
ENV CLOUDFLARE_INCLUDE_PROCESS_ENV=true
ENV PUBLISH_PORT=8787
ENV WRANGLER_LOG=info
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

USER node:node
EXPOSE 8787

CMD ["wrangler", "dev", "--config", "wrangler.selfhost.toml", "--ip", "0.0.0.0", "--port", "8787", "--persist-to", "/data/wrangler"]
