# Runbook: креативы и кампании Meta Ads для Кравиры

Этот документ описывает воспроизводимый процесс подготовки рекламных
изображений, проверки доступов и создания кампании по аналогии с текущей
кампанией Кравиры.

Главное правило безопасности: кампания, группа объявлений и объявления
создаются только в статусе `PAUSED`. Перевод в `ACTIVE` выполняется отдельным
действием после проверки в Ads Manager и отдельного подтверждения владельца.

## 1. Текущая эталонная кампания

### Кампания

| Параметр | Значение |
| --- | --- |
| Название | `Kravira \| Website Sales \| Minsk \| 2026-07 \| Test` |
| Buying type | `AUCTION` |
| Цель | `OUTCOME_SALES` |
| Специальные категории | Нет |
| Бюджет | На уровне группы объявлений |
| Статус | `PAUSED` |

### Группа объявлений

| Параметр | Значение |
| --- | --- |
| Название | `Minsk \| MRS_Try_180_days \| Online Booking \| 50 PLN` |
| Место конверсии | Website |
| Дневной бюджет | 50 PLN (`5000` в минимальных единицах API) |
| Billing event | `IMPRESSIONS` |
| Оптимизация | `OFFSITE_CONVERSIONS` |
| Bid strategy | `LOWEST_COST_WITHOUT_CAP` |
| Pixel/Dataset | `kravira_mrs_ads` |
| Pixel ID | `1524169318700997` |
| Событие | `MRS_FB_onlineBooking` |
| Custom event type | `OTHER` |
| Аудитория | `MRS_Try_180_days` |
| География | Минск, Беларусь |
| Meta city key | `283241` |
| Возраст | 18–65+ |
| Пол | Все |
| Языки | Без ограничения |
| Плейсменты | Автоматические Advantage+ |
| Атрибуция | 7 дней после клика, 1 день после просмотра |
| Dynamic Creative | Выключен |
| Статус | `PAUSED` |

Для произвольного события Pixel используется:

```python
promoted_object = {
    "pixel_id": "1524169318700997",
    "custom_event_type": "OTHER",
    "custom_event_str": "MRS_FB_onlineBooking",
}
```

Отдельная custom conversion для этой связки не обязательна. Перед запуском
нужно убедиться, что событие срабатывает именно на успешную запись, а не на
открытие или отправку промежуточной формы.

### Идентичность и ссылка

- Facebook Page: `Медицинский центр Кравира`.
- Instagram: `@kravira.by`.
- URL: `https://kravira.by/`.
- CTA: `LEARN_MORE`.
- UTM-метки не добавляются без отдельного согласования.
- Сайт ограничивает доступ по региону; целевой трафик кампании — Беларусь.

## 2. Структура файлов

```text
assets/fonts/                       # Montserrat
image/brand/sources/                # утверждённые исходники без foreground-лого
image/concepts/                     # три финальных JPEG 1080×1080
image/logo_circle.png               # официальный знак для watermark
scripts/build_ad_banners.py         # воспроизводимая сборка
scripts/create_test_campaign.py     # проверка и создание PAUSED-кампании
docs/AD_COPY.md                     # тексты объявлений и баннеров
docs/CAMPAIGN_PLAN.md               # краткий план кампании
```

В `image/concepts/` должны оставаться только актуальные финальные варианты:

```text
final_1_unique.jpg
final_2_health.jpg
final_3_hear.jpg
```

Черновики, старые варианты, cutout-файлы и изображения для проверки логотипа
не коммитятся.

## 3. Как создавать новые изображения

### 3.1. Визуальный стиль

Ориентир — кампании уролога Александра Баценко и гинеколога Дарьи Осипенко:

- мятный медицинский фон;
- лёгкое боке без визуального шума;
- врач крупно справа;
- рекламный текст слева;
- крупный нижний блок с телефоном `403`;
- один CTA в округлой бирюзовой плашке;
- высокая читаемость на мобильном устройстве;
- доверительная клиническая подача без запугивания.

### 3.2. Структура сообщения

Каждый баннер строится как:

```text
ТРИГГЕР → РЕШЕНИЕ → ДЕЙСТВИЕ
```

Примеры:

1. `Устали от формальных приёмов?`
   → `Здесь лечат вас, а не «средний случай»`
   → `Запишитесь онлайн`.
2. `Откладываете здоровье на потом?`
   → `25 лет помогаем вернуть главное`
   → `Выберите врача и запишитесь`.
3. `Вас действительно слышат?`
   → `Разберёмся вместе и найдём ваш путь к здоровью`
   → `Начните с консультации`.

Тексты должны быть короткими. На баннере не следует дублировать весь
Primary text объявления.

### 3.3. Правила бренда

- Шрифт: Montserrat.
- Заголовок: ExtraBold/Bold.
- Решение: Bold/SemiBold.
- CTA: SemiBold.
- Используется короткое тире `–` (U+2013), не длинное `—`.
- Нельзя генерировать логотип нейросетью.
- Официальный знак берётся из `image/logo_circle.png`.
- Знак размещается в свободной верхней области как полупрозрачный watermark.
- Watermark не должен перекрывать лицо врача, заголовок, CTA или номер `403`.
- Основной текст и телефон должны иметь достаточный контраст.

### 3.4. Рекомендуемый prompt для ImageGen

Перед генерацией укажите роли изображений:

- Image 1 — редактируемый макет или фотография врача;
- Image 2 — референс композиции Баценко/Осипенко;
- логотип не передаётся нейросети как элемент для перерисовки.

Шаблон:

