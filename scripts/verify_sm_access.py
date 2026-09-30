"""Проверка доступов из указанного .env (без печати секретов).

    python -m scripts.verify_sm_access --env /path/to.env
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def graph_ok(token: str, path: str, version: str) -> tuple[bool, str]:
    url = f"https://graph.facebook.com/{version}/{path.lstrip('/')}"
    req = urllib.request.Request(url + "?access_token=" + urllib.parse.quote(token))
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:200]
        return False, f"http {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__
    if data.get("error"):
        return False, str(data["error"].get("message", "error"))[:80]
    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    args = parser.parse_args()
    env_path = Path(args.env)
    vals = load_env(env_path)
    os.environ.update({k: v for k, v in vals.items() if v})
    ver = vals.get("META_GRAPH_API_VERSION") or "v25.0"
    failed = 0

    def report(name: str, ok: bool, detail: str) -> None:
        nonlocal failed
        print(f"[{'ok' if ok else 'fail'}] {name} {detail}")
        if not ok:
            failed += 1

    mrs = vals.get("META_ACCESS_TOKEN_MRS") or ""
    old = vals.get("META_ACCESS_TOKEN_OLD") or vals.get("META_ACCESS_TOKEN") or ""
    pix = vals.get("META_DATASET_ID_MRS") or ""
    act = vals.get("META_AD_ACCOUNT_ID_MRS") or ""

    if mrs:
        ok, detail = graph_ok(mrs, "me", ver)
        report("meta_mrs_me", ok, detail)
        if pix:
            ok, detail = graph_ok(mrs, pix, ver)
            report("meta_mrs_pixel", ok, detail)
        if act:
            aid = act if act.startswith("act_") else f"act_{act}"
            ok, detail = graph_ok(mrs, aid, ver)
            report("meta_mrs_account", ok, detail)
    else:
        report("meta_mrs_me", False, "no token")

    if old and old != mrs:
        ok, detail = graph_ok(old, "me", ver)
        report("meta_old_me", ok, detail)

    hey = vals.get("HEYGEN_API_KEY") or ""
    if hey:
        req = urllib.request.Request(
            "https://api.heygen.com/v3/users/me",
            headers={"X-Api-Key": hey, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                ok = resp.status == 200
            report("heygen_user_me", ok, "ok" if ok else f"http {resp.status}")
        except urllib.error.HTTPError as exc:
            report("heygen_user_me", False, f"http {exc.code}")
        except Exception as exc:  # noqa: BLE001
            report("heygen_user_me", False, type(exc).__name__)

    if not (vals.get("GOOGLE_ADS_CLIENT_ID") and vals.get("GOOGLE_ADS_REFRESH_TOKEN")):
        report("google_ads", False, "missing env")
    else:
        try:
            from scripts.verify_google_ads import main as ga_main

            code = ga_main()
            report("google_ads", code == 0, "verify_google_ads")
        except Exception as exc:  # noqa: BLE001
            report("google_ads", False, type(exc).__name__)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
