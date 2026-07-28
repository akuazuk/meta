# Meta Ads – интеграция (Marketing API + Conversions API)

Программное управление рекламным аккаунтом Meta и серверное отслеживание
конверсий для лид-генерации. Реализованы шаги 1–3 плана:

1. Доступы (System User + долгоживущий токен) – чек-лист ниже.
2. Каркас проекта + конфиг + проверка авторизации.
3. Отправка события `Lead` через Conversions API (Pixel + CAPI, дедуп, Test Events).

## Структура

```
src/
  config.py              # загрузка .env, init FacebookAdsApi
  auth/token.py          # обмен токена, /debug_token, проверка scopes
  conversions/
    hashing.py           # нормализация + SHA-256 PII (Advanced Matching)
    dedup.py             # общий event_id для дедупа Pixel <-> CAPI
    capi.py              # отправка Lead-события через Conversions API
scripts/
  verify_auth.py         # диагностика токена + список рекламных аккаунтов
  send_test_lead.py      # тестовое событие Lead в Test Events
  exchange_token.py      # short-lived -> long-lived токен
  build_ad_banners.py    # сборка финальных рекламных изображений
  create_test_campaign.py # проверка и создание PAUSED-кампании
  diagnose_blockers.py   # read-only проверка блокеров размещения
```

Подробный воспроизводимый процесс создания креативов и кампании:
[`docs/CREATIVE_CAMPAIGN_RUNBOOK.md`](docs/CREATIVE_CAMPAIGN_RUNBOOK.md).

## Продолжение работы с другого компьютера

Размещение объявлений сейчас заблокировано на стороне Meta: приложение
`Kravira_MRS` находится в режиме разработки. Кампания и группа объявлений уже
созданы и стоят на паузе.

Что именно мешает, какие ID уже созданы, что должен сделать администратор
вручную и готовый текст запроса агентству:
[`docs/HANDOFF_BLOCKERS.md`](docs/HANDOFF_BLOCKERS.md).

Проверить актуальный статус блокеров, ничего не меняя в Meta:

```bash
python -m scripts.diagnose_blockers
```

## Шаг 1. Доступы (делается в интерфейсах Meta)

- [ ] **Business Manager** (business.facebook.com) с доступом к бизнесу.
- [ ] **Рекламный аккаунт** привязан к Business Manager (`act_<ID>`).
- [ ] **App** на developers.facebook.com (тип Business) + продукт **Marketing API**.
- [ ] **System User** в настройках Business Manager (Users → System Users).
- [ ] **Assets**: назначить System User доступ к рекламному аккаунту, Pixel/Dataset и Странице.
- [ ] **Долгоживущий токен** System User с правами:
      `ads_management`, `ads_read`, `business_management`, `leads_retrieval`.
- [ ] Для боевого использования вне тестового аккаунта – пройти **App Review**.
- [ ] Создать **Dataset** в Events Manager, взять его ID для CAPI.
- [ ] (Опц.) Взять **Test Event Code** из вкладки Test Events.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # затем заполнить значения
```

## Запуск (из корня проекта)

Проверка авторизации и вывод рекламных аккаунтов:

```bash
python -m scripts.verify_auth
```

Тестовое событие Lead через CAPI (уйдёт в Test Events, если задан код):

```bash
python -m scripts.send_test_lead
```

Обмен короткоживущего токена на долгоживущий:

```bash
python -m scripts.exchange_token <SHORT_LIVED_TOKEN>
```

## Дедупликация Pixel <-> CAPI

Сервер и браузер шлют одно и то же событие с одинаковым `event_id`.
На фронте:

```js
const eventId = crypto.randomUUID().replace(/-/g, '');
fbq('track', 'Lead', {}, { eventID: eventId });
// eventId передать на бэкенд, чтобы CAPI отправил его же
```

На сервере тот же `eventId` кладётся в `LeadEvent(event_id=...)`.

## Дальше по плану

- Шаг 4: Conversion Leads Optimization – возврат стадий лида из CRM (`Qualified Lead`, `Converted Lead`) через `action_source=SYSTEM_GENERATED`.
- Шаг 5: Leadgen Webhook + выгрузка лидов из Instant Forms.
- Шаг 6: программное создание кампаний – реализован безопасный идемпотентный
  сценарий для Website Sales, создающий все объекты в `PAUSED`.
- Шаг 7: метрики через Insights API.