```text
Use case: ads-marketing
Asset type: square Meta Ads banner, 1080x1080
Primary request: transform Image 1 into a direct-response medical ad using
the trigger → solution → action structure and the hierarchy of Image 2.
Input images: Image 1 = edit target; Image 2 = style reference only.
Composition: mint clinical background, subtle bokeh, doctor large on the
right, text on the left, stable bottom phone band. Do not create a logo.
Use three levels: trigger in dark teal, solution in white, action inside one
rounded teal button.
Text (verbatim, Cyrillic): "<ТРИГГЕР>"; "<РЕШЕНИЕ>"; "<ДЕЙСТВИЕ>"; "403".
Constraints: preserve the exact identity, face, hair, pose, uniform, hands and
jewelry of the doctor; exact Cyrillic text; safe margins; no foreground logo.
Avoid: altered face, invented person, deformed hands, misspelled Cyrillic,
watermark, fake logo, clutter, fearmongering and before/after imagery.
```

После генерации обязательно проверить каждое русское слово и лицо врача.
ImageGen может изменить буквы, кисти рук, украшения или детали формы даже при
строгом prompt.

### 3.5. Сборка финальных JPEG

Исходники кладутся в `image/brand/sources/`, после чего выполняется:

```bash
source .venv/bin/activate
python -m scripts.build_ad_banners
```

Скрипт:

1. приводит изображение к `1080×1080`;
2. добавляет официальный знак с прозрачностью 16%;
3. размещает знак в свободной верхней области;
4. сохраняет JPEG с качеством 95 без chroma subsampling.

### 3.6. QA изображений

Перед загрузкой проверить:

- размер ровно `1080×1080`;
- формат JPEG/RGB;
- врач не обрезан по лицу или рукам;
- лицо соответствует исходному врачу;
- все русские слова написаны правильно;
- только короткие тире;
- CTA читается на экране телефона;
- `403` и телефонная иконка видны;
- официальный watermark не перекрывает контент;
- отсутствуют чужие логотипы и watermark нейросети;
- старые версии удалены из `image/concepts/`.

## 4. Доступы и `.env`

Секреты хранятся только в `.env`, который исключён из Git.

```text
META_APP_ID=
META_APP_SECRET=
META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=
META_DATASET_ID=1524169318700997
META_TEST_EVENT_CODE=
META_GRAPH_API_VERSION=v25.0
```

Права файла:

```bash
chmod 600 .env
```

Для боевой отправки CAPI `META_TEST_EVENT_CODE` должен быть пустым.

Токен System User должен содержать:

```text
ads_management
ads_read
business_management
leads_retrieval
```

Приложение, выпустившее токен, должно находиться в `Live` mode. В Development
Mode Meta разрешает создать кампанию и группу, но блокирует создание Ad
Creative ошибкой `1885183`.

## 5. Проверка перед созданием

Установить зависимости и активировать окружение:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Базовая диагностика:

```bash
python -m scripts.verify_auth
```

Полная read-only проверка ресурсов и delivery estimate:

```bash
python -m scripts.create_test_campaign --check
```

Проверка должна подтвердить:

- валидный System User token;
- нужные scopes;
- рекламный аккаунт активен;
- валюта аккаунта — PLN;
- Page и Instagram доступны;
- Pixel ID совпадает;
- аудитория готова;
- geo key Минска принимается;
- Meta принимает `MRS_FB_onlineBooking` для `OFFSITE_CONVERSIONS`.

## 6. Создание кампании

Запускать только после явного подтверждения настроек:

```bash
python -m scripts.create_test_campaign --create
```

Скрипт идемпотентный:

- создаёт всё только в `PAUSED`;
- выполняет `validate_only` перед каждой сущностью;
- ищет кампанию и группу по точному имени;
- сохраняет созданные IDs и image hashes в
  `tmp_refs/campaign_create_state.json`;
- повторный запуск продолжает с места остановки;
- не создаёт повторно уже сохранённые объекты.

State-файл содержит только идентификаторы Meta и не коммитится.

Если Meta вернула ошибку после создания кампании или группы, нельзя начинать
процесс вручную с нуля. Нужно устранить причину и повторить ту же команду.

## 7. Проверка результата

После успешного создания:

```bash
python -m scripts.create_test_campaign --verify
```

Ожидаемый результат:

- кампания — `PAUSED`;
- группа — `PAUSED`;
- три объявления — `PAUSED`;
- бюджет — `5000` минимальных единиц, то есть 50 PLN;
- оптимизация — `OFFSITE_CONVERSIONS`;
- место конверсии — `WEBSITE`;
- событие — `MRS_FB_onlineBooking`;
- Dynamic Creative выключен;
- standard enhancements — `OPT_OUT`.

Затем вручную открыть Ads Manager и проверить preview всех плейсментов.

## 8. Активация

Скрипт намеренно не умеет активировать кампанию.

Перед активацией нужно отдельно подтвердить:

- корректность preview;
- доступность сайта из Беларуси;
- корректное срабатывание события после успешной записи;
- бюджет и дату запуска;
- отсутствие автоматических изменений изображений и текста.

Только после этого кампания, группа и объявления переводятся в `ACTIVE`
отдельной операцией.

## 9. Текущее состояние на 28 июля 2026

- Кампания создана в `PAUSED`.
- Группа объявлений создана в `PAUSED`.
- Загружено первое рекламное изображение.
- Креативы и объявления не созданы.
- Повторная проверка Meta возвращает `1885183`: используемое приложение всё
  ещё определяется как Development Mode.

После перевода правильного приложения — с App ID из `META_APP_ID` — в Live
нужно повторить:

```bash
python -m scripts.create_test_campaign --create
python -m scripts.create_test_campaign --verify
```
