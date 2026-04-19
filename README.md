# Logseq Self-hosted Images Monorepo

[![Build Sync Image](https://github.com/yshalsager/logseq-sync-server/actions/workflows/build-sync-image.yml/badge.svg)](https://github.com/yshalsager/logseq-sync-server/actions/workflows/build-sync-image.yml)
[![Build Web Image](https://github.com/yshalsager/logseq-sync-server/actions/workflows/build-web-image.yml/badge.svg)](https://github.com/yshalsager/logseq-sync-server/actions/workflows/build-web-image.yml)
[![Bump Sync Ref](https://github.com/yshalsager/logseq-sync-server/actions/workflows/bump-db-sync-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-sync-server/actions/workflows/bump-db-sync-ref.yml)
[![Bump Web Ref](https://github.com/yshalsager/logseq-sync-server/actions/workflows/bump-logseq-db-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-sync-server/actions/workflows/bump-logseq-db-ref.yml)
[![License](https://img.shields.io/github/license/yshalsager/logseq-sync-server.svg)](https://github.com/yshalsager/logseq-sync-server/blob/master/LICENSE)

This repository publishes two self-hosted images from one codebase:

- `ghcr.io/<owner>/logseq-sync-server` (Logseq `deps/db-sync` node adapter)
- `ghcr.io/<owner>/logseq-web` (Logseq DB web app static bundle)

## Layout

- `images/sync`: sync image Docker/build/deploy/smoke files
- `images/web`: web image Docker/build/deploy/smoke files
- `.github/workflows`: reusable build/bump workflows and thin wrappers
- `mise.toml`: shared pinned toolchain for both image builds

## Documentation

- [Sync image guide](images/sync/README.md)
- [Web image guide](images/web/README.md)

## Upstream

- [Logseq repository](https://github.com/logseq/logseq)
- Custom sync server URL support: [logseq/logseq#12459](https://github.com/logseq/logseq/pull/12459)
- DB web branch currently tracked: `test/db`

## License

This repository is licensed under `AGPL-3.0-or-later` (see `LICENSE`).
