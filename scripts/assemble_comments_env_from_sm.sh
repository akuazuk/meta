#!/usr/bin/env bash
# Собрать /opt/kravira-meta-comments/.env из Secret Manager (запускать на GCE).
set -euo pipefail
PROJECT="${GCP_PROJECT:-protocol-home-e1}"
OUT="${COMMENTS_ENV:-/opt/kravira-meta-comments/.env}"
OPS_USER="${GCE_OPS_USER:-pavel}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud not in PATH" >&2
  exit 2
fi

fetch() {
  local secret_id="$1"
  gcloud secrets versions access latest --secret="$secret_id" --project="$PROJECT" 2>/dev/null | tr -d '\r' | sed -e '${/^$/d;}'
}

need() {
  local env_key="$1"
  local secret_id="$2"
  local val
  val="$(fetch "$secret_id" || true)"
  if [[ -z "$val" ]]; then
    echo "ERROR: empty or missing secret $secret_id ($env_key)" >&2
    exit 2
  fi
  printf '%s=%s\n' "$env_key" "$val"
}

tmp="$(mktemp)"
chmod 600 "$tmp"
trap 'rm -f "$tmp"' EXIT

{
  echo "GOOGLE_SHEETS_ID=1LkaVoEZ7hQWR2FL0Iejjviutdte91SLq9rM7W5u80lU"
  echo "GOOGLE_APPLICATION_CREDENTIALS=/opt/kravira-meta-comments/service-account.json"
  echo "COMMENT_SINCE=2026-09-01"
  echo "TZ=Europe/Minsk"
  echo "GOOGLE_CLOUD_PROJECT=protocol-home-e1"
  echo "GEMINI_MODEL=gemini-2.5-flash"
  echo "GEMINI_LOCATION=europe-west1"
  echo "COMMENT_USE_GEMINI=1"
  need META_ACCESS_TOKEN_MRS meta-access-token-mrs
  need META_AD_ACCOUNT_ID_MRS meta-ad-account-id-mrs
  need META_PAGE_ID meta-page-id
  need META_INSTAGRAM_ID meta-instagram-id
  need META_GRAPH_API_VERSION meta-graph-api-version
} >>"$tmp"

# refuse dumping extra tokens into comments env
if grep -qE '^(META_APP_SECRET|HEYGEN_API_KEY|GOOGLE_ADS_REFRESH_TOKEN)=' "$tmp"; then
  echo "ERROR: comments env must not contain extra secrets" >&2
  exit 2
fi

sudo mkdir -p "$(dirname "$OUT")"
sudo cp "$tmp" "$OUT"
if getent passwd "$OPS_USER" >/dev/null 2>&1; then
  sudo chown "$OPS_USER:$OPS_USER" "$OUT"
else
  sudo chown "$(whoami):$(whoami)" "$OUT"
fi
sudo chmod 600 "$OUT"
echo "COMMENTS_ENV_ASSEMBLED path=$OUT keys=$(grep -cE '^[A-Z]' "$OUT")"
