# Google Ads API – доступ агентства и продолжение с другого компьютера

Документ на **2 августа 2026**. Секреты в Git не хранятся – только `.env` на машине.

## 1. Статус доступов (проверено)

Аккаунт клиента в `.env`: `GOOGLE_ADS_CUSTOMER_ID` = Кравира (`7132108539`).

| Возможность | Статус |
| --- | --- |
| Чтение аккаунта / кампаний | OK |
| Редактирование (mutate validate_only) | OK |
| Создание бюджета + Search-кампании + группы + RSA | OK (`validate_only`) |
| MCC login | `GOOGLE_ADS_LOGIN_CUSTOMER_ID` |

Developer token – Basic Access. Для клиентов агентства через MCC этого достаточно.

Кода создания/редактирования в репозитории пока нет – только OAuth-скрипт и эта инструкция.
Следующий шаг на новой машине: проверить доступ, затем писать контур mutate.

## 2. Переменные `.env`

```env
# ==== Google Ads API (агентство → клиенты) ====
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=xxxxxx.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
# MCC агентства без дефисов
GOOGLE_ADS_LOGIN_CUSTOMER_ID=
# Клиентский аккаунт без дефисов (меняется по задаче)
GOOGLE_ADS_CUSTOMER_ID=
```

| Переменная | Где взять |
| --- | --- |
| `DEVELOPER_TOKEN` | MCC → Инструменты → API-центр |
| `CLIENT_ID` / `CLIENT_SECRET` | Google Cloud → APIs & Services → Credentials → OAuth Desktop |
| `REFRESH_TOKEN` | `python -m scripts.google_ads_oauth` (один раз) |
| `LOGIN_CUSTOMER_ID` | ID MCC без дефисов |
| `CUSTOMER_ID` | ID клиента без дефисов |

`CLIENT_ID` – это **не** номер аккаунта вида `713-210-8539`, а строка
`*.apps.googleusercontent.com`.

## 3. Старт с другого компьютера

```bash
git pull
cd meta   # если репозиторий лежит в meta/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Скопировать `.env` с рабочей машины **целиком** (Meta + Google), либо заполнить
по `.env.example` / `.env.template`.

```bash
chmod 600 .env
```

Проверка Google Ads:

```bash
python -m scripts.verify_google_ads
```

Если refresh token нет или протух / отозван:

```bash
python -m scripts.google_ads_oauth
# вставить GOOGLE_ADS_REFRESH_TOKEN=... в .env
python -m scripts.verify_google_ads
```

Проверка Meta (как раньше):

```bash
python -m scripts.diagnose_blockers
python -m scripts.create_test_campaign --verify
```

## 4. Правила безопасности для Google

- По умолчанию создавать объекты в статусе **PAUSED**.
- Сначала `validate_only`, потом реальный mutate – только по явной команде.
- Не коммитить `.env`, `client_secret_*.json`, refresh token.
- Для другого клиента менять только `GOOGLE_ADS_CUSTOMER_ID` (MCC/OAuth те же).
- Пользователь OAuth должен иметь на клиенте роль **Standard** или **Admin**.

## 5. Что делать завтра (логичный порядок)

1. `git pull` + venv + `pip install -r requirements.txt` + `.env`.
2. `python -m scripts.verify_google_ads` – убедиться, что доступ жив.
3. Дать задание: какую кампанию/объявления создать или изменить.
4. Реализовать контур `src/google_ads/` + скрипты list / create / update по брифу.

Связанные Meta-документы: [`ACTION_CHECKLIST.md`](ACTION_CHECKLIST.md),
[`AD_TASK_BRIEF.md`](AD_TASK_BRIEF.md), [`CAMPAIGN_PLAN.md`](CAMPAIGN_PLAN.md).
