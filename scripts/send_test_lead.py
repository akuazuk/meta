"""Отправка тестового события Lead через Conversions API.

Проверяет связку CAPI + Dataset. Если в .env задан META_TEST_EVENT_CODE,
событие появится во вкладке Test Events в Events Manager в реальном времени
и НЕ повлияет на оптимизацию.

Запуск:
    python -m scripts.send_test_lead
"""

from __future__ import annotations

import sys

from src.config import ConfigError, get_settings
from src.conversions.capi import CapiError, LeadContact, LeadEvent, RequestContext, send_lead
from src.conversions.dedup import new_event_id
from src.conversions.hashing import preview_match_keys


def main() -> int:
    try:
        get_settings()
    except ConfigError as exc:
        print(f"[config] {exc}")
        return 2

    event_id = new_event_id()
    contact = LeadContact(
        email="test.lead@example.com",
        phone="+1 555 010 2030",
        first_name="Test",
        last_name="Lead",
        country="us",
        external_id="crm-lead-000001",
    )
    context = RequestContext(
        client_ip_address="203.0.113.10",
        client_user_agent="Mozilla/5.0 (capi-test)",
        event_source_url="https://example.com/landing",
        fbp="fb.1.1700000000000.1234567890",
    )

    print("== Match-ключи, которые будут захешированы ==")
    for k, v in preview_match_keys(
        email=contact.email,
        phone=contact.phone,
        first_name=contact.first_name,
        last_name=contact.last_name,
    ).items():
        print(f"  {k} = {v}")
    print(f"\nevent_id (используйте тот же в браузерном Pixel для дедупа): {event_id}")

    lead = LeadEvent(contact=contact, context=context, event_id=event_id)

    try:
        result = send_lead(lead)
    except CapiError as exc:
        print(f"[config] {exc}")
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"[error] отправка не удалась: {exc}")
        return 1

    print("\n== Ответ Meta ==")
    for key, value in result.items():
        print(f"  {key}: {value}")
    if not result.get("test_event_code"):
        print("\n[info] META_TEST_EVENT_CODE не задан — событие ушло в боевой поток.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
