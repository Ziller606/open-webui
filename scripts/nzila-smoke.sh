#!/usr/bin/env bash
# Smoke-check Nzila API on a running Open WebUI instance.
set -euo pipefail

BASE_URL="${NZILA_SMOKE_BASE_URL:-http://127.0.0.1:8080}"
TOKEN="${NZILA_SMOKE_TOKEN:-}"
API="${BASE_URL%/}/api/v1/nzila"

auth_args=()
if [[ -n "$TOKEN" ]]; then
	auth_args=(-H "Authorization: Bearer ${TOKEN}")
fi

pass=0
fail=0

check() {
	local name="$1"
	local method="$2"
	local path="$3"
	local expect="${4:-200}"
	local extra=()
	if [[ $# -ge 5 ]]; then
		extra=("${@:5}")
	fi
	local code
	code="$(curl -s -o /tmp/nzila-smoke-body.json -w '%{http_code}' -X "$method" "${auth_args[@]}" "${extra[@]}" "${API}${path}")"
	if [[ "$code" == "$expect" ]] || [[ "$expect" == "any" && "$code" =~ ^[23] ]]; then
		echo "PASS  ${name} (${code})"
		pass=$((pass + 1))
	else
		echo "FAIL  ${name} (expected ${expect}, got ${code})"
		cat /tmp/nzila-smoke-body.json 2>/dev/null || true
		echo
		fail=$((fail + 1))
	fi
}

echo "Nzila smoke — ${API}"
echo "Set NZILA_SMOKE_BASE_URL and NZILA_SMOKE_TOKEN if needed."
echo

check "safe-ctx" GET "/safe-ctx" "200"
check "gpu-stats" GET "/gpu-stats" "any"
check "loaded" GET "/loaded" "200"
check "fit sample" GET "/fit/llama3.2" "any"

echo
echo "Summary: ${pass} passed, ${fail} failed"
[[ "$fail" -eq 0 ]]
