# Как давать задание на создание объявлений

Шаблон для задач агенту. Чем точнее бриф, тем меньше уточнений и ошибок.
Если поле не заполнено – агент использует **значения по умолчанию** из
[`CAMPAIGN_PLAN.md`](CAMPAIGN_PLAN.md) и правила `.cursor/rules/kravira-ad-creatives.mdc`.

## Обязательные правила безопасности

- Создавать только в `PAUSED`.
- Не переводить в `ACTIVE` без явной фразы: «активируй» / «запусти показы».
- Не менять spend_cap / биллинг без запроса.
- Перед `--create`: `python -m scripts.diagnose_blockers`.
- Тире в текстах только короткое `–` (U+2013).
- Шрифт баннеров: Montserrat. Логотип не рисовать нейросетью.

## Шаблон брифа (скопировать и заполнить)

```text
### Задача
[ ] Новая кампания + группа + объявления
[ ] Добавить объявления в существующую группу
[ ] Только креативы/баннеры (без Meta)
[ ] Только тексты (AD_COPY)
[ ] Проверить / починить / verify

### Кампания
Название:
Цель: OUTCOME_SALES (по умолчанию)
Сайт / URL: https://kravira.by/
Статус: PAUSED

### Группа объявлений
Название:
Дневной бюджет (PLN): 50
Гео: Минск
Возраст / пол: без сужения (или указать)
Аудитория: MRS_Try_180_days (или новая / lookalike / interest – описать)
Плейсменты: Advantage+ (или только IG / FB / Audience Network)
Оптимизация: MRS_FB_onlineBooking
Pixel: 1524169318700997
UTM: нет (или указать метки)

### Объявления (по одному блоку на креатив)
1) Имя:
   Файл изображения: image/concepts/...
   Primary text:
   Headline:
   Description:
   CTA: LEARN_MORE

2) ...

### Стиль баннера (если нужна сборка)
Эталон: final_*.jpg (мятный фон, врач справа, текст слева, 403, teal CTA)
Триггер → решение → действие:
Логотип: logo_circle watermark 16%
Формат: 1080×1080

### Запреты / особое
Не включать Advantage+ creative auto-enhancements
Не дублировать на баннере весь Primary text
Другое:
```

## Значения по умолчанию (если в брифе пусто)

| Параметр | По умолчанию |
| --- | --- |
| Аккаунт | `AMX_RB_kravira.by` (`act_723170300839405`) |
| BM для своего System User | `Kravira` (`756364310076502`) |
| Владелец ad account | `Artox Media RB` (агентство) |
| Page | `265643990153763` |
| Instagram | `17841404399569974` (`@kravira.by`) |
| Цель | `OUTCOME_SALES` |
| Бюджет | 50 PLN / день на группе |
| Гео | Минск |
| Аудитория | `MRS_Try_180_days` |
| Событие | `MRS_FB_onlineBooking` |
| CTA | `LEARN_MORE` |
| URL | `https://kravira.by/` |
| Креативы тестовой серии | `final_1_unique`, `final_2_health`, `final_3_hear` |
| Тексты | [`AD_COPY.md`](AD_COPY.md) варианты A/B/C |
| Улучшения креатива | все индивидуально `OPT_OUT` |

## Что агент делает по брифу

1. Сверяет бриф с дефолтами и правилами стиля.
2. При необходимости собирает баннеры: `python -m scripts.build_ad_banners`.
3. `python -m scripts.diagnose_blockers`.
4. Создаёт/досоздаёт через `python -m scripts.create_test_campaign --create`
   (или расширяет скрипт под новый бриф, если дефолтный план не подходит).
5. `python -m scripts.create_test_campaign --verify`.
6. Отдаёт ID объектов. Активирует только по явной команде пользователя.

Тестовая серия `final_1/2/3` уже в Meta в статусе `ACTIVE` (см. `CAMPAIGN_PLAN.md`).
Не пересоздавать её без запроса. Новые креативы – отдельные имена и `PAUSED`.

## Частые блокеры

| Симптом | Что делать |
| --- | --- |
| `1885183` | приложение не Live |
| `2859024` | политика недискриминации для System User в BM **Kravira** |
| `3858504` | не использовать `standard_enhancements`, только individual OPT_OUT |
| spend_cap слишком низкий | попросить агентство поднять лимит (тестовый аккаунт уже ~2850 PLN) |
| Page/IG недоступны | выдать ассеты System User в BM |

Подробности: [`HANDOFF_BLOCKERS.md`](HANDOFF_BLOCKERS.md), runbook
[`CREATIVE_CAMPAIGN_RUNBOOK.md`](CREATIVE_CAMPAIGN_RUNBOOK.md).

## Пример короткого задания

```text
Добавь в тестовую группу ещё одно объявление.
Картинка: image/concepts/final_2_health.jpg
Текст B из AD_COPY.md
CTA LEARN_MORE, URL https://kravira.by/
Всё в PAUSED, не активировать.
```
