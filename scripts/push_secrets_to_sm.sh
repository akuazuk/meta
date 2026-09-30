#!/usr/bin/env bash
# Заливка allowlist из meta/.env в Secret Manager (как Protocol push_web_secrets.sh).
# Значения в stdout не печатает.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PROJECT="${GCP_PROJECT:-protocol-home-e1}"
ZONE="${GCP_ZONE:-europe-central2-a}"
VM="${GCP_VM:-protocol-app}"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "ERROR: нет $ROOT/.env" >&2
  exit 2
fi

gcloud config set project "$PROJECT" --quiet >/dev/null

SM_DIR="$(mktemp -d)"
chmod 700 "$SM_DIR"
trap 'rm -rf "$SM_DIR"' EXIT

python3 - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "$ROOT")
from scripts.sm_config import SM_MAP

vals = {}
for line in Path("$ROOT/.env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k, v = s.split("=", 1)
    k, v = k.strip(), v.strip().strip('"').strip("'")
    if v:
        vals[k] = v

out = Path("$SM_DIR")
n = 0
for env_key, secret_id in SM_MAP.items():
    val = vals.get(env_key)
    if not val:
        print(f"SM_SKIP empty={env_key}")
        continue
    p = out / secret_id
    p.write_text(val, encoding="utf-8")
    p.chmod(0o600)
    n += 1
    print(f"SM_READY secret={secret_id}")
print(f"SM_FILES {n}")
PY

SA="$(gcloud compute instances describe "$VM" --zone="$ZONE" --project="$PROJECT" \
  --format='get(serviceAccounts[0].email)' 2>/dev/null || true)"
if [[ -z "${SA:-}" ]]; then
  echo "WARN: VM $VM недоступна, IAM на compute SA не выдам (секреты всё равно залью)"
fi

upsert_secret() {
  local secret_id="$1"
  local file="$2"
  if gcloud secrets describe "$secret_id" --project="$PROJECT" >/dev/null 2>&1; then
    gcloud secrets versions add "$secret_id" --data-file="$file" --project="$PROJECT" >/dev/null
    echo "SM_VERSION_ADDED secret=$secret_id"
  else
    gcloud secrets create "$secret_id" --data-file="$file" \
      --project="$PROJECT" --replication-policy=automatic >/dev/null
    echo "SM_CREATED secret=$secret_id"
  fi
  if [[ -n "${SA:-}" ]]; then
    gcloud secrets add-iam-policy-binding "$secret_id" \
      --project="$PROJECT" \
      --member="serviceAccount:${SA}" \
      --role="roles/secretmanager.secretAccessor" \
      --quiet >/dev/null || true
  fi
}

shopt -s nullglob
for f in "$SM_DIR"/*; do
  [[ -f "$f" ]] || continue
  upsert_secret "$(basename "$f")" "$f"
done

echo "SM_PUSH_DONE project=$PROJECT"
