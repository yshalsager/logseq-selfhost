#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-${1:-logseq-selfhost-publish:local}}"
PORT="${PORT:-18788}"
CONTAINER_NAME="${CONTAINER_NAME:-logseq-selfhost-publish-smoke}"
WAIT_SECONDS="${WAIT_SECONDS:-4}"
MAX_RETRIES="${MAX_RETRIES:-30}"

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

docker run -d --rm \
  --name "${CONTAINER_NAME}" \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /app/worker/.wrangler/tmp:uid=1000,gid=1000,mode=1777 \
  --tmpfs /app/worker/node_modules/.mf:uid=1000,gid=1000,mode=1777 \
  -v "${CONTAINER_NAME}_data:/data" \
  -p "127.0.0.1:${PORT}:8787" \
  "${IMAGE}" >/dev/null

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker volume rm "${CONTAINER_NAME}_data" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep "${WAIT_SECONDS}"

home_html=''
for _ in $(seq 1 "${MAX_RETRIES}"); do
  if home_html="$(curl --noproxy '*' -fsS "http://127.0.0.1:${PORT}/" 2>/dev/null)"; then
    break
  fi
  sleep 1
done

if [ -z "${home_html}" ]; then
  echo "publish worker did not become ready after ${MAX_RETRIES} retries" >&2
  docker logs --tail 100 "${CONTAINER_NAME}" >&2 || true
  exit 1
fi

if ! grep -Eqi '<!doctype html|<html|Logseq Publish' <<<"${home_html}"; then
  echo "expected / to return publish HTML" >&2
  exit 1
fi

css_status="$(curl --noproxy '*' -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/static/publish.css")"
if [ "${css_status}" != "200" ]; then
  echo "expected /static/publish.css status 200, got ${css_status}" >&2
  exit 1
fi

pages_status="$(
  curl --noproxy '*' -sS -o /dev/null -w '%{http_code}' \
    -X POST \
    -H 'content-type: application/transit+json' \
    --data '[]' \
    "http://127.0.0.1:${PORT}/pages"
)"
if [ "${pages_status}" != "401" ]; then
  echo "expected unauthenticated POST /pages status 401, got ${pages_status}" >&2
  exit 1
fi

echo "smoke test passed"
