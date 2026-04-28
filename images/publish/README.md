# Logseq Publish Server (Wrangler Local Runtime)

[![Build Image](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-publish-image.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-publish-image.yml)
[![Bump Upstream Ref](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-publish-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-publish-ref.yml)
[![ghcr.io tag](https://ghcr-badge.egpl.dev/yshalsager/logseq-selfhost-publish/latest_tag?ignore=latest,buildcache*,sha256*&trim=major&label=GitHub%20Registry&color=steelblue)](https://github.com/yshalsager/logseq-selfhost/pkgs/container/logseq-selfhost-publish)
[![ghcr.io size](https://ghcr-badge.egpl.dev/yshalsager/logseq-selfhost-publish/size?tag=latest&label=Image%20size&color=steelblue)](https://github.com/yshalsager/logseq-selfhost/pkgs/container/logseq-selfhost-publish)
[![License](https://img.shields.io/github/license/yshalsager/logseq-selfhost.svg)](https://github.com/yshalsager/logseq-selfhost/blob/master/LICENSE)

This image packages Logseq `deps/publish` and runs it with Wrangler's local Workers runtime for VPS self-hosting.

## What This Image Provides

- Logseq publish worker bundle from upstream `deps/publish`
- Local Durable Object persistence under `/data/wrangler`
- Local R2 emulation under the same persisted Wrangler state
- Public publish pages and assets served through the worker
- JWT validation against the regular Logseq Cognito issuer

## Known Gaps

- This is not a native Node adapter. It runs the Cloudflare Worker through Wrangler/Miniflare.
- Run a single container replica. Local Durable Object and R2 state are container-volume state, not shared cluster storage.
- The `/pages/:graph/:page/transit` API still returns a Cloudflare-style presigned R2 URL. Public rendered pages and assets do not depend on that route, but API consumers that fetch raw transit blobs from this route need a native adapter patch.
- Authentication still depends on Logseq Cognito tokens. Fully independent auth requires client and worker changes.

## Upstream URLs

- [Logseq repository](https://github.com/logseq/logseq)
- `deps/publish` [README.md](https://github.com/logseq/logseq/blob/master/deps/publish/README.md)

## Configure

From repository root:

```bash
cp images/publish/.env.example images/publish/.env
```

Edit `images/publish/.env` values:

- `GHCR_OWNER`
- `IMAGE_TAG`
- `PUBLISH_PORT`
- `COGNITO_*`

The `R2_*` values are local placeholders for the current worker's raw transit presign route. Keep them local unless you patch the worker to use a real external S3-compatible store.

## Build and Publish (GitHub Actions)

Workflow: `.github/workflows/build-selfhost-publish-image.yml`

Triggers:

- `workflow_dispatch` with optional `logseq_ref`, `image_tag`
- Weekly fallback: Saturday 04:00 UTC
- Push to `master` affecting image build inputs (`Dockerfile`, Wrangler config, pinned upstream ref, or shared `mise.toml`)

Pinned upstream ref file: `images/publish/UPSTREAM_PUBLISH_REF`

Published tags:

- `ghcr.io/<GHCR_OWNER>/logseq-selfhost-publish:<tag>`
- `ghcr.io/<GHCR_OWNER>/logseq-selfhost-publish:latest` (default branch builds)

## Deploy

From repository root:

```bash
docker compose -f images/publish/docker-compose.yml pull
docker compose -f images/publish/docker-compose.yml up -d
```

Put your reverse proxy in front of the mapped port, for example:

```text
https://publish.example.com -> http://127.0.0.1:8788
```

Then set Logseq's publish endpoint to:

```text
Settings -> Advanced -> Publish server URL -> https://publish.example.com
```

## Smoke Test

From repository root:

```bash
IMAGE=ghcr.io/<GHCR_OWNER>/logseq-selfhost-publish:<tag> ./images/publish/scripts/smoke-test.sh
```

Default checks:

- `/` returns publish HTML
- `/static/publish.css` returns `200`
- `POST /pages` returns `401` without auth

## Auto-track Upstream

Workflow: `.github/workflows/bump-selfhost-publish-ref.yml`

- Weekly Saturday 03:00 UTC
- Tracks latest commit in `logseq/logseq` touching `deps/publish`
- Updates `images/publish/UPSTREAM_PUBLISH_REF` and opens PR
