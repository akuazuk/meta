"""Проверка авторизации: диагностика токена + список рекламных аккаунтов.

Запуск:
    python -m scripts.verify_auth
"""

from __future__ import annotations

import sys

from facebook_business.adobjects.user import User
from facebook_business.exceptions import FacebookRequestError

from src.auth.token import debug_token, missing_scopes
from src.config import ConfigError, get_settings, init_api


def main() -> int:
    try:
        settings = get_settings()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2

    print("== Диагностика токена ==")
    try:
        info = debug_token()
        print(info.summary())
        gaps = missing_scopes(info)
        if gaps:
            print(f"[warn] не хватает прав: {', '.join(sorted(gaps))}")
        if not info.is_valid:
            print("[error] токен невалиден — дальше нет смысла.")
            return 1
    except Exception as exc:  # noqa: BLE001 - хотим показать любую ошибку сети/API
        print(f"[error] не удалось проверить токен: {exc}")
        return 1

    print("\n== Рекламные аккаунты (me/adaccounts) ==")
    init_api()
    try:
        me = User(fbid="me")
        accounts = me.get_ad_accounts(
            fields=["id", "name", "account_status", "currency", "timezone_name"]
        )
        found = False
        for acc in accounts:
            found = True
            print(
                f"- {acc.get('id')} | {acc.get('name')} | "
                f"status={acc.get('account_status')} | {acc.get('currency')} | "
                f"{acc.get('timezone_name')}"
            )
        if not found:
            print("(аккаунтов не найдено — проверьте доступы System User к рекламному аккаунту)")
    except FacebookRequestError as exc:
        print(f"[error] Graph API: {exc.api_error_message()} (code={exc.api_error_code()})")
        return 1

    if settings.ad_account_ref:
        print(f"\n[ok] Целевой рекламный аккаунт из .env: {settings.ad_account_ref}")
    else:
        print("\n[info] META_AD_ACCOUNT_ID не задан в .env.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
