# Logseq Sync Server (Node Adapter)

[![Build Image](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-sync-image.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-sync-image.yml)
[![Bump Upstream Ref](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-sync-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-sync-ref.yml)
[![ghcr.io tag](https://ghcr-badge.egpl.dev/yshalsager/logseq-selfhost-sync/latest_tag?ignore=latest,buildcache*,sha256*&trim=major&label=GitHub%20Registry&color=steelblue)](https://github.com/yshalsager/logseq-selfhost/pkgs/container/logseq-selfhost-sync)
[![ghcr.io size](https://ghcr-badge.egpl.dev/yshalsager/logseq-selfhost-sync/size?tag=latest&label=Image%20size&color=steelblue)](https://github.com/yshalsager/logseq-selfhost/pkgs/container/logseq-selfhost-sync)
[![License](https://img.shields.io/github/license/yshalsager/logseq-selfhost.svg)](https://github.com/yshalsager/logseq-selfhost/blob/master/LICENSE)

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

Workflow: `.github/workflows/build-selfhost-sync-image.yml`

Triggers:

- `workflow_dispatch` with optional `logseq_ref`, `image_tag`
- Weekly fallback: Saturday 04:00 UTC
- Push to `master` affecting image build inputs (`Dockerfile`, pinned upstream ref, or shared `mise.toml`)

Pinned upstream ref file: `images/sync/UPSTREAM_DB_SYNC_REF`

Published tags:

- `ghcr.io/<GHCR_OWNER>/logseq-selfhost-sync:<tag>`
- `ghcr.io/<GHCR_OWNER>/logseq-selfhost-sync:latest` (default branch builds)

## Deploy

From repository root:

```bash
docker compose -f images/sync/docker-compose.yml pull
docker compose -f images/sync/docker-compose.yml up -d
```

## Smoke test

From repository root:

```bash
IMAGE=ghcr.io/<GHCR_OWNER>/logseq-selfhost-sync:<tag> ./images/sync/scripts/smoke-test.sh
```

Default checks:

- `/health` returns `200` with `{"ok":true}`
- `/graphs` returns `401` without auth
- `/sync/<graph-id>/pull?since=0` returns `401` without auth

## Optional read-only dashboard

The dashboard is an optional sidecar for the Sync service. It reads the same
`sync_data` volume as read-only and exposes redacted operational metadata:

- user and graph counts, plus seven-day activity
- graph name, shortened ID, E2EE/ready/schema state
- transaction count, latest `t`, last sync time and shortened checksum
- graph database size and asset count/size/update time

It never queries the graph `kvs` table or reads asset contents, email addresses,
JWTs or admin tokens. It does not mount the Docker socket. Host CPU, container
restarts and system backup status are intentionally out of scope because the
sidecar has no portable, least-privilege source for them.

Copy and configure the optional sidecar environment if needed, then enable the
Compose profile:

```bash
cp images/sync/dashboard.env.example images/sync/dashboard.env
docker compose -f images/sync/docker-compose.yml --profile dashboard pull
docker compose -f images/sync/docker-compose.yml --profile dashboard up -d
```

The default listener is `127.0.0.1:8080`, and the dashboard is served below
`/dashboard/`. Both Basic Auth values are optional: leave
`DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` empty to disable application-level
authentication, or set both to enable it. Setting only one makes the sidecar
fail fast.

Expose it below the same Sync hostname with Caddy. Use `handle`, rather than
`handle_path`, so the dashboard receives its `/dashboard` base path:

```caddyfile
sync.example.com {
	@dashboard path /dashboard /dashboard/*
	handle @dashboard {
		reverse_proxy 127.0.0.1:8080
	}

	handle {
		reverse_proxy 127.0.0.1:8787
	}
}
```

The equivalent nginx location is:

```nginx
location /dashboard/ {
    proxy_pass http://127.0.0.1:8080;
}
```

## Auto-track upstream

Workflow: `.github/workflows/bump-selfhost-sync-ref.yml`

- Weekly Saturday 03:00 UTC
- Tracks latest commit in `logseq/logseq` touching `deps/db-sync`
- Updates `images/sync/UPSTREAM_DB_SYNC_REF` and opens PR
