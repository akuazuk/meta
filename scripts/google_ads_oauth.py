"""Получение GOOGLE_ADS_REFRESH_TOKEN через OAuth (Desktop app).

Запуск из корня проекта:

    source .venv/bin/activate
    pip install google-auth-oauthlib
    python -m scripts.google_ads_oauth

Скрипт откроет браузер. Войдите Google-аккаунтом агентства, у которого
есть доступ Standard/Admin к MCC и клиентским аккаунтам. После согласия
в терминал будет выведен refresh token – вставьте его в .env:

    GOOGLE_ADS_REFRESH_TOKEN=...
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPE = ["https://www.googleapis.com/auth/adwords"]


def main() -> int:
    client_id = (os.getenv("GOOGLE_ADS_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("GOOGLE_ADS_CLIENT_SECRET") or "").strip()
    if not client_id or not client_secret:
        print(
            "[error] Заполните GOOGLE_ADS_CLIENT_ID и GOOGLE_ADS_CLIENT_SECRET в .env"
        )
        return 1
    if not client_id.endswith(".apps.googleusercontent.com"):
        print(
            "[error] GOOGLE_ADS_CLIENT_ID должен быть OAuth Client ID "
            "(*.apps.googleusercontent.com), а не номер аккаунта Google Ads."
        )
        return 1

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    print("Откроется браузер. Войдите аккаунтом агентства и подтвердите доступ.")
    print("Если Google покажет предупреждение о тестовом приложении –")
    print("нажмите «Продолжить» / Advanced → Go to app.")
    print()

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPE)
    credentials = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
    )

    refresh = credentials.refresh_token
    if not refresh:
        print(
            "[error] Google не вернул refresh_token.\n"
            "Частая причина: доступ уже выдавался этому приложению раньше.\n"
            "Отзовите доступ: https://myaccount.google.com/permissions\n"
            "найдите ваше OAuth-приложение → Удалить доступ, затем запустите снова."
        )
        return 1

    print()
    print("=== Скопируйте в .env ===")
    print(f"GOOGLE_ADS_REFRESH_TOKEN={refresh}")
    print("=========================")
    print()
    print("После сохранения напишите ассистенту – проверим доступ к API.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[cancelled]")
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001 – показать пользователю текст Google
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(1)
