# Logseq Self-hosted Images Monorepo

[![Build Sync Image](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-sync-image.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-sync-image.yml)
[![Build Publish Image](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-publish-image.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-publish-image.yml)
[![Build Web Image](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-web-image.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/build-selfhost-web-image.yml)
[![Bump Sync Ref](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-sync-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-sync-ref.yml)
[![Bump Publish Ref](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-publish-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-publish-ref.yml)
[![Bump Web Ref](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-web-ref.yml/badge.svg)](https://github.com/yshalsager/logseq-selfhost/actions/workflows/bump-selfhost-web-ref.yml)
[![License](https://img.shields.io/github/license/yshalsager/logseq-selfhost.svg)](https://github.com/yshalsager/logseq-selfhost/blob/master/LICENSE)

This repository publishes three self-hosted images from one codebase:

- `ghcr.io/<owner>/logseq-selfhost-sync` (Logseq `deps/db-sync` node adapter)
- `ghcr.io/<owner>/logseq-selfhost-publish` (Logseq `deps/publish` worker through Wrangler local runtime)
- `ghcr.io/<owner>/logseq-selfhost-web` (Logseq DB web app static bundle)

## Layout

- `images/sync`: sync image Docker/build/deploy/smoke files
- `images/publish`: publish image Docker/build/deploy/smoke files
- `images/web`: web image Docker/build/deploy/smoke files
- `.github/workflows`: reusable build/bump workflows and thin wrappers
- `mise.toml`: shared pinned toolchain for image builds

## Documentation

- [Sync image guide](images/sync/README.md)
- [Publish image guide](images/publish/README.md)
- [Web image guide](images/web/README.md)

## Upstream

- [Logseq repository](https://github.com/logseq/logseq)
- Custom sync server URL support: [logseq/logseq#12459](https://github.com/logseq/logseq/pull/12459)
- Publish server URL support is required in the Logseq client to point at `logseq-selfhost-publish`
- DB web branch currently tracked: `master`

## License

This repository is licensed under `AGPL-3.0-or-later` (see `LICENSE`).
