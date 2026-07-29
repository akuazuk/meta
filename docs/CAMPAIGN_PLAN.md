# План тестовой кампании Meta Ads

## Текущий статус (29 июля 2026, вечер)

| Объект | ID | Статус |
| --- | --- | --- |
| Кампания | `120250238338830770` | `ACTIVE` |
| Группа | `120250238339070770` | `ACTIVE`, 50 PLN/день |
| Ad 01 Individual approach | `120250257575060770` | `ACTIVE` |
| Ad 02 Health first | `120250257576040770` | `ACTIVE` |
| Ad 03 We hear everyone | `120250257576710770` | `ACTIVE` |

Приложение Live. `spend_cap` аккаунта поднят (~2850 PLN), блокеров размещения нет.
Тестовая кампания уже крутится и тратит бюджет.

### Preview объявлений

| Объявление | Preview |
| --- | --- |
| 01 Individual approach | https://fb.me/21zeWr951rqXyPt |
| 02 Health first | https://fb.me/2bDSxgkLnSkd5Yu |
| 03 We hear everyone | https://fb.me/yvkCAFXnfR0LPMR |

### Доставка (lifetime на 29.07, API Insights)

| Метрика | Значение |
| --- | --- |
| Показы | ~8 665 |
| Охват | ~5 700+ по сумме ads |
| Клики | 44 (link clicks ~28) |
| Landing page views | 10 |
| Расход кампании | ~24 PLN |
| Custom pixel conversions | 2 (`offsite_conversion.fb_pixel_custom`) |
| Именованная custom conversion | 1 × `MRS_Ph_Spec` (телефонный Test_F_Ph) |

Оптимизация группы – custom event `MRS_FB_onlineBooking`. В Insights пока явно
видно общее custom pixel и `MRS_Ph_Spec`; отдельно сверить `MRS_FB_onlineBooking`
во вкладке Events Manager / Test Events при записи онлайн.

### Что дальше

- Новые объявления / кампании – только по брифу [`AD_TASK_BRIEF.md`](AD_TASK_BRIEF.md), создавать в `PAUSED`.
- Не дублировать эту тестовую структуру без нужды.
- История блокеров: [`HANDOFF_BLOCKERS.md`](HANDOFF_BLOCKERS.md).

```bash
python -m scripts.diagnose_blockers
python -m scripts.create_test_campaign --verify
```

## Безопасный режим

- Кампания, группа объявлений и все объявления создаются в статусе `PAUSED`.
- Ничего не переводить в `ACTIVE` без отдельного подтверждения.
- Валюта рекламного аккаунта – польский злотый (`PLN`).
- Дневной бюджет – **50 PLN** на уровне группы объявлений.

## Кампания

- Цель: продажи / конверсии на сайте (`OUTCOME_SALES`).
- Сайт: `https://kravira.by/`.
- Стратегия: максимальное количество конверсий.
- Название: `Kravira | Website Sales | Minsk | 2026-07 | Test`.

## Группа объявлений

- Название: `Minsk | MRS_Try_180_days | Online Booking | 50 PLN`.
- Место конверсии: сайт.
- Pixel/Dataset: `kravira_mrs_ads` (`1524169318700997`).
- Конверсия: custom event `MRS_FB_onlineBooking` с типом `OTHER`.
- Аудитория: `MRS_Try_180_days`.
- География: Минск.
- Плейсменты: автоматические Advantage+.
- Бюджет: 50 PLN в день.
- Возраст и пол: без дополнительного сужения, если перед созданием не согласовано иное.

## Объявления

Три отдельных объявления:

| # | Имя | Файл | Creative ID |
| --- | --- | --- | --- |
| 1 | `01 \| Individual approach` | `image/concepts/final_1_unique.jpg` | `1531174861277327` |
| 2 | `02 \| Health first` | `image/concepts/final_2_health.jpg` | `1339921248353269` |
| 3 | `03 \| We hear everyone` | `image/concepts/final_3_hear.jpg` | `1579654607143218` |

- Тексты: соответствующие варианты из `docs/AD_COPY.md`.
- CTA: `LEARN_MORE`.
- Ссылка: `https://kravira.by/`.
- Advantage+ creative features – индивидуально `OPT_OUT`.
- UTM-метки не добавлять до отдельного согласования.

## Проверки перед созданием

- Доступность Facebook Page и Instagram-аккаунта для рекламного аккаунта.
- Доступность Pixel/Dataset и конверсии `MRS_FB_onlineBooking`.
- Доступность аудитории `MRS_Try_180_days`.
- Корректность валюты аккаунта – PLN.
- Политика недискриминации принята для System User в BM Kravira.
- После создания проверить структуру и параметры через API, оставив всё на паузе.

## Как подготовлены изображения

Финальные баннеры воспроизводимо собираются командой:

```bash
source .venv/bin/activate
python -m scripts.build_ad_banners
```

Процесс:

1. Берутся утверждённые исходники из `image/brand/sources/`.
2. Каждый баннер использует структуру «триггер → решение → действие».
3. Композиция нормализуется до `1080×1080`.
4. Официальный знак из `image/logo_circle.png` добавляется в свободную верхнюю
   область как полупрозрачный элемент фона.
5. Знак не перекрывает врача, рекламный текст или номер `403`.
6. Финальные изображения сохраняются в JPEG с высоким качеством.

Подробный runbook:
[`CREATIVE_CAMPAIGN_RUNBOOK.md`](CREATIVE_CAMPAIGN_RUNBOOK.md).
