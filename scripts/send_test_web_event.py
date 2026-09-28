"""Тест Conversions API для NEW dataset (MRS ad account).

Отправляет MRS_FB_onlineBooking в Test Events, если задан META_TEST_EVENT_CODE_MRS.

Запуск:
    python -m scripts.send_test_web_event
    python -m scripts.send_test_web_event --event Test_F_Ph
"""

from __future__ import annotations

import argparse
import sys

from src.config import ConfigError, get_mrs_settings
from src.conversions.capi_web import CapiWebError, WebEvent, WebEventContext, send_web_event
from src.conversions.dedup import new_event_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--event",
        default="MRS_FB_onlineBooking",
        help="имя custom event (по умолчанию MRS_FB_onlineBooking)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        settings = get_mrs_settings()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2

    event_id = new_event_id()
    print(f"dataset_id: {settings.dataset_id}")
    print(f"event_name: {args.event}")
    print(f"event_id (тот же передайте в fbq для дедупа): {event_id}")
    if settings.test_event_code:
        print(f"test_event_code: {settings.test_event_code}")
    else:
        print("[warn] META_TEST_EVENT_CODE_MRS не задан — событие уйдёт в боевой поток")

    event = WebEvent(
        event_name=args.event,
        event_id=event_id,
        context=WebEventContext(
            client_ip_address="203.0.113.10",
            client_user_agent="Mozilla/5.0 (capi-web-test)",
            event_source_url="https://kravira.by/",
            fbp="fb.1.1700000000000.1234567890",
        ),
    )

    try:
        result = send_web_event(event)
    except CapiWebError as exc:
        print(f"[error] {exc}")
        return 1

    print("\n== Ответ Meta ==")
    for key, value in result.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
