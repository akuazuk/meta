"""Нормализация и SHA-256 хеширование PII для Advanced Matching.

ВАЖНО: официальный SDK facebook-business хеширует поля UserData
автоматически при отправке. Поэтому в capi.py мы передаём НЕхешированные
(но нормализованные) значения. Эти утилиты нужны, чтобы:
  * нормализовать данные единообразно (телефон в E.164-подобный вид и т.п.);
  * заранее посмотреть, какие match-ключи уйдут в Meta (для отладки EMQ);
  * при желании реализовать raw-HTTP отправку без SDK.

Не хешируйте значения дважды: либо SDK, либо вручную — не оба сразу.
"""

from __future__ import annotations

import hashlib
import re


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_phone(phone: str) -> str:
    """Оставляем только цифры (Meta ждёт цифры с кодом страны, без + и разделителей)."""
    return re.sub(r"\D", "", phone)


def normalize_name(name: str) -> str:
    return name.strip().lower()


def hash_email(email: str) -> str:
    return _sha256(normalize_email(email))


def hash_phone(phone: str) -> str:
    return _sha256(normalize_phone(phone))


def hash_name(name: str) -> str:
    return _sha256(normalize_name(name))


def preview_match_keys(
    *,
    email: str | None = None,
    phone: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> dict[str, str]:
    """Возвращает хеши match-ключей (для проверки, что именно уйдёт в Meta)."""
    keys: dict[str, str] = {}
    if email:
        keys["em"] = hash_email(email)
    if phone:
        keys["ph"] = hash_phone(phone)
    if first_name:
        keys["fn"] = hash_name(first_name)
    if last_name:
        keys["ln"] = hash_name(last_name)
    return keys
