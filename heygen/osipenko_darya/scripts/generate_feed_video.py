"""Генерация ролика Осипенко Дарья Петровна через HeyGen API.

Шаги: upload photo → photo avatar → video 1:1 + burned captions.
Запуск:
    source .venv/bin/activate
    python -m heygen.osipenko_darya.scripts.generate_feed_video
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
JOB_DIR = Path(__file__).resolve().parents[1]
INPUT = JOB_DIR / "input"
OUTPUT = JOB_DIR / "output"
SPEECH_FILE = JOB_DIR / "SPEECH.md"

load_dotenv(ROOT / ".env", override=True)

API = "https://api.heygen.com"
VOICE_ID = "bc69c9589d6747028dc5ec4aec2b43c3"  # Dariya - Professional (RU, female)
SOURCE = INPUT / "source.jpg"


def headers() -> dict:
    key = (os.getenv("HEYGEN_API_KEY") or "").strip()
    if not key:
        raise SystemExit("HEYGEN_API_KEY missing in .env")
    return {"X-Api-Key": key}


def speech_a() -> str:
    text = SPEECH_FILE.read_text(encoding="utf-8")
    # Extract variant A block between first --- and next ---
    parts = text.split("---")
    if len(parts) < 2:
        raise SystemExit("Cannot parse SPEECH.md variant A")
    body = parts[1].strip()
    # drop markdown headings if any leaked
    lines = [ln for ln in body.splitlines() if not ln.startswith("#")]
    return "\n".join(lines).strip()


def upload_photo(path: Path) -> str:
    with path.open("rb") as f:
        resp = requests.post(
            f"{API}/v3/assets",
            headers=headers(),
            files={"file": (path.name, f, "image/jpeg")},
            timeout=120,
        )
    resp.raise_for_status()
    data = resp.json().get("data") or {}
    asset_id = data.get("id") or data.get("asset_id")
    if not asset_id:
        # some responses nest differently
        print("upload response", resp.text[:500])
        raise RuntimeError("No asset_id in upload response")
    print("[ok] uploaded asset", asset_id)
    return asset_id


def create_photo_avatar(asset_id: str) -> str:
    resp = requests.post(
        f"{API}/v3/avatars",
        headers={**headers(), "Content-Type": "application/json"},
        json={
            "type": "photo",
            "name": "Osipenko Darya Petrovna",
            "file": {"type": "asset_id", "asset_id": asset_id},
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json().get("data") or {}
    item = data.get("avatar_item") or {}
    look_id = item.get("id")
    if not look_id:
        print(resp.text[:800])
        raise RuntimeError("No avatar look id")
    print("[ok] photo avatar", look_id, "group", (data.get("avatar_group") or {}).get("id"))
    (OUTPUT / "avatar.json").write_text(
        json.dumps(resp.json(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return look_id


def wait_avatar_ready(look_id: str, timeout_s: int = 600) -> None:
    """Photo avatar training is async – wait until status=completed."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(
            f"{API}/v3/avatars/{look_id}",
            headers=headers(),
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json().get("data") or {}
            item = data.get("avatar_item") or data
            status = str(item.get("status") or "").lower()
            print("[avatar status]", status or "(empty)")
            if status in {"completed", "ready", "success", "active"}:
                return
            if status == "failed":
                raise RuntimeError(f"Avatar failed: {item.get('error') or item}")
        else:
            # fallback: list looks
            resp2 = requests.get(
                f"{API}/v3/avatars/looks",
                headers=headers(),
                params={"limit": 50},
                timeout=60,
            )
            if resp2.status_code == 200:
                raw = resp2.json().get("data") or []
                items = raw if isinstance(raw, list) else (raw.get("items") or raw.get("looks") or [])
                for it in items:
                    if it.get("id") == look_id:
                        status = str(it.get("status") or "").lower()
                        print("[avatar status]", status or "(empty)")
                        if status in {"completed", "ready", "success", "active"}:
                            return
                        if status == "failed":
                            raise RuntimeError(f"Avatar failed: {it}")
                        # empty/unknown status: keep waiting (do NOT treat as ready)
        time.sleep(8)
    raise TimeoutError(f"Avatar {look_id} not ready in {timeout_s}s")


