#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/yshalsager/logseq-web:latest}"
PORT="${PORT:-18080}"
CONTAINER="logseq-web-smoke-$$"

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run -d --rm --name "$CONTAINER" -p "127.0.0.1:${PORT}:8080" "$IMAGE" >/dev/null

ok=false
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/" >/tmp/logseq-web-smoke.html 2>/dev/null; then
    ok=true
    break
  fi
  sleep 1
done

if [[ "$ok" != true ]]; then
  echo "Smoke test failed: web app did not become ready on port ${PORT}" >&2
  exit 1
fi

status="$(curl -sS -o /tmp/logseq-web-smoke.html -w '%{http_code}' "http://127.0.0.1:${PORT}/")"
if [[ "$status" != "200" ]]; then
  echo "Smoke test failed: expected HTTP 200 from /, got ${status}" >&2
  exit 1
fi

if ! grep -Eqi '<!doctype html|<html' /tmp/logseq-web-smoke.html; then
  echo 'Smoke test failed: response body does not look like HTML' >&2
  exit 1
fi

echo "Smoke test passed for ${IMAGE}"
