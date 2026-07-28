"""Проверка блокеров, мешающих разместить объявления Кравиры.

Скрипт строго read-only: он читает данные и использует только
`validate_only`, поэтому ничего не создаёт и не изменяет в Meta. Его можно
запускать с любого компьютера, чтобы понять, сняты ли блокеры из
`docs/HANDOFF_BLOCKERS.md`.

Запуск:
    source .venv/bin/activate
    python -m scripts.diagnose_blockers
"""

from __future__ import annotations

import requests
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.exceptions import FacebookRequestError

from src.auth.token import debug_token, missing_scopes
from src.config import get_settings, init_api

# Meta возвращает этот subcode, когда приложение всё ещё в режиме разработки.
DEV_MODE_SUBCODE = 1885183

GRAPH = "https://graph.facebook.com/v23.0"


class Report:
    """Накапливает результаты проверок и считает блокеры."""

    def __init__(self) -> None:
        self.blocked = 0

    def ok(self, title: str, detail: str = "") -> None:
        print(f"[ok]      {title}{f' – {detail}' if detail else ''}")

    def blocker(self, title: str, detail: str, action: str) -> None:
        self.blocked += 1
        print(f"[BLOCKED] {title} – {detail}")
        print(f"          требуется: {action}")

    def warn(self, title: str, detail: str) -> None:
        print(f"[warn]    {title} – {detail}")


def check_token(report: Report) -> None:
    info = debug_token()
    if not info.is_valid:
        report.blocker(
            "Токен доступа",
            "Meta считает токен недействительным",
            "выпустить новый долгоживущий токен System User",
        )
        return
    gaps = missing_scopes(info)
    if gaps:
        report.blocker(
            "Разрешения токена",
            f"не хватает: {', '.join(sorted(gaps))}",
            "выдать недостающие разрешения System User в Business Manager",
        )
        return
    report.ok("Токен и разрешения", f"тип {info.type}, все нужные scopes на месте")


def check_app_mode(report: Report, account: AdAccount, page_id: str) -> None:
    """Единственный надёжный признак Live-режима – попытка валидации креатива."""
    probe = {
        "name": "blocker probe",
        "object_story_spec": {
            "page_id": page_id,
            "link_data": {
                "link": "https://kravira.by/",
                "message": "probe",
                "name": "probe",
            },
        },
        "execution_options": ["validate_only"],
    }
    try:
        account.create_ad_creative(params=probe)
    except FacebookRequestError as exc:
        if exc.api_error_subcode() == DEV_MODE_SUBCODE:
            report.blocker(
                "Режим приложения",
                f"приложение в режиме разработки (subcode {DEV_MODE_SUBCODE})",
                "перевести приложение в «Действующий» в панели разработчика",
            )
        else:
            error = (exc.body() or {}).get("error", {})
            report.blocker(
                "Создание оформления рекламы",
                error.get("error_user_msg") or exc.api_error_message(),
                "разобрать ошибку Meta перед созданием объявлений",
            )
        return
    report.ok("Режим приложения", "Meta принимает создание оформления рекламы")


def check_privacy_policy(report: Report) -> None:
    settings = get_settings()
    response = requests.get(
        f"{GRAPH}/{settings.app_id}",
        params={
            "fields": "privacy_policy_url",
            "access_token": f"{settings.app_id}|{settings.app_secret}",
        },
        timeout=30,
    )
    response.raise_for_status()
    url = response.json().get("privacy_policy_url")
    if url:
        report.ok("Политика конфиденциальности приложения", url)
        return
    report.blocker(
        "Политика конфиденциальности приложения",
        "поле пустое, Meta не переведёт приложение в Live",
        "указать ссылку на политику конфиденциальности kravira.by",
    )


def check_account(report: Report, account: AdAccount) -> None:
    data = account.api_get(
        fields=["name", "account_status", "currency", "spend_cap", "amount_spent"]
    )
    if int(data.get("account_status", 0)) != 1:
        report.blocker(
            "Рекламный аккаунт",
            f"статус {data.get('account_status')}",
            "восстановить активность аккаунта",
        )
    else:
        report.ok("Рекламный аккаунт", f"{data.get('name')}, активен")

    currency = data.get("currency")
    if currency != "PLN":
        report.warn("Валюта аккаунта", f"ожидали PLN, получили {currency}")

    cap = int(data.get("spend_cap") or 0)
    spent = int(data.get("amount_spent") or 0)
    if cap and cap - spent < 5000:
        report.blocker(
            "Лимит расходов аккаунта",
            f"остаток {(cap - spent) / 100:.2f} {currency} меньше дневного бюджета",
            "снять или поднять лимит расходов в настройках платежей",
        )
    else:
        report.ok("Лимит расходов аккаунта", "не мешает дневному бюджету 50 PLN")


def resolve_page(account: AdAccount) -> str:
    pages = list(account.get_promote_pages(fields=["id", "name"]))
    if len(pages) != 1:
        raise RuntimeError(f"Expected one promoted Page, found {len(pages)}")
    return pages[0]["id"]


def main() -> int:
    init_api()
    account = AdAccount(get_settings().ad_account_ref)
    page_id = resolve_page(account)

    report = Report()
    print("Проверка блокеров размещения объявлений (только чтение)\n")
    check_token(report)
    check_account(report, account)
    check_privacy_policy(report)
    check_app_mode(report, account, page_id)

    print()
    if report.blocked:
        print(f"Активных блокеров: {report.blocked}. Подробности и инструкции –")
        print("docs/HANDOFF_BLOCKERS.md")
        return 1
    print("Блокеров нет. Можно завершать размещение:")
    print("  python -m scripts.create_test_campaign --create")
    print("  python -m scripts.create_test_campaign --verify")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, requests.RequestException) as exc:
        print(f"[error] {exc}")
        raise SystemExit(1)
