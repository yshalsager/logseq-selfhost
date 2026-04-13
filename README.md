# Logseq Sync Server (Node Adapter)

This repository provides a minimal self-host setup for Logseq's `db-sync` node adapter using Docker Compose.

It includes:
- `mise.toml` to pin build toolchain versions (Node, Java, Clojure)
- `Dockerfile` to build `worker/dist/node-adapter.js` from upstream Logseq with distroless non-root runtime
- `docker-compose.yml` to run the sync server with persistent data
- GitHub Actions workflow to build and push an updatable image to GHCR
- GitHub Actions workflow that tracks the latest upstream commit touching `deps/db-sync` and opens a PR
- `UPSTREAM_DB_SYNC_REF` as the pinned upstream commit used by default builds

## Upstream Logseq URLs

- [Logseq repository](https://github.com/logseq/logseq)
- Custom Sync Server URL support PR: [logseq/logseq#12459](https://github.com/logseq/logseq/pull/12459)
- `deps/db-sync` node-adapter [README.md](https://github.com/logseq/logseq/blob/master/deps/db-sync/README.md)
- [Logseq releases](https://github.com/logseq/logseq/releases/latest)
- [Logseq Android (Play Store)](https://play.google.com/store/apps/details?id=com.logseq.app)

## 0) Local tooling with `mise`

Mise docs: [mise.jdx.dev](https://mise.jdx.dev/)

Install pinned tool versions from `mise.toml`:

```bash
mise install
```

Optional quick check:

```bash
mise exec -- node -v
mise exec -- java -version
mise exec -- clojure -Sdescribe
```

The Docker build also uses `mise.toml` and a pinned `MISE_VERSION` in `Dockerfile` for reproducible builds.

## 1) Configure environment

```bash
cp .env.example .env
```

Edit `.env` values:
- `GHCR_OWNER`: your GitHub username/org that owns the package
- `IMAGE_TAG`: image tag to deploy (`latest` or a pinned tag)
- `SYNC_PORT`: VPS port to expose
- `DB_SYNC_BASE_URL`: public URL clients use for sync
- `DB_SYNC_DATA_DIR`: default is `/app/data` for writable persistent volume with non-root runtime
- `COGNITO_*`: auth settings used by the node adapter for JWT validation

## 2) Build and publish image (GitHub Actions)

Workflow file: `.github/workflows/build-sync-image.yml`

Triggers:
- Manual (`workflow_dispatch`) with optional `logseq_ref` and `image_tag`
- Weekly schedule (Saturday 04:00 UTC fallback)
- Push changes to `Dockerfile`, `UPSTREAM_DB_SYNC_REF`, or workflow on `main`

By default, the build uses `UPSTREAM_DB_SYNC_REF` (latest known upstream commit for `deps/db-sync`).
You can override it manually with `workflow_dispatch` input `logseq_ref`.
Build toolchain versions are pinned in `mise.toml`.

The workflow publishes to:
- `ghcr.io/<GHCR_OWNER>/logseq-sync-server:<tag>`
- `ghcr.io/<GHCR_OWNER>/logseq-sync-server:latest` (for `main` builds)

### GHCR package access

If your VPS pulls anonymously, make sure the package is public in GitHub Packages.
If private, run `docker login ghcr.io` on the VPS first.

## 3) Deploy on VPS

```bash
docker compose pull
docker compose up -d
```

## 4) Update later (updatable image flow)

If `IMAGE_TAG=latest`:
```bash
docker compose pull sync
docker compose up -d sync
```

If pinning explicit tags:
1. Change `IMAGE_TAG` in `.env`.
2. Run:
```bash
docker compose pull sync
docker compose up -d sync
```

## 5) Smoke test

Run this after build/deploy:

```bash
IMAGE=ghcr.io/<GHCR_OWNER>/logseq-sync-server:<tag> ./scripts/smoke-test.sh
```

By default, it validates:
- `/health` returns `200` with `{"ok":true}`
- `/graphs` returns `401` without auth
- `/sync/<graph-id>/pull?since=0` returns `401` without auth

If you have a valid Logseq Cognito bearer token, provide it to validate authenticated sync pull:

```bash
BEARER_TOKEN='<jwt>' IMAGE=ghcr.io/<GHCR_OWNER>/logseq-sync-server:<tag> ./scripts/smoke-test.sh
```

## 6) Logseq client setup

Use a Logseq version that includes custom sync server URL support (PR `#12459`).
Then set your sync endpoint in Logseq to your server URL.

## 7) Auto-track db-sync upstream changes

Workflow file: `.github/workflows/bump-db-sync-ref.yml`

What it does:
- Weekly checks latest commit in `logseq/logseq` that touched `deps/db-sync` (Saturday 03:00 UTC)
- If changed, updates `UPSTREAM_DB_SYNC_REF`
- Opens a PR in this repo with that update

Merging that PR triggers image rebuild (because `UPSTREAM_DB_SYNC_REF` changed).

## Notes

- This repo intentionally does not include reverse proxy or TLS setup.
- Persisted data is stored in Docker volume `sync_data` mounted at `/app/data`.
- Back up volume data before major upgrades.

## License

This repository is licensed under `AGPL-3.0-or-later` (see `LICENSE`).

It builds and packages upstream Logseq `deps/db-sync` from the commit pinned in `UPSTREAM_DB_SYNC_REF`.
