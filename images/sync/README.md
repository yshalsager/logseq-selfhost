# Logseq Sync Server (Node Adapter)

[![Build Image](https://github.com/yshalsager/logseq-sync-server/actions/workflows/build-sync-image.yml/badge.svg)](https://github.com/yshalsager/logseq-sync-server/actions/workflows/build-sync-image.yml)
[![Bump Upstream Ref](https://github.com/yshalsager/logseq-sync-server/actions/workflows/bump-db-sync-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-sync-server/actions/workflows/bump-db-sync-ref.yml)
[![ghcr.io tag](https://ghcr-badge.egpl.dev/yshalsager/logseq-sync-server/latest_tag?trim=major&label=GitHub%20Registry&color=steelblue)](https://github.com/yshalsager/logseq-sync-server/pkgs/container/logseq-sync-server)
[![ghcr.io size](https://ghcr-badge.egpl.dev/yshalsager/logseq-sync-server/size?tag=latest&label=Image%20size&color=steelblue)](https://github.com/yshalsager/logseq-sync-server/pkgs/container/logseq-sync-server)
[![License](https://img.shields.io/github/license/yshalsager/logseq-sync-server.svg)](https://github.com/yshalsager/logseq-sync-server/blob/master/LICENSE)

This image packages Logseq `deps/db-sync` node adapter for self-hosting.

## Upstream URLs

- [Logseq repository](https://github.com/logseq/logseq)
- `deps/db-sync` [README.md](https://github.com/logseq/logseq/blob/master/deps/db-sync/README.md)
- Custom Sync Server URL PR: [logseq/logseq#12459](https://github.com/logseq/logseq/pull/12459)

## Configure

From repository root:

```bash
cp images/sync/.env.example images/sync/.env
```

Edit `images/sync/.env` values:

- `GHCR_OWNER`
- `IMAGE_TAG`
- `SYNC_PORT`
- `DB_SYNC_BASE_URL`
- `DB_SYNC_DATA_DIR`
- `COGNITO_*`

## Build and publish (GitHub Actions)

Workflow: `.github/workflows/build-sync-image.yml`

Triggers:

- `workflow_dispatch` with optional `logseq_ref`, `image_tag`
- Weekly fallback: Saturday 04:00 UTC
- Push to `master` affecting sync files/workflow

Pinned upstream ref file: `images/sync/UPSTREAM_DB_SYNC_REF`

Published tags:

- `ghcr.io/<GHCR_OWNER>/logseq-sync-server:<tag>`
- `ghcr.io/<GHCR_OWNER>/logseq-sync-server:latest` (default branch builds)

## Deploy

From repository root:

```bash
docker compose -f images/sync/docker-compose.yml pull
docker compose -f images/sync/docker-compose.yml up -d
```

## Smoke test

From repository root:

```bash
IMAGE=ghcr.io/<GHCR_OWNER>/logseq-sync-server:<tag> ./images/sync/scripts/smoke-test.sh
```

Default checks:

- `/health` returns `200` with `{"ok":true}`
- `/graphs` returns `401` without auth
- `/sync/<graph-id>/pull?since=0` returns `401` without auth

## Auto-track upstream

Workflow: `.github/workflows/bump-db-sync-ref.yml`

- Weekly Saturday 03:00 UTC
- Tracks latest commit in `logseq/logseq` touching `deps/db-sync`
- Updates `images/sync/UPSTREAM_DB_SYNC_REF` and opens PR
