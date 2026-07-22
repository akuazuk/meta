"""Отправка серверных событий через Conversions API (CAPI).

Здесь реализовано событие Lead (и его down-funnel стадии для CLO).
PII передаётся НЕхешированной — SDK хеширует сам при отправке.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from facebook_business.adobjects.serverside.action_source import ActionSource
from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.event_request import EventRequest
from facebook_business.adobjects.serverside.user_data import UserData

from src.config import get_settings, init_api
from src.conversions.dedup import new_event_id


class CapiError(RuntimeError):
    pass


@dataclass
class LeadContact:
    """Контакт лида. Всё опционально, но чем больше match-ключей — тем выше EMQ."""

    email: str | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip_code: str | None = None
    # Стабильный ID лида из вашей CRM. Нужен для связки стадий в CLO.
    external_id: str | None = None


@dataclass
class RequestContext:
    """Данные запроса пользователя (нужны для качественной атрибуции)."""

    client_ip_address: str | None = None
    client_user_agent: str | None = None
    fbc: str | None = None  # cookie _fbc / из fbclid
    fbp: str | None = None  # cookie _fbp
    event_source_url: str | None = None


@dataclass
class LeadEvent:
    contact: LeadContact
    context: RequestContext = field(default_factory=RequestContext)
    # Имя события: Lead / Qualified Lead / Converted Lead (для CLO — down-funnel).
    event_name: str = "Lead"
    # Общий с браузером event_id для дедупликации.
    event_id: str | None = None
    event_time: int | None = None
    # website — лид с сайта; system_generated — из CRM/webhook.
    action_source: ActionSource = ActionSource.WEBSITE
    # Ценность лида (для оптимизации по стоимости/ROAS), опционально.
    value: float | None = None
    currency: str | None = None
    lead_id: str | None = None  # leadgen_id для Instant Forms (CRM-события)


def _build_user_data(contact: LeadContact, context: RequestContext) -> UserData:
    return UserData(
        emails=[contact.email] if contact.email else None,
        phones=[contact.phone] if contact.phone else None,
        first_name=contact.first_name,
        last_name=contact.last_name,
        city=contact.city,
        state=contact.state,
        country_code=contact.country,
        zip_code=contact.zip_code,
        external_id=contact.external_id,
        client_ip_address=context.client_ip_address,
        client_user_agent=context.client_user_agent,
        fbc=context.fbc,
        fbp=context.fbp,
    )


def _build_custom_data(lead: LeadEvent) -> CustomData | None:
    if lead.value is None and lead.currency is None and lead.lead_id is None:
        return None
    return CustomData(
        value=lead.value,
        currency=lead.currency,
        lead_event_source="CRM" if lead.action_source == ActionSource.SYSTEM_GENERATED else None,
    )


def build_event(lead: LeadEvent) -> Event:
    return Event(
        event_name=lead.event_name,
        event_time=lead.event_time or int(time.time()),
        event_id=lead.event_id or new_event_id(),
        action_source=lead.action_source,
        event_source_url=lead.context.event_source_url,
        user_data=_build_user_data(lead.contact, lead.context),
        custom_data=_build_custom_data(lead),
    )


def send_lead(lead: LeadEvent) -> dict:
    """Отправляет одно lead-событие через CAPI. Возвращает ответ Meta как dict."""
    return send_events([build_event(lead)])


def send_events(events: list[Event]) -> dict:
    """Отправляет батч серверных событий в Dataset."""
    settings = get_settings()
    if not settings.dataset_id:
        raise CapiError("Не задан META_DATASET_ID — некуда отправлять события CAPI.")
    init_api()

    request = EventRequest(
        events=events,
        pixel_id=settings.dataset_id,
        test_event_code=settings.test_event_code or None,
    )
    response = request.execute()
    # EventResponse -> сериализуем в понятный dict
    return {
        "events_received": getattr(response, "events_received", None),
        "messages": getattr(response, "messages", None),
        "fbtrace_id": getattr(response, "fbtrace_id", None),
        "test_event_code": settings.test_event_code or None,
    }
