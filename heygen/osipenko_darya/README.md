# HeyGen: Осипенко Дарья Петровна (гинеколог)

Короткие ролики врача для Instagram / Facebook (лента **1:1**).

**Продолжение на другом ПК:** см. [`docs/HEYGEN_OSIPENKO_HANDOFF.md`](../../docs/HEYGEN_OSIPENKO_HANDOFF.md) и `STATE.md`.

## Структура

```text
heygen/osipenko_darya/
  BRIEF.md SPEECH.md README.md STATE.md
  input/source.jpg
  input/backgrounds/     ← фоны A/B/C для превью и замены
  input/frames/
  scripts/
    generate_feed_video.py   # вариант A, reuse avatar
    generate_variant_b.py    # B + Anya + cream + ffmpeg субтитры
  output/                    # gitignored: mp4/srt/json
```

## Статус (2026-08-04)

- Текст: варианты A/B/C в `SPEECH.md`; последний рендер – **B**.
- Аватар: look `57f149749cb146f7bff7582309a58517` (не плодить новые).
- Голос последнего ролика: **Anya**.
- Фон cream через API маскировался плохо – см. handoff.
- Субтитры: белые крупные через ffmpeg после SRT.

## Запуск (только после «ок» пользователя)

```bash
cd meta && source .venv/bin/activate
# баланс + один job:
python -m heygen.osipenko_darya.scripts.generate_variant_b
```

Нужны: `HEYGEN_API_KEY` в `.env`, ffmpeg в PATH.
