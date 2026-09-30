# Инструкции для агента (Кравира / Meta)

Репозиторий: [github.com/akuazuk/meta](https://github.com/akuazuk/meta).
Локально это папка `Cursor_Folders/Meta/meta`. Git только здесь.
Домашний репозиторий `/Users/pavelkuzauka` не трогать и в него не коммитить.

Секреты в Git не класть. Значения токенов – только на машине, см. [§ Ключи](#ключи-доступа).

## Что это

Программное управление рекламой **Meta (аккаунт MRS / USD)** и **Google Ads**,
плюс CAPI, креативы, GTM и видео. Клиент – ОДО «Медицинский центр «Кравира»»,
сайт `kravira.by`.

Рабочий рекламный аккаунт для новых задач: **MRS** `act_2649521998797481`.
Старый PLN-аккаунт `act_723170300839405` – только чтение / история, не мешать
с MRS без явной просьбы.

## Старт

```bash
cd /Users/pavelkuzauka/Cursor_Folders/Meta/meta
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# .env уже должен лежать локально (не из Git). Иначе скопировать с рабочей машины
# или заполнить по .env.example
chmod 600 .env
python -m scripts.verify_auth          # Meta
python -m scripts.verify_google_ads    # Google Ads
```

Скрипты запускать из корня репозитория: `python -m scripts.<имя>`.

Cursor MCP Meta Ads: `scripts/run_meta_ads_mcp.sh` (берёт `META_ACCESS_TOKEN_MRS` из `.env`).

## Жёсткие правила

- Тексты объявлений, титры, речь в кадре – **только русский**. CTA в API – enum
  (`LEARN_MORE`), в кабинете Meta сам покажет «Подробнее».
- Вакансии: `locales: [17]` (русский), `advantage_audience: 0`.
- Новые объекты создавать **PAUSED**. В ACTIVE – только после явной команды.
- **HeyGen не генерировать** (дорого на подписке). Читать аккаунт можно.
- **Higgsfield:** сначала баланс и смета (`higgsfield account status`,
  `higgsfield generate cost`), генерация только после «да / генерируй / ок трать».
  CLI: `export PATH="$HOME/.local/bin:$PATH"`. MCP баланса ненадёжен.
- Тире в копирайте – короткое `–` (U+2013).
- Не коммитить `.env`, `tmp_refs/`, токены, `.mp4` / `.mov` / `.wav`.

Подробности: `.cursor/rules/` (`creatives-russian`, `kravira-ad-creatives`,
`heygen-credits`, `higgsfield-credits`, `bacenko-video`).

## Аккаунты и ID (не секреты)

| Что | ID / значение |
| --- | --- |
| MRS ad account | `act_2649521998797481` |
| MRS pixel / dataset | `1064023126171171` (`Kravira_MRS_CAPI`) |
| OLD pixel (не трогать без нужды) | `1524169318700997` |
| OLD ad account | `act_723170300839405` |
| Meta App | `Kravira_MRS` `1045577707887803` |
| Кампания «Вакансии» | `120247828518660434` (`OUTCOME_LEADS`) |
| GTM контейнер | `GTM-59QGB4V` (аккаунт `6104203271`, контейнер `118976342`) |
| Google Ads клиент Кравира | `7132108539` |
| Google Ads MCC | `4529863027` |
| Сайт вакансий | `https://kravira.by/o-companii/vacancy/` |

## Вакансии (актуально 30.09.2026)

Оптимизация рабочих групп: пиксель `1064023126171171` + событие **`MRS_FB_hr`**.

```json
{"pixel_id":"1064023126171171","custom_event_type":"OTHER","custom_event_str":"MRS_FB_hr"}
```

Не ставить `custom_conversion_id` вместе с pixel+event – Meta отклоняет комбинацию.
Без `pixel_id` + имени события в Ads Manager поле «Событие» выглядит пустым.

| Группа | ID | Статус |
| --- | --- | --- |
| Ортопеды | `120248358357910434` | ACTIVE |
| Администраторы | `120248358379870434` | PAUSED |
| Стоматологи | `120248358386490434` | PAUSED |
| Кардиологи | `120248358393630434` | PAUSED |
| Кардиологи база HR | `120248358404720434` | PAUSED |
| ЛОР | `120248358414600434` | PAUSED |
| Эндокринологи | `120248358421690434` | PAUSED |
| Терапевты | `120248358427620434` | PAUSED |
| Медсёстры | `120248358434530434` | PAUSED |

Архив со старыми кастомными конверсиями (`— старая конверсия` / `— старая цель`)
не включать.

Скрипт ортопедов: `scripts/create_ortho_vacancy.py`. Креативы:
`image/concepts/ortho_job/`.

### События HR – что реально доходит

| Имя | Доходит в пиксель | Комментарий |
| --- | --- | --- |
| `MRS_FB_hr` | да | Рабочее. GTM тег `MRS_ FB_hr`, `fbq('track','MRS_FB_hr')`. Шире одной кнопки: клик «Отправить резюме» + звонок HR + отправка формы. |
| `MRS_FB_hr_click` | нет | Тег GTM 181 на том же триггере «Отправить резюме». Preview зелёный, Events Manager пустой. Пробовали `track` и `trackCustom` (контейнер v252). Не использовать в оптимизации, пока `/stats` не покажет fires. |
| Кастом «Отправить резюме» `2491849758003783` | да | Правило: `MRS_FB_hr` + URL `/o-companii/vacancy`. |
| `MRS_HR_Click` `1112676098080897` | нет | Правило на `MRS_FB_hr_click`, last_fired пустой. |

Главное событие для медицинских кампаний (не вакансии): `MRS_FB_onlineBooking`.

## GTM

Контейнер `GTM-59QGB4V`. Триггер `MRS_click_Resume` (112): Click Text содержит
«Отправить резюме». На нём висят старый `MRS_ FB_hr` и новый `MRS_FB_hr_click`.
Публикация – из кабинета GTM под Google-аккаунтом владельца. REST GTM из этого
репо не настроен.

## Ключи доступа

Секреты **не в Git**. На другой машине копируют файлы ниже или проходят OAuth заново.

### 1. Главный файл – `meta/.env`

Путь: `/Users/pavelkuzauka/Cursor_Folders/Meta/meta/.env`  
Права: `600`. Шаблон без значений: `.env.example`.

| Переменная | Зачем |
| --- | --- |
| `META_APP_ID` / `META_APP_SECRET` | приложение `Kravira_MRS` |
| `META_ACCESS_TOKEN` | запасной / по умолчанию |
| `META_ACCESS_TOKEN_MRS` | **боевой** System User MRS, Ads + CAPI |
| `META_AD_ACCOUNT_ID_MRS` | `2649521998797481` |
| `META_DATASET_ID_MRS` | пиксель `1064023126171171` |
| `META_ACCESS_TOKEN_OLD` / `META_AD_ACCOUNT_ID_OLD` / `META_DATASET_ID` | старый PLN-аккаунт |
| `META_PAGE_ID` / `META_INSTAGRAM_ID` | страница и IG |
| `META_GRAPH_API_VERSION` | сейчас `v25.0` |
| `META_TEST_EVENT_CODE*` | пусто = прод, не тест |
| `GOOGLE_ADS_CLIENT_ID` / `CLIENT_SECRET` / `REFRESH_TOKEN` | Google Ads API |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | MCC |
| `GOOGLE_ADS_CUSTOMER_ID` | клиент (Кравира) |
| `HEYGEN_API_KEY` | только чтение HeyGen, генерацию не запускать |

Откуда брать заново:

- Meta: Business Manager → System Users → токен (`ads_management`, `ads_read`,
  `business_management`). MRS: пользователь `MRS_S_User`.
- Google Ads: `docs/GOOGLE_ADS_SETUP.md`, скрипт `python -m scripts.google_ads_oauth`.
- HeyGen: app.heygen.com → Settings → API.

### 2. Cursor MCP – `~/.cursor/mcp.json`

Не содержит самих токенов Meta. Список серверов:

| Сервер | Как логинится |
| --- | --- |
| `meta-ads` | `meta/scripts/run_meta_ads_mcp.sh` → читает `.env` → `META_ACCESS_TOKEN_MRS` |
| `higgsfield` | OAuth Cursor на `https://mcp.higgsfield.ai/mcp` |
| `heygen` | OAuth Cursor на `https://mcp.heygen.com/mcp/v1/` |
| `artlist` | OAuth Cursor на `https://mcp.artlist.io/mcp` |
| `google-sheets` / `google-docs` / `google-business` | скрипты в `~/.config/google-workspace-mcp/` |

Плагины Gmail / Calendar / Drive – отдельный OAuth Cursor (не в `.env`).

### 3. Higgsfield CLI (кредиты и генерация)

| Файл | Путь |
| --- | --- |
| Бинарь | `~/.local/bin/higgsfield` |
| Токен CLI | `~/.config/higgsfield/credentials.json` |
| Workspace | `~/.config/higgsfield/config.json` |

MCP Higgsfield для баланса не использовать как источник правды.

### 4. Google Workspace MCP

Каталог: `~/.config/google-workspace-mcp/`

- `oauth-desktop.json` – OAuth-клиент
- `sheets-token.json` – Sheets
- `gbp-token.json` – Google Business Profile
- `run-sheets.sh` / `run-docs.sh` / `run-gbp.sh`

### 5. Прочие локальные токены (gitignore)

| Файл | Зачем |
| --- | --- |
| `meta/.youtube_token.json` | загрузка YouTube |
| `meta/.google_ads_credentials.json` | запасной формат Google Ads |
| `google-ads.yaml` | не использовать, если есть `.env` |
| `client_secret_*.json` | Google Cloud OAuth client |

`tmp_refs/` – рабочие JSON скриптов, тоже не в Git.

### 6. Чего нет в файлах

- GTM и Google Tag Manager – вход в браузере (аккаунт владельца контейнера).
- Кабинет Meta Ads / Events Manager – тот же Business Manager, что выдал System User.
- Cookie / сессия браузера агента не являются постоянными ключами.

## Куда смотреть в доках

| Тема | Файл |
| --- | --- |
| Бриф на объявление | `docs/AD_TASK_BRIEF.md` |
| CAPI / события MRS | `docs/META_CAPI_NEW_DATASET.md` |
| Google Ads доступ | `docs/GOOGLE_ADS_SETUP.md` |
| Креативы Meta | `docs/CREATIVE_CAMPAIGN_RUNBOOK.md` |
| HeyGen (без генерации) | `docs/HEYGEN_OSIPENKO_HANDOFF.md` |
| Баценко видео | `.cursor/rules/bacenko-video.mdc` |

## Типичные команды

```bash
python -m scripts.diagnose_blockers
python -m scripts.setup_mrs_capi_dataset --check
higgsfield account status --json
```

Graph API (токен из `.env`, не печатать): пиксель
`/{PIXEL_ID}/stats?aggregation=event`, кастомные конверсии
`/{act}/customconversions?fields=id,name,last_fired_time,rule`.
