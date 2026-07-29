"""Нагон вызовов Marketing API для требования App Review (500+).

Только чтение. Ничего не создаёт и не меняет.

Запуск:
    python -m scripts.burn_marketing_api_calls
    python -m scripts.burn_marketing_api_calls --count 550
"""

from __future__ import annotations

import argparse
import sys
import time

import requests

from src.config import ConfigError, get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=550, help="сколько успешных вызовов нужно")
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="пауза между успешными вызовами, сек (по умолчанию 1s, чтобы не словить rate limit)",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="стоп при стольких ошибках подряд (не портим success rate)",
    )
    args = parser.parse_args()

    try:
        settings = get_settings()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2

    if not settings.ad_account_ref:
        print("[error] META_AD_ACCOUNT_ID не задан")
        return 2

    version = settings.graph_api_version or "v25.0"
    base = f"https://graph.facebook.com/{version}"
    token = settings.access_token
    act = settings.ad_account_ref

    # Чередуем несколько read-only Marketing API endpoint'ов.
    endpoints = [
        f"{base}/{act}",
        f"{base}/{act}/campaigns",
        f"{base}/{act}/adsets",
        f"{base}/{act}/ads",
        f"{base}/me/adaccounts",
    ]
    params_variants = [
        {"access_token": token, "fields": "id,name,account_status,currency", "limit": 1},
        {"access_token": token, "fields": "id,name,status", "limit": 1},
        {"access_token": token, "fields": "id,name,status", "limit": 1},
        {"access_token": token, "fields": "id,name,status", "limit": 1},
        {"access_token": token, "fields": "id,name", "limit": 5},
    ]

    ok = 0
    err = 0
    streak_err = 0
    attempt = 0
    started = time.time()
    backoff = 60.0

    print(f"Цель: {args.count} успешных вызовов Marketing API ({act})")
    print("При rate limit ждём с backoff и не спамим ошибками (нужен success ≥85%).")
    while ok < args.count:
        idx = attempt % len(endpoints)
        url = endpoints[idx]
        params = params_variants[idx]
        attempt += 1
        try:
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json() if resp.content else {}
            api_err = data.get("error") if isinstance(data, dict) else None
            if resp.status_code == 200 and not api_err:
                ok += 1
                streak_err = 0
                backoff = 60.0
                if ok % 25 == 0 or ok == args.count:
                    elapsed = time.time() - started
                    print(f"[ok] {ok}/{args.count}  errors={err}  elapsed={elapsed:.0f}s")
                time.sleep(args.sleep)
            else:
                err += 1
                streak_err += 1
                body = resp.text[:200]
                code = (api_err or {}).get("code") if isinstance(api_err, dict) else None
                if resp.status_code == 429 or code in (4, 17, 32, 613) or "rate" in body.lower() or "request limit" in body.lower():
                    print(f"[rate-limit] пауза {backoff:.0f}s (ok={ok} err={err})")
                    time.sleep(backoff)
                    backoff = min(backoff * 1.5, 900.0)
                    # Не считаем повтор после ожидания как «streak» для аварийного стопа.
                    streak_err = 0
                else:
                    print(f"[fail] HTTP {resp.status_code}: {body}")
                    time.sleep(2)
                    if streak_err >= args.max_errors:
                        print("[error] слишком много ошибок подряд — останавливаюсь")
                        return 1
        except requests.RequestException as exc:
            err += 1
            streak_err += 1
            print(f"[fail] network: {exc}")
            time.sleep(5)
            if streak_err >= args.max_errors:
                print("[error] слишком много сетевых ошибок — останавливаюсь")
                return 1

    elapsed = time.time() - started
    rate = (ok / (ok + err) * 100) if (ok + err) else 0
    print(f"\nГотово: ok={ok} err={err} success_rate={rate:.1f}% за {elapsed:.0f}s")
    print("Счётчик в App Review может обновиться с задержкой до 24 часов.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
