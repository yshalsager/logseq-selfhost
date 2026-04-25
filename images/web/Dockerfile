# syntax=docker/dockerfile:1.23@sha256:2780b5c3bab67f1f76c781860de469442999ed1a0d7992a5efdf2cffc0e3d769
FROM debian:trixie-slim@sha256:4ffb3a1511099754cddc70eb1b12e50ffdb67619aa0ab6c13fcd800a78ef7c7a AS build
ARG LOGSEQ_REF=test/db
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

RUN --mount=type=cache,target=/root/.cache/yarn \
    --mount=type=cache,target=/root/.m2/repository \
    export ENABLE_FILE_SYNC_PRODUCTION=true ENABLE_RTC_SYNC_PRODUCTION=true; \
    mise exec -- yarn install --frozen-lockfile && \
    mise exec -- yarn gulp:build && \
    mise exec -- clojure -M:cljs release app db-worker && \
    mise exec -- yarn webpack-app-build

RUN mkdir -p /tmp/web && rsync -a --delete /src/static/ /tmp/web/

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:7377697a821c131a924a7105fafbe7414db4e9fcc77a6f08f776f33f141ec3f8
LABEL org.opencontainers.image.description="Self-hosted Logseq DB web app static image"
COPY images/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=101:101 --from=build /tmp/web/ /usr/share/nginx/html/

EXPOSE 8080
