#!/usr/bin/env bash
# Local Meta Ads MCP for Cursor. Official mcp.facebook.com/ads needs OAuth
# that Cursor cannot finish (401 / Error). This uses the System User token.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
export META_ACCESS_TOKEN="${META_ACCESS_TOKEN_MRS:-${META_ACCESS_TOKEN:-}}"
if [[ -z "${META_ACCESS_TOKEN}" ]]; then
  echo "META_ACCESS_TOKEN_MRS is empty in .env" >&2
  exit 1
fi
# .env secret is for another app; a mismatched appsecret_proof makes
# every Graph call fail. Direct API works without proof.
unset META_APP_SECRET
exec "$ROOT/.venv/bin/meta-ads-mcp" --transport stdio
