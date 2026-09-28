"""Классификация комментариев Кравиры: правила + Gemini (сарказм / намёк)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, replace

OWN_USERNAMES = {
    "kravira.by",
    "lor_yarovoy",
    "медицинский центр кравира",
}

INSULT = (
    "дебил", "идиот", "тварь", "мразь", "урод", "уродина", "дурак", "дура ",
    "сука", "бляд", "пидор", "пидр", "хуй", "херня", "говно", "гнид",
    "чмо", "сволоч", "кретин", "даун", "аутист", "уроды", "мразот",
    "лицо только", "только для лечения детей", "страшн", "лысый",
    "мешки под глаз", "залысин",
)

SCAM = (
    "развод", "разводят", "мошенник", "мошенниц", "кидалово", "кидалы",
    "обман", "обманщик", "лохотрон", "не ходите", "не ходи", "никому не советую",
    "никому не рекомендую", "закрывайте", "убегайте",
)

STRONG_NEG = (
    "ужасн", "кошмар", "отврат", "халтур", "антисанитар", "грязнющий",
    "убили", "покалечил", "изуродовал", "деньги выманил", "выманивают",
    "никогда больше", "больше ни ногой", "хуже некуда", "полный пиздец",
    "фу такое", "фуу",
)

COMPLAINT = (
    "не дозвон", "не дозвони", "не берут трубк", "нахамил", "нахамила",
    "грубиян", "грубая", "хамло", "хамка", "очередь часами", "прождал",
    "прождала", "развели на деньги", "выкачали деньги", "плохое отношение",
    "ужасный врач", "плохой врач", "врач плохой", "некомпетент",
)

SPAM = (
    "crypto", "bitcoin", "займ без", "переходи в тг", "подпишись",
    "зараб", "казино", "ставки на спорт", "onlyfans", "Escorts",
    "http://t.me", "https://t.me", "вайтлист", "nft",
)

POSITIVE = (
    "круто",
    "спасибо", "благодар", "хороший врач", "отличн", "супер", "рекоменду",
    "профессионал", "всё понятно", "все понятно", "доступно", "бережн",
    "лучшая клиник", "очень довол", "замечательн", "классик", "браво",
    "полностью соглас",
)

QUESTION_HINTS = (
    "?", "можно записаться", "как записаться", "сколько стоит", "входит ли",
    "входит в", "анастез", "анестез", "наркоз", "подскажите", "скажите пожалуйста",
    "а это больно", "нужно ли", "когда приём", "когда прием", "график",
)

MIXED = (
    "но врач", "дороговат", "долговато", "но спасибо", "хотя врач",
)

# Намёк / сарказм, который словари пропускают как «нейтраль».
SHADE = (
    "честный доктор", "честный врач", "прям по видео", "прямо по видео",
    "по лицу видно", "по роже", "сразу видно что", "сразу видно, что",
    "ну честный", "какой честный", "ага честный", "да уж честн",
    "не похож на врача", "врач как на подбор", "только для детей",
)


@dataclass(frozen=True)
class Verdict:
    rating: str
    score: int
    tone: str
    category: str
    markers: str
    should_delete: bool
    skip_own: bool
    should_hide: bool = False
    reason: str = ""
    source: str = "rules"


def _norm(text: str) -> str:
    t = (text or "").lower().replace("ё", "е")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _hits(text: str, words: tuple[str, ...]) -> list[str]:
    return [w.strip() for w in words if w.strip() and w.lower() in text]


def classify_rules(
    text: str,
    username: str | None = None,
    *,
    is_own_reply: bool = False,
    parent_text: str = "",
) -> Verdict:
    uname = (username or "").strip().lstrip("@").lower()
    if is_own_reply or uname in OWN_USERNAMES:
        return Verdict(
            rating="свой",
            score=5,
            tone="ответ клиники",
            category="свой аккаунт",
            markers="",
            should_delete=False,
            skip_own=True,
            source="rules",
        )

    raw = text or ""
    t = _norm(raw)
    parent = _norm(parent_text)
    blob = f"{t} {parent}".strip()
    if not t:
        return Verdict("нейтральный", 3, "пусто", "без текста", "", False, False)

    insult = _hits(t, INSULT)
    scam = _hits(t, SCAM)
    strong = _hits(t, STRONG_NEG)
    complaint = _hits(t, COMPLAINT)
    spam = _hits(t, SPAM)
    pos = _hits(t, POSITIVE)
    mixed = _hits(t, MIXED)
    shade = _hits(blob, SHADE)
    q = _hits(t, QUESTION_HINTS) or (["?"] if "?" in raw else [])

    markers = ", ".join(insult + scam + strong + complaint + spam + pos + mixed + shade + q[:3])

    if spam and not pos:
        return Verdict("спам", 1, "реклама / накрутка", "спам", markers, True, False, reason="спам")

    if insult:
        return Verdict(
            "оскорбление", 1, "оскорбление / насмешка", "оскорбление",
            markers, True, False, reason="оскорбление",
        )
    if scam or strong:
        return Verdict(
            "негатив", 1, "жёсткая жалоба / призыв не ходить", "атака на клинику",
            markers, True, False, reason="явный негатив",
        )
    if complaint and not pos:
        return Verdict(
            "негатив", 2, "жалоба на сервис или врача", "жалоба",
            markers, True, False, reason="жалоба",
        )

    if shade:
        return Verdict(
            "намёк", 2, "намёк / сарказм", "намёк на врача",
            markers, False, False, should_hide=True,
            reason="намёк или сарказм про врача/клинику",
        )

    if q and not insult and not scam and not strong:
        cat = "вопрос о записи" if any(x in t for x in ("запис", "стоит", "входит", "анестез", "анастез")) else "вопрос"
        return Verdict("вопрос", 3, "запрос информации", cat, markers, False, False)

    if pos and (complaint or mixed or strong):
        return Verdict("смешанный", 3, "смешанный отзыв", "смешанный", markers, False, False)
    if mixed and not pos:
        return Verdict("смешанный", 3, "оговорка / сомнение", "смешанный", markers, False, False)
    if pos:
        return Verdict("позитив", 5, "благодарность / хвала", "благодарность", markers, False, False)

    if re.fullmatch(r"[😂🤣😅]+", raw.replace(" ", "")):
        return Verdict("шутка", 3, "смех без текста", "реакция", "emoji", False, False)
    if re.fullmatch(r"[😈💩👎]+", raw.replace(" ", "")):
        return Verdict(
            "намёк", 2, "насмешка эмодзи", "насмешка", "emoji",
            False, False, should_hide=True, reason="насмешка эмодзи",
        )
    if re.fullmatch(r"[👍❤️❤💚👏🔥💯✨😊😁]+", raw.replace(" ", "")):
        return Verdict("позитив", 5, "реакция эмодзи", "реакция", "emoji", False, False)

    return Verdict("нейтральный", 3, "без оценки", "прочее", markers, False, False)


_SYSTEM = """Ты модератор комментариев медицинского центра «Кравира» (Беларусь).
Русский и белорусский, ирония, сарказм.

