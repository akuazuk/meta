"""Conversions API для веб-событий (NEW dataset / MRS ad account).

Отправка custom events с дедупликацией Pixel + CAPI через общий event_id.
Использует META_ACCESS_TOKEN_MRS и META_DATASET_ID_MRS (не OLD profile).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from src.config import ConfigError, get_mrs_settings
from src.conversions.dedup import new_event_id

_GRAPH = "https://graph.facebook.com"


class CapiWebError(RuntimeError):
    pass


@dataclass
class WebEventContext:
    client_ip_address: str | None = None
    client_user_agent: str | None = None
    fbc: str | None = None
    fbp: str | None = None
    event_source_url: str | None = None
    email: str | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    external_id: str | None = None


@dataclass
class WebEvent:
    event_name: str
    context: WebEventContext = field(default_factory=WebEventContext)
    event_id: str | None = None
    event_time: int | None = None
    custom_data: dict | None = None


def _base_url(version: str | None) -> str:
    return f"{_GRAPH}/{version}" if version else _GRAPH


def _user_data(ctx: WebEventContext) -> dict:
    data: dict = {}
    if ctx.client_ip_address:
        data["client_ip_address"] = ctx.client_ip_address
    if ctx.client_user_agent:
        data["client_user_agent"] = ctx.client_user_agent
    if ctx.fbc:
        data["fbc"] = ctx.fbc
    if ctx.fbp:
        data["fbp"] = ctx.fbp
    if ctx.email:
        data["em"] = ctx.email
    if ctx.phone:
        data["ph"] = ctx.phone
    if ctx.first_name:
        data["fn"] = ctx.first_name
    if ctx.last_name:
        data["ln"] = ctx.last_name
    if ctx.external_id:
        data["external_id"] = ctx.external_id
    return data


def build_payload(event: WebEvent) -> dict:
    payload: dict = {
        "event_name": event.event_name,
        "event_time": event.event_time or int(time.time()),
        "event_id": event.event_id or new_event_id(),
        "action_source": "website",
        "user_data": _user_data(event.context),
    }
    if event.context.event_source_url:
        payload["event_source_url"] = event.context.event_source_url
    if event.custom_data:
        payload["custom_data"] = event.custom_data
    return payload


def send_web_event(event: WebEvent) -> dict:
    """Отправляет одно веб-событие в NEW dataset через CAPI."""
    return send_web_events([event])


def send_web_events(events: list[WebEvent]) -> dict:
    settings = get_mrs_settings()
    if not settings.dataset_id:
        raise CapiWebError("Не задан META_DATASET_ID_MRS.")

    body: dict = {"data": [build_payload(event) for event in events]}
    if settings.test_event_code:
        body["test_event_code"] = settings.test_event_code

    response = requests.post(
        f"{_base_url(settings.graph_api_version)}/{settings.dataset_id}/events",
        params={"access_token": settings.access_token},
        json=body,
        timeout=30,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise CapiWebError(f"Meta вернула не-JSON: {response.text[:400]}") from exc

    if response.status_code != 200:
        err = payload.get("error", {})
        raise CapiWebError(
            err.get("error_user_msg") or err.get("message") or str(payload)
        )
    return payload
