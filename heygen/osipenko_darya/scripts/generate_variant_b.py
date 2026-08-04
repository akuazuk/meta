"""Одноразовая генерация: вариант B, Anya, фон cream, белые крупные субтитры.

Запуск (из meta/):
    source .venv/bin/activate
    python -m heygen.osipenko_darya.scripts.generate_variant_b
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
BG_PATH = JOB_DIR / "input" / "backgrounds" / "cabinet_bg_b_cream.jpg"
LOOK_ID = "57f149749cb146f7bff7582309a58517"  # existing photo avatar look
VOICE_ANYA = "37832e32d4f7475ab7a1cb0db8e5dd66"
API = "https://api.heygen.com"

load_dotenv(ROOT / ".env", override=True)


def headers() -> dict:
    key = (os.getenv("HEYGEN_API_KEY") or "").strip()
    if not key:
        raise SystemExit("HEYGEN_API_KEY missing")
    return {"X-Api-Key": key}


def wallet() -> float:
    me = requests.get(f"{API}/v3/users/me", headers=headers(), timeout=30).json()
    return float(((me.get("data") or {}).get("wallet") or {}).get("remaining_balance") or 0)


def speech_b() -> str:
    parts = SPEECH_FILE.read_text(encoding="utf-8").split("---")
    if len(parts) < 3:
        raise SystemExit("Cannot parse SPEECH.md variant B")
    body = parts[2].strip()
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
        raise RuntimeError(f"No asset id: {resp.text[:500]}")
    print("[ok] asset", asset_id, path.name)
    return asset_id


def create_video(look_id: str, script: str, bg_asset_id: str) -> str:
    payload = {
        "type": "avatar",
        "title": "Osipenko Darya – feed 1x1 – variant B – Anya – cream",
        "avatar_id": look_id,
        "script": script,
        "voice_id": VOICE_ANYA,
        "resolution": "1080p",
        "aspect_ratio": "1:1",
        "remove_background": True,
        "background": {"type": "image", "asset_id": bg_asset_id},
        # SRT only – burn white/large locally
        "caption": {"file_format": "srt"},
    }
    resp = requests.post(
        f"{API}/v3/videos",
        headers={**headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if resp.status_code >= 400:
        print("[create error]", resp.status_code, resp.text[:1500])
        resp.raise_for_status()
    data = resp.json().get("data") or {}
    video_id = data.get("video_id") or data.get("id")
    if not video_id:
        raise RuntimeError(resp.text[:800])
    (OUTPUT / "create_video_b.json").write_text(
        json.dumps(resp.json(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("[ok] video job", video_id)
    return video_id


def poll(video_id: str) -> dict:
    deadline = time.time() + 900
    while time.time() < deadline:
        resp = requests.get(f"{API}/v3/videos/{video_id}", headers=headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json().get("data") or {}
        print("[video]", data.get("status"), "duration", data.get("duration"))
        if data.get("status") in {"completed", "failed"}:
            (OUTPUT / "video_status_b.json").write_text(
                json.dumps(resp.json(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return data
        time.sleep(10)
    raise TimeoutError("timeout")


def download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(256 * 1024):
                if chunk:
                    f.write(chunk)
    print("[ok] saved", dest, dest.stat().st_size)


def burn_white_captions(video: Path, srt: Path, dest: Path) -> None:
    """Large white captions with soft black outline via ffmpeg ass/force_style."""
    # Escape path for ffmpeg filter (mac/linux)
    srt_esc = str(srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    # Fontsize ~22–24 is relative to ASS playres; for 1080p use Fontsize=22–28
    force = (
        "FontName=Arial,"
        "FontSize=18,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H80000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=80"
    )
    vf = f"subtitles={srt_esc}:force_style='{force}'"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-vf",
        vf,
        "-c:a",
        "copy",
        str(dest),
    ]
    print("[ffmpeg]", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("[ok] captions burned", dest, dest.stat().st_size)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not BG_PATH.exists():
        raise SystemExit(f"Missing background {BG_PATH}")

    bal0 = wallet()
    print("[wallet before]", bal0)
    if bal0 < 1.5:
        raise SystemExit(f"Balance too low: ${bal0}")

    # Guard: refuse if a create_video_b.json already in-progress from last 10 min
    lock = OUTPUT / "create_video_b.json"
    if lock.exists():
        try:
            prev = json.loads(lock.read_text(encoding="utf-8"))
            vid = (prev.get("data") or {}).get("video_id")
            if vid:
                st = requests.get(f"{API}/v3/videos/{vid}", headers=headers(), timeout=60)
                if st.status_code == 200:
                    status = (st.json().get("data") or {}).get("status")
                    if status in {"pending", "waiting", "processing"}:
                        raise SystemExit(f"Already rendering {vid} status={status} – not creating another")
        except SystemExit:
            raise
        except Exception:
            pass

    script = speech_b()
    print("[script B chars]", len(script))
    print(script[:200], "...")
    print("[look]", LOOK_ID, "[voice] Anya")

    bg_id = upload_asset(BG_PATH, "image/jpeg")
    video_id = create_video(LOOK_ID, script, bg_id)
    data = poll(video_id)
    if data.get("status") != "completed":
        print("[failed]", data.get("failure_code"), data.get("failure_message"))
        return 2

    clean = OUTPUT / "osipenko_feed_1x1_B_clean.mp4"
    final = OUTPUT / "osipenko_feed_1x1_B_captions.mp4"
    srt_path = OUTPUT / "osipenko_feed_1x1_B.srt"

    download(data["video_url"], clean)
    sub = data.get("subtitle_url")
    if not sub:
        print("[warn] no subtitle_url – saving clean only")
        print("[wallet after]", wallet())
        return 0
    download(sub, srt_path)

    # Ensure SRT is UTF-8 (ffmpeg likes BOM sometimes)
    raw = srt_path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8-sig", errors="replace")
    # strip ASS-like tags if any
    text = re.sub(r"<[^>]+>", "", text)
    srt_path.write_text(text, encoding="utf-8")

    burn_white_captions(clean, srt_path, final)
    bal1 = wallet()
    print("[wallet after]", bal1, "spent ~", round(bal0 - bal1, 2))
    print("[done]", final)
    print("[page]", data.get("video_page_url"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.HTTPError as exc:
        print("[http]", exc)
        if exc.response is not None:
            print(exc.response.text[:1200])
        raise SystemExit(1)