Оценка (одно слово):
- оскорбление — мат, «урод», насмешка над внешностью. score=1, action=delete
- негатив — «не ходите», мошенники, жёсткая жалоба. score=1, action=delete
- спам — реклама, ссылки. score=1, action=delete
- намёк — сарказм ИМЕННО про врача/клинику: нечестный, некомпетентный, «прям по видео скажешь я честный доктор)». score=2, action=hide
- смешанный — и плюс и минус про приём, без издёвки. score=3, action=keep
- нейтральный — факт, «+++», тег друга, без оценки врача. score=3, action=keep. НИКОГДА не hide и не delete.
- шутка — лёгкий смех не про честность/компетентность врача (про ИИ, про ролик, «а мне другое ответил😂»). score=3, action=keep
- вопрос — запись, цена, наркоз. score=3, action=keep
- позитив — хвала. score=5, action=keep
- свой — аккаунт клиники. score=5, action=keep

Не скрывай нейтраль и шутку «на всякий случай». Hide только если цель — репутация врача или клиники.
Верни JSON."""


def _gemini_json(prompt: str) -> dict | None:
    if os.getenv("COMMENT_USE_GEMINI", "1").strip() in ("0", "false", "no"):
        return None
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
    except Exception:
        return None
    try:
        creds, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not creds.valid:
            creds.refresh(Request())
        elif getattr(creds, "expired", False) and creds.refresh_token:
            creds.refresh(Request())
        if not creds.valid:
            creds.refresh(Request())
    except Exception:
        return None
    proj = os.getenv("GOOGLE_CLOUD_PROJECT") or project or "protocol-home-e1"
    loc = os.getenv("GEMINI_LOCATION", "europe-west1")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://aiplatform.googleapis.com/v1/projects/{proj}/locations/{loc}"
        f"/publishers/google/models/{model}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": _SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "rating": {"type": "STRING"},
                    "score": {"type": "INTEGER"},
                    "tone": {"type": "STRING"},
                    "category": {"type": "STRING"},
                    "markers": {"type": "STRING"},
                    "action": {"type": "STRING", "enum": ["keep", "hide", "delete"]},
                    "reason": {"type": "STRING"},
                },
                "required": ["rating", "score", "action", "reason"],
            },
        },
    }
    payload = json.dumps(body).encode("utf-8")
    data = None
    for attempt in range(2):
        if attempt and creds:
            try:
                creds.refresh(Request())
            except Exception:
                pass
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            err = e.read()[:400] if hasattr(e, "read") else str(e)
            print(f"gemini_http {e.code} {err}")
        except Exception as e:
            print(f"gemini_err {e}")
    if not data:
        return None
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception:
        return None


DELETE_RATINGS = {"оскорбление", "негатив", "спам"}
HIDE_RATINGS = {"намёк"}
KEEP_RATINGS = {"смешанный", "нейтральный", "шутка", "вопрос", "позитив", "свой"}
ALL_RATINGS = DELETE_RATINGS | HIDE_RATINGS | KEEP_RATINGS | {"средний"}


def apply_policy(verdict: Verdict) -> Verdict:
    """Оценка задаёт действие: нейтраль/шутка не скрываем."""
    rating = verdict.rating
    if rating == "средний":
        rating = "намёк" if verdict.should_hide else "смешанный"
    if rating not in ALL_RATINGS - {"средний"}:
        rating = "нейтральный"
    if rating in DELETE_RATINGS:
        return replace(verdict, rating=rating, should_delete=True, should_hide=False, score=min(verdict.score, 2) or 1)
    if rating in HIDE_RATINGS:
        return replace(verdict, rating=rating, should_delete=False, should_hide=True, score=2)
    score = verdict.score
    if rating == "позитив":
        score = max(score, 4)
    elif rating in ("нейтральный", "вопрос", "шутка", "смешанный"):
        score = 3 if score < 2 else min(score, 3) if rating != "смешанный" else 3
        if rating == "смешанный":
            score = 3
        if rating in ("нейтральный", "вопрос", "шутка"):
            score = 3
    return replace(verdict, rating=rating, should_delete=False, should_hide=False, score=score)


def _from_llm(data: dict, fallback: Verdict) -> Verdict:
    action = str(data.get("action") or "keep").strip().lower()
    if action not in ("keep", "hide", "delete"):
        action = "keep"
    rating = str(data.get("rating") or fallback.rating).strip().lower()
    allowed = ALL_RATINGS
    if rating not in allowed:
        rating = fallback.rating
    try:
        score = int(data.get("score") or fallback.score)
    except (TypeError, ValueError):
        score = fallback.score
    score = max(1, min(5, score))
    reason = str(data.get("reason") or "").strip()[:240]
    markers = str(data.get("markers") or fallback.markers).strip()
    if reason and reason not in markers:
        markers = f"{markers}; {reason}".strip("; ")
    return apply_policy(Verdict(
        rating=rating,
        score=score,
        tone=str(data.get("tone") or fallback.tone)[:80],
        category=str(data.get("category") or fallback.category)[:80],
        markers=markers[:240],
        should_delete=action == "delete",
        skip_own=False,
        should_hide=action == "hide",
        reason=reason,
        source="gemini",
    ))


def classify(
    text: str,
    username: str | None = None,
    *,
    is_own_reply: bool = False,
    parent_text: str = "",
    doctor: str = "",
    post_preview: str = "",
    use_llm: bool = True,
) -> Verdict:
    rules = classify_rules(text, username, is_own_reply=is_own_reply, parent_text=parent_text)
    if rules.skip_own:
        return rules
    if not use_llm:
        return apply_policy(rules)
    prompt = (
        f"Врач/тема: {doctor or '—'}\n"
        f"Пост: {(post_preview or '')[:240] or '—'}\n"
        f"Автор: @{username or '—'}\n"
        f"Родительский комментарий: {(parent_text or '')[:240] or '—'}\n"
        f"Комментарий: {text or '—'}\n"
    )
    data = _gemini_json(prompt)
    if not data:
        return apply_policy(replace(rules, source="rules-fallback"))
    llm = _from_llm(data, rules)
    # Явный токсик по правилам нельзя смягчить моделью до keep.
    if rules.should_delete and not llm.should_delete:
        return apply_policy(replace(rules, source="rules-override", reason=rules.reason or llm.reason))
    return apply_policy(llm)
