# Logseq DB Web (Self-hosted)

[![Build Image](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-web-image.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-web-image.yml)
[![Bump Upstream Ref](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-web-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-web-ref.yml)
[![ghcr.io tag](https://ghcr-badge.egpl.dev/yshalsager/logseq-selfhost-web/latest_tag?ignore=latest,buildcache*,sha256*&trim=major&label=GitHub%20Registry&color=steelblue)](https://github.com/yshalsager/logseq-selfhost/pkgs/container/logseq-selfhost-web)
[![ghcr.io size](https://ghcr-badge.egpl.dev/yshalsager/logseq-selfhost-web/size?tag=latest&label=Image%20size&color=steelblue)](https://github.com/yshalsager/logseq-selfhost/pkgs/container/logseq-selfhost-web)
[![License](https://img.shields.io/github/license/yshalsager/logseq-selfhost.svg)](https://github.com/yshalsager/logseq-selfhost/blob/master/LICENSE)

This image builds and serves the Logseq DB web app (PWA) from upstream `logseq/logseq`.

## Upstream URLs

- [Logseq repository](https://github.com/logseq/logseq)
- [Logseq DB overview](https://github.com/logseq/docs/blob/master/db-version.md)
- [DB web test site](https://test.logseq.com/)
- [Docker web app guide](https://github.com/logseq/logseq/blob/master/docs/docker-web-app-guide.md)

## Configure

From repository root:

```bash
cp images/web/.env.example images/web/.env
```

Edit `images/web/.env` values:

- `GHCR_OWNER`
- `IMAGE_TAG`
- `WEB_PORT`

## Build and publish (GitHub Actions)

Workflow: `.github/workflows/build-selfhost-web-image.yml`

Triggers:

- `workflow_dispatch` with optional `logseq_ref`, `image_tag`
- Weekly fallback: Saturday 04:00 UTC
- Push to `master` affecting image build inputs (`Dockerfile`, `nginx.conf`, pinned upstream ref, or shared `mise.toml`)

Pinned upstream ref file: `images/web/UPSTREAM_LOGSEQ_DB_REF`

Published tags:

- `ghcr.io/<GHCR_OWNER>/logseq-selfhost-web:<tag>`
- `ghcr.io/<GHCR_OWNER>/logseq-selfhost-web:latest` (default branch builds)

## Deploy

From repository root:

```bash
docker compose -f images/web/docker-compose.yml pull
docker compose -f images/web/docker-compose.yml up -d
```

## Smoke test

From repository root:

```bash
IMAGE=ghcr.io/<GHCR_OWNER>/logseq-selfhost-web:<tag> ./images/web/scripts/smoke-test.sh
```

Default checks:

- `/` returns `200`
- body looks like HTML

## Browser requirements

- Chromium-based browser is recommended (File System Access API)
- Use HTTPS when exposed remotely

## Auto-track upstream

Workflow: `.github/workflows/bump-selfhost-web-ref.yml`

- Weekly Saturday 03:00 UTC
- Tracks latest commit at `logseq/logseq` branch `test/db`
- Updates `images/web/UPSTREAM_LOGSEQ_DB_REF` and opens PR
