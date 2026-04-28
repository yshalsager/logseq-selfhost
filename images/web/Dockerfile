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
    rsync \
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
RUN mise exec -- corepack enable

RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    --mount=type=cache,target=/root/.m2/repository \
    export ENABLE_FILE_SYNC_PRODUCTION=true ENABLE_RTC_SYNC_PRODUCTION=true; \
    mise exec -- pnpm install --frozen-lockfile && \
    mise exec -- pnpm run gulp:build && \
    mise exec -- clojure -M:cljs release app db-worker && \
    mise exec -- pnpm run webpack-app-build

RUN mkdir -p /tmp/web && rsync -a --delete /src/static/ /tmp/web/

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:35a4455cd4153d7cd0ae1fcfa42451884ef19848202606f144d9a089376c7e6c
LABEL org.opencontainers.image.description="Self-hosted Logseq DB web app static image"
COPY images/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=101:101 --from=build /tmp/web/ /usr/share/nginx/html/

EXPOSE 8080
