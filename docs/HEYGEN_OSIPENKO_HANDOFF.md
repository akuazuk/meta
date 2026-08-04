# Handoff: HeyGen – Осипенко Дарья (продолжение завтра)

Для другого компьютера / другого агента Cursor. Репозиторий: `https://github.com/akuazuk/meta.git` (папка `meta/`).

## Быстрый старт на новом Mac

```bash
git clone https://github.com/akuazuk/meta.git
cd meta
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Вставить секреты из старого .env (НЕ коммитить .env)
```

Обязательные ключи в `.env` (скопировать со старого ПК):

- `HEYGEN_API_KEY`
- Meta / Google Ads ключи – если нужны смежные задачи

Проверка HeyGen:

```bash
source .venv/bin/activate
python - <<'PY'
import os, requests
from dotenv import load_dotenv
load_dotenv()
r = requests.get("https://api.heygen.com/v3/users/me",
                 headers={"X-Api-Key": os.environ["HEYGEN_API_KEY"].strip()}, timeout=30)
print(r.status_code, r.json()["data"]["wallet"])
PY
```

## Что уже сделано (статус на 2026-08-04)

| Пункт | Значение |
| --- | --- |
| Врач | Осипенко Дарья Петровна |
| Текст | `SPEECH.md` – утверждён **вариант B** для последнего ролика; A был раньше |
| Формат | **1:1**, без CTA / лого |
| Голос последнего ролика | **Anya** `37832e32d4f7475ab7a1cb0db8e5dd66` |
| Фон выбран | `input/backgrounds/cabinet_bg_b_cream.jpg` |
| Photo avatar look_id | `57f149749cb146f7bff7582309a58517` (группа `e1b4606d28294f26a85828168b565bae`) |
| Последнее видео | `fd5c1cbd24b34aee866ba6959c3ac12d` – https://app.heygen.com/videos/fd5c1cbd24b34aee866ba6959c3ac12d |
| Длительность / цена | ~26.5 сек, списано ~**$1.30** (баланс после: ~$4.30) |
| Субтитры | белые крупные – локально через ffmpeg (не стиль HeyGen) |

### Известная проблема

`remove_background` + картинка кабинета **почти не сработали** (белый халат/стена). В кадре фон cream виден узкой полоской. Варианты:

1. Оставить ролик как есть  
2. Перегенерация **без** `remove_background` (исходный белый кабинет с фото) ~$1.3  
3. Новый look с кабинетом в prompt – **+$1** аватар + ~$1.3 видео  

**Не создавать новый photo avatar** без явного `HEYGEN_FORCE_NEW_AVATAR=1` – раньше из‑за дублей ушло ~$14.

## Где лежат файлы

```text
heygen/osipenko_darya/
  BRIEF.md SPEECH.md README.md STATE.md
  input/source.jpg              ← фото для аватара
  input/backgrounds/            ← превью фонов A/B/C (в git)
  input/frames/                 ← кадры из IG-ролика
  scripts/generate_variant_b.py ← последний пайплайн B+Anya+cream
  scripts/generate_feed_video.py← старый (вариант A, reuse avatar)
  output/                       ← gitignored: MP4, SRT, json
```

### MP4 не в git

Скопировать вручную со старого ПК или скачать из HeyGen:

- `output/osipenko_feed_1x1_B_captions.mp4` – финал B с субтитрами  
- `output/osipenko_feed_1x1_B_clean.mp4` – без субтитров  
- `output/osipenko_feed_1x1_captions.mp4` – старый вариант A  

Сэмплы голосов были в `output/previews/voice_*.wav` (тоже gitignored) – при необходимости скачать снова из API `/v2/voices`.

## Правила для агента

1. Перед любой платной генерацией: проверить баланс, показать смету, дождаться «ок, запускай».  
2. Переиспользовать look_id из `STATE.md` / `output/avatar.json`.  
3. Один video job за раз; при обрыве сети – **poll существующий** `video_id`, не создавать второй.  
4. Субтитры «белые / крупнее»: SRT из API + `ffmpeg` `force_style` (см. `generate_variant_b.py`).  
5. `.env` и `*.mp4` не коммитить.

## Следующий логичный шаг

Согласовать с пользователем фикс фона (п. 1–3 выше) → одна генерация → показать кадр/MP4 → только потом commit при просьбе.
