# syntax=docker/dockerfile:1.24@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89
FROM debian:trixie-slim@sha256:b6e2a152f22a40ff69d92cb397223c906017e1391a73c952b588e51af8883bf8 AS build
ARG LOGSEQ_REF=master
ARG MISE_VERSION=v2026.5.15

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

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:acc3239879a65d9e3d250b21847ec3f34f33367017394d22830242af15cf1cb0
LABEL org.opencontainers.image.description="Self-hosted Logseq DB web app static image"
COPY images/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=101:101 --from=build /tmp/web/ /usr/share/nginx/html/

EXPOSE 8080
