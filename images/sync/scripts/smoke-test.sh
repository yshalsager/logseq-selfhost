#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-${1:-logseq-sync-server:local}}"
PORT="${PORT:-18787}"
DB_SYNC_ADMIN_TOKEN="${DB_SYNC_ADMIN_TOKEN:-smoke-admin-token}"
GRAPH_ID="${GRAPH_ID:-smoke-graph}"
BEARER_TOKEN="${BEARER_TOKEN:-}"
CONTAINER_NAME="${CONTAINER_NAME:-logseq-sync-server-smoke}"
WAIT_SECONDS="${WAIT_SECONDS:-4}"
MAX_HEALTH_RETRIES="${MAX_HEALTH_RETRIES:-20}"

json_assert() {
  local expr="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -e "$expr" >/dev/null
  else
    case "$expr" in
      '.ok == true')
        grep -Eq '"ok"[[:space:]]*:[[:space:]]*true'
        ;;
      '.type=="pull/ok" and (.t|type=="number") and (.txs|type=="array")')
        grep -Eq '"type"[[:space:]]*:[[:space:]]*"pull/ok"' \
          && grep -Eq '"t"[[:space:]]*:[[:space:]]*[0-9]+' \
          && grep -Eq '"txs"[[:space:]]*:[[:space:]]*\['
        ;;
      *)
        echo "unsupported json assertion without jq: ${expr}" >&2
        return 1
        ;;
    esac
  fi
}

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

docker run -d --rm \
  --name "${CONTAINER_NAME}" \
  -p "${PORT}:8787" \
  -e DB_SYNC_ADMIN_TOKEN="${DB_SYNC_ADMIN_TOKEN}" \
  "${IMAGE}" >/dev/null

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep "${WAIT_SECONDS}"

# 1) Liveness
health_json=''
for _ in $(seq 1 "${MAX_HEALTH_RETRIES}"); do
  if health_json="$(curl --noproxy '*' -fsS "http://127.0.0.1:${PORT}/health" 2>/dev/null)"; then
    break
  fi
  sleep 1
done
if [ -z "${health_json}" ]; then
  echo "health check failed after ${MAX_HEALTH_RETRIES} retries" >&2
  docker logs --tail 100 "${CONTAINER_NAME}" >&2 || true
  exit 1
fi
printf '%s' "${health_json}" | json_assert '.ok == true'

# 2) Auth gate (no token should be rejected)
graphs_status="$(curl --noproxy '*' -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/graphs")"
if [ "${graphs_status}" != "401" ]; then
  echo "expected /graphs status 401, got ${graphs_status}" >&2
  exit 1
fi

# 3) Sync route auth gate (or full pull when BEARER_TOKEN is provided)
sync_pull_url="http://127.0.0.1:${PORT}/sync/${GRAPH_ID}/pull?since=0"
if [ -n "${BEARER_TOKEN}" ]; then
  pull_json="$(
    curl --noproxy '*' -fsS \
      -H "authorization: Bearer ${BEARER_TOKEN}" \
      "${sync_pull_url}"
  )"
  printf '%s' "${pull_json}" | json_assert '.type=="pull/ok" and (.t|type=="number") and (.txs|type=="array")'
else
  sync_status="$(curl --noproxy '*' -sS -o /dev/null -w '%{http_code}' "${sync_pull_url}")"
  if [ "${sync_status}" != "401" ]; then
    echo "expected unauthenticated /sync pull status 401, got ${sync_status}" >&2
    exit 1
  fi
fi

echo "smoke test passed"
