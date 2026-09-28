"""Вариант A + Anya + фон jul29-style + белые субтитры без обводки.

Один job. Аватар не создаём. Запуск из meta/:
    python -m heygen.osipenko_darya.scripts.generate_variant_a_jul29
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
JOB_DIR = Path(__file__).resolve().parents[1]
OUTPUT = JOB_DIR / "output"
SPEECH_FILE = JOB_DIR / "SPEECH.md"
BG_PATH = JOB_DIR / "input" / "backgrounds" / "cabinet_bg_jul29_style.jpg"
LOOK_ID = "57f149749cb146f7bff7582309a58517"
VOICE_ANYA = "37832e32d4f7475ab7a1cb0db8e5dd66"
API = "https://api.heygen.com"
STATE_FILE = OUTPUT / "create_video_a_jul29.json"

load_dotenv(ROOT / ".env", override=True)


def headers() -> dict:
    key = (os.getenv("HEYGEN_API_KEY") or "").strip()
    if not key:
        raise SystemExit("HEYGEN_API_KEY missing")
    return {"X-Api-Key": key}


def wallet() -> float:
    me = requests.get(f"{API}/v3/users/me", headers=headers(), timeout=60).json()
    return float(((me.get("data") or {}).get("wallet") or {}).get("remaining_balance") or 0)


def speech_a() -> str:
    parts = SPEECH_FILE.read_text(encoding="utf-8").split("---")
    if len(parts) < 2:
        raise SystemExit("Cannot parse SPEECH.md variant A")
    body = parts[1].strip()
    lines = [ln for ln in body.splitlines() if not ln.startswith("#")]
    return "\n".join(lines).strip()


def upload_asset(path: Path, mime: str) -> str:
    with path.open("rb") as f:
        resp = requests.post(
            f"{API}/v3/assets",
            headers=headers(),
            files={"file": (path.name, f, mime)},
            timeout=180,
        )
    resp.raise_for_status()
    data = resp.json().get("data") or {}
    asset_id = data.get("id") or data.get("asset_id")
    if not asset_id:
        raise RuntimeError(resp.text[:500])
    print("[ok] asset", asset_id)
    return asset_id


def create_video(look_id: str, script: str, bg_asset_id: str) -> str:
    payload = {
        "type": "avatar",
        "title": "Osipenko Darya – feed 1x1 – variant A – Anya – jul29 bg",
        "avatar_id": look_id,
        "script": script,
        "voice_id": VOICE_ANYA,
        "resolution": "1080p",
        "aspect_ratio": "1:1",
        "remove_background": True,
        "background": {"type": "image", "asset_id": bg_asset_id},
        "caption": {"file_format": "srt"},
    }
    resp = requests.post(
        f"{API}/v3/videos",
        headers={**headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if resp.status_code >= 400:
        print(resp.status_code, resp.text[:1500])
        resp.raise_for_status()
    data = resp.json().get("data") or {}
    video_id = data.get("video_id") or data.get("id")
    if not video_id:
        raise RuntimeError(resp.text[:800])
    STATE_FILE.write_text(json.dumps(resp.json(), ensure_ascii=False, indent=2), encoding="utf-8")
    print("[ok] video job", video_id)
    return video_id


def get_status(video_id: str) -> dict:
    last_err = None
    for _ in range(5):
        try:
            resp = requests.get(f"{API}/v3/videos/{video_id}", headers=headers(), timeout=90)
            resp.raise_for_status()
            return resp.json().get("data") or {}
        except Exception as exc:
            last_err = exc
            time.sleep(3)
    raise RuntimeError(last_err)


def poll(video_id: str) -> dict:
    deadline = time.time() + 900
    while time.time() < deadline:
        data = get_status(video_id)
        print("[video]", data.get("status"), "duration", data.get("duration"))
        if data.get("status") in {"completed", "failed"}:
            (OUTPUT / "video_status_a_jul29.json").write_text(
                json.dumps({"data": data}, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return data
        time.sleep(12)
    raise TimeoutError("timeout")


def download(url: str, dest: Path) -> None:
    last_err = None
    for _ in range(4):
        try:
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with dest.open("wb") as f:
                    for chunk in r.iter_content(256 * 1024):
                        if chunk:
                            f.write(chunk)
            print("[ok] saved", dest, dest.stat().st_size)
            return
        except Exception as exc:
            last_err = exc
            time.sleep(2)
    raise RuntimeError(last_err)


def burn_white_no_outline(video: Path, srt: Path, dest: Path) -> None:
    srt_esc = str(srt.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    force = (
        "FontName=Arial,"
        "FontSize=20,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=0,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=90"
    )
    vf = f"subtitles={srt_esc}:force_style='{force}'"
    cmd = ["ffmpeg", "-y", "-i", str(video), "-vf", vf, "-c:a", "copy", str(dest)]
    print("[ffmpeg]", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("[ok] captions", dest, dest.stat().st_size)


def existing_in_progress() -> str | None:
    if not STATE_FILE.exists():
        return None
    try:
        prev = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        vid = (prev.get("data") or {}).get("video_id")
        if not vid:
            return None
        status = get_status(vid).get("status")
        if status in {"pending", "waiting", "processing"}:
            return vid
    except Exception:
        return None
    return None


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not BG_PATH.exists():
        raise SystemExit(f"Missing {BG_PATH}")

    bal0 = wallet()
    print("[wallet before]", bal0)
    if bal0 < 2.0:
        raise SystemExit(f"Balance too low: ${bal0}")

    in_prog = existing_in_progress()
    if in_prog:
        print("[reuse] already rendering", in_prog)
        video_id = in_prog
    else:
        script = speech_a()
        print("[script A chars]", len(script))
        print(script[:180], "...")
        print("[look]", LOOK_ID, "[voice] Anya [bg] jul29-style")
        bg_id = upload_asset(BG_PATH, "image/jpeg")
        video_id = create_video(LOOK_ID, script, bg_id)

    data = poll(video_id)
    if data.get("status") != "completed":
        print("[failed]", data.get("failure_code"), data.get("failure_message"))
        return 2

    clean = OUTPUT / "osipenko_feed_1x1_A_jul29_clean.mp4"
    final = OUTPUT / "osipenko_feed_1x1_A_jul29_captions.mp4"
    srt_path = OUTPUT / "osipenko_feed_1x1_A_jul29.srt"
    download(data["video_url"], clean)
    sub = data.get("subtitle_url")
    if sub:
        download(sub, srt_path)
        text = srt_path.read_bytes().decode("utf-8-sig", errors="replace")
        text = re.sub(r"<[^>]+>", "", text)
        srt_path.write_text(text, encoding="utf-8")
        burn_white_no_outline(clean, srt_path, final)
    else:
        print("[warn] no subtitle_url")

    bal1 = wallet()
    print("[wallet after]", bal1, "spent ~", round(bal0 - bal1, 2))
    print("[done]", final if final.exists() else clean)
    print("[page]", data.get("video_page_url"))
    print("[duration]", data.get("duration"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.HTTPError as exc:
        print("[http]", exc)
        if exc.response is not None:
            print(exc.response.text[:1200])
        raise SystemExit(1)
