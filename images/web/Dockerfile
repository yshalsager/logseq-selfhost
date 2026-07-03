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

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:fd3314e343bad2de4e1127ef58be122abbfa7e09572fa46ae62fcddb6b3f21c5
LABEL org.opencontainers.image.description="Self-hosted Logseq DB web app static image"
COPY images/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=101:101 --from=build /tmp/web/ /usr/share/nginx/html/

EXPOSE 8080