def create_video(avatar_id: str, script: str) -> str:
    # Keep original photo background (cabinet). Burn captions via caption.style.
    payload = {
        "type": "avatar",
        "title": "Osipenko Darya – feed 1x1 – variant A",
        "avatar_id": avatar_id,
        "script": script,
        "voice_id": VOICE_ID,
        "resolution": "1080p",
        "aspect_ratio": "1:1",
        "caption": {
            "file_format": "srt",
            "style": "default",
        },
    }
    resp = requests.post(
        f"{API}/v3/videos",
        headers={**headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if resp.status_code >= 400:
        print("create video error", resp.status_code, resp.text[:1000])
        resp.raise_for_status()
    data = resp.json().get("data") or {}
    video_id = data.get("video_id") or data.get("id")
    if not video_id:
        print(resp.text[:800])
        raise RuntimeError("No video_id")
    print("[ok] video job", video_id)
    (OUTPUT / "create_video.json").write_text(
        json.dumps(resp.json(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return video_id


def poll_video(video_id: str, timeout_s: int = 900) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(
            f"{API}/v3/videos/{video_id}",
            headers=headers(),
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json().get("data") or {}
        status = data.get("status")
        print("[video]", status, "duration", data.get("duration"))
        if status in {"completed", "failed"}:
            (OUTPUT / "video_status.json").write_text(
                json.dumps(resp.json(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return data
        time.sleep(10)
    raise TimeoutError("Video render timeout")


def download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    print("[ok] saved", dest, dest.stat().st_size, "bytes")


def wallet_balance() -> float:
    me = requests.get(f"{API}/v3/users/me", headers=headers(), timeout=30).json()
    wallet = (me.get("data") or {}).get("wallet") or {}
    return float(wallet.get("remaining_balance") or 0)


def reuse_look_id() -> str | None:
    """Reuse already-created photo avatar – never create duplicates by default."""
    path = OUTPUT / "avatar.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        item = ((raw.get("data") or {}).get("avatar_item") or {})
        look_id = item.get("id")
        if look_id:
            print("[reuse] look from avatar.json", look_id)
            return look_id
    # Prefer existing Osipenko group look from API
    resp = requests.get(f"{API}/v3/avatars", headers=headers(), params={"limit": 50}, timeout=90)
    resp.raise_for_status()
    for group in resp.json().get("data") or []:
        if group.get("name") != "Osipenko Darya Petrovna":
            continue
        gid = group.get("id")
        looks = requests.get(
            f"{API}/v3/avatars/{gid}/looks",
            headers=headers(),
            params={"limit": 10},
            timeout=60,
        )
        if looks.status_code != 200:
            continue
        items = looks.json().get("data") or []
        if isinstance(items, dict):
            items = items.get("items") or items.get("looks") or []
        for it in items:
            if str(it.get("status") or "").lower() in {"completed", "ready", "success", "active"}:
                print("[reuse] look from API", it.get("id"), "group", gid)
                return it.get("id")
    return None


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}")

    bal = wallet_balance()
    print("[wallet]", bal, "usd")
    # ~$1 avatar (if new) + ~$2 for ~40s Avatar IV photo; refuse if too low
    force_new = os.getenv("HEYGEN_FORCE_NEW_AVATAR", "").strip() in {"1", "true", "yes"}
    look_id = None if force_new else reuse_look_id()
    need_avatar_budget = 0.0 if look_id else 1.0
    if bal < need_avatar_budget + 2.0:
        raise SystemExit(
            f"Balance too low (${bal}). Need ~${need_avatar_budget + 2:.0f}+. "
            "Refusing to spend more without top-up."
        )

    script = speech_a()
    print("script chars", len(script))
    print(script[:180], "...")

    if not look_id:
        print("[warn] creating NEW photo avatar ($1) – set HEYGEN_FORCE_NEW_AVATAR only when needed")
        asset_id = upload_photo(SOURCE)
        look_id = create_photo_avatar(asset_id)
        wait_avatar_ready(look_id)
    else:
        print("[ok] skipping avatar create – reusing", look_id)

    video_id = create_video(look_id, script)
    data = poll_video(video_id)
    if data.get("status") != "completed":
        print("[error] render failed", data.get("failure_code"), data.get("failure_message"))
        return 2

    # Prefer captioned URL if present
    url = (
        data.get("captioned_video_url")
        or data.get("video_url")
        or data.get("url")
    )
    if not url:
        print("[error] no video url in response", data)
        return 3
    dest = OUTPUT / "osipenko_feed_1x1_captions.mp4"
    download(url, dest)
    # also keep clean if separate
    clean = data.get("video_url")
    if clean and clean != url:
        download(clean, OUTPUT / "osipenko_feed_1x1_clean.mp4")
    print("\n[done] balance check:", wallet_balance(), "usd")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.HTTPError as exc:
        print("[http]", exc)
        if exc.response is not None:
            print(exc.response.text[:1000])
        raise SystemExit(1)
