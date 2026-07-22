"""Обмен короткоживущего user-токена на долгоживущий (~60 дней).

Запуск:
    python -m scripts.exchange_token <SHORT_LIVED_TOKEN>

Для боевой автоматизации предпочтительнее токен System User из Business
Manager (он не истекает), но этот скрипт удобен для быстрых локальных тестов.
"""

from __future__ import annotations

import sys

from src.auth.token import debug_token, exchange_for_long_lived
from src.config import ConfigError, get_settings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m scripts.exchange_token <SHORT_LIVED_TOKEN>")
        return 2
    try:
        get_settings()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2

    try:
        long_lived = exchange_for_long_lived(argv[1])
    except Exception as exc:  # noqa: BLE001
        print(f"[error] обмен не удался: {exc}")
        return 1

    print("Долгоживущий токен получен. Впишите его в .env как META_ACCESS_TOKEN:\n")
    print(long_lived)
    print("\n== Диагностика нового токена ==")
    try:
        print(debug_token(long_lived).summary())
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] не удалось продиагностировать: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
