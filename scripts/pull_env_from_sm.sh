#!/usr/bin/env bash
# Собрать .env из Secret Manager (значения в stdout не печатает).
#   bash scripts/pull_env_from_sm.sh              # пишет meta/.env (с бэкапом)
#   bash scripts/pull_env_from_sm.sh --out FILE   # только FILE
#   bash scripts/pull_env_from_sm.sh --check      # сверить набор ключей с локальным .env
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT:-protocol-home-e1}"
OUT=""
CHECK=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="${2:-}"; shift 2 ;;
    --check) CHECK=1; shift ;;
    -h|--help)
      echo "Usage: pull_env_from_sm.sh [--out FILE] [--check]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$OUT" ]]; then
  OUT="$ROOT/.env"
fi

gcloud config set project "$PROJECT" --quiet >/dev/null

TMP="$(mktemp)"
chmod 600 "$TMP"
trap 'rm -f "$TMP"' EXIT

python3 - <<PY
import subprocess
import sys
sys.path.insert(0, "$ROOT")
from scripts.sm_config import SM_MAP

project = "$PROJECT"
lines = []
ok = 0
missing = []
for env_key, secret_id in SM_MAP.items():
    r = subprocess.run(
        [
            "gcloud", "secrets", "versions", "access", "latest",
            f"--secret={secret_id}", f"--project={project}",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        missing.append(env_key)
        print(f"SM_MISS key={env_key} secret={secret_id}", file=sys.stderr)
        continue
    val = r.stdout.rstrip("\n")
    lines.append(f"{env_key}={val}")
    ok += 1
    print(f"SM_OK key={env_key}", file=sys.stderr)

Path = __import__("pathlib").Path
Path("$TMP").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
print(f"SM_PULL keys={ok} missing={len(missing)}", file=sys.stderr)
if ok == 0:
    sys.exit(2)
PY

if [[ "$CHECK" == "1" ]]; then
  python3 - <<PY
from pathlib import Path
local = Path("$ROOT/.env")
pulled = Path("$TMP")
def keys(p):
    out = set()
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        if v.strip():
            out.add(k.strip())
    return out
l, r = keys(local), keys(pulled)
only_local = sorted(l - r)
only_sm = sorted(r - l)
print(f"CHECK local_set={len(l)} sm_set={len(r)}")
if only_local:
    print("CHECK only_local", ",".join(only_local))
if only_sm:
    print("CHECK only_sm", ",".join(only_sm))
if not only_local:
    print("CHECK_OK sm has every non-empty local mapped key")
PY
  exit 0
fi

if [[ "$OUT" == "$ROOT/.env" && -f "$OUT" ]]; then
  bak="$OUT.bak.$(date +%Y%m%d%H%M%S)"
  cp -p "$OUT" "$bak"
  echo "SM_BACKUP $bak"
fi

# Keep unmapped local keys (test codes etc.) when writing the main .env
if [[ "$OUT" == "$ROOT/.env" && -f "$OUT" ]]; then
  python3 - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "$ROOT")
from scripts.sm_config import SM_MAP

old = {}
for line in Path("$OUT").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k, v = s.split("=", 1)
    old[k.strip()] = v.strip()
new = {}
for line in Path("$TMP").read_text(encoding="utf-8").splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        new[k] = v
# SM wins for mapped keys; keep extra local keys
for k, v in old.items():
    if k not in SM_MAP:
        new[k] = v
text = "\n".join(f"{k}={v}" for k, v in new.items()) + "\n"
Path("$OUT").write_text(text, encoding="utf-8")
Path("$OUT").chmod(0o600)
print(f"SM_WROTE path=$OUT keys={len(new)}")
PY
else
  cp "$TMP" "$OUT"
  chmod 600 "$OUT"
  echo "SM_WROTE path=$OUT"
fi
