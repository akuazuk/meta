# Google Ads — приоритеты 1–4 (2026-08-05)

## Baseline (до изменений)
Файл: [`docs/baselines/google_ads_baseline_BEFORE_2026-08-05_priorities.json`](baselines/google_ads_baseline_BEFORE_2026-08-05_priorities.json)

Срез: LAST_30_DAYS, все ENABLED-кампании, Search ad groups, PMax asset groups, настройки conversion actions.  
Сумма дневных бюджетов **до**: **$390**.

Как сравнить через 7–14 дней: выгрузить тот же срез скриптом/запросом и сравнить CPA, conv, cost, IS по `campaign.id` / `ad_group.id`.

Скрипт применения: `scripts/apply_priorities_2026_08_05.py`.

---

## P1 — без роста бюджета
| Действие | Результат |
|----------|-----------|
| Shared list `MRS_Search_Efficiency_2026-08` (15 phrase-минусов: нордин/лодэ, вакансии, учёба, «это»…) | Создан `12181664314`, **привязан к Search** |
| Минусы неврологу: ортопед, травматолог, ревматолог | OK |
| Пауза позитивов «гинеколог в Нордин/Лодэ» | OK |
| PMax Lor + Невролог: доп. H/D (strength был POOR) | OK |
| DISAPPROVED картинки PMax | **Не сняты** — нужны новые square/landscape из клиники (UI) |
| Gyn Video DISAPPROVED | Уже PAUSED |

## P2 — перекладка бюджета (сумма та же)
| Кампания | Было | Стало |
|----------|------|-------|
| Gynecology_Video_Conversions #2 | $10 | **$5** |
| MRS-Google_Search | $130 | **$135** |
| **Итого / день** | $390 | **$390** |

## P3 — структура Search
| Действие | Результат |
|----------|-----------|
| Группа `MRS УЗИ_wk` `196762490817` | Создана, RSA + ключи на реальные `/yzi/` страницы |
| В Кардиологе минусы `узи/ультразвук/эхокг…`, пауза явных УЗИ-ключей | OK |
| Часть УЗИ-ключей (молочные/вены/щитовидка/малый таз) | **Policy reject** — не добавлены |
| Гинеколог_wk: минусы «консультация / запись к гинекологу» → трафик в konsult-группу | OK |

## P4 — ценность конверсий
| Action | value | primary | include_in_conversions |
|--------|-------|---------|------------------------|
| GTM_click_tel | **5→2** | True | True |
| MRS_try_Aibolit | **10→25** | True | True |
| Test_MRS_Call_Back_Sent | **3→8** | True | True |
| MRS_onlineBooking | **3→20** | **True** | **True** |
| GTM_clicl_zapis | **3→15** | **True** | **True** |
| MRS_headerZapisButton | **3→12** | **True** | **True** |

---

## Ожидаемый эффект
- Меньше слива на конкурентов/чужие специальности  
- УЗИ с релевантным LP вместо «кардиолог»  
- +$5/день Search за счёт Video  
- tROAS сильнее тянет Aibolit/запись относительно клика по телефону  

## Не сделано / блокер
1. Замена DISAPPROVED изображений во всех PMax (LIMITED останется, пока нет ассетов).  
2. УЗИ-ключи с policy (молочные железы / часть анатомических) — не форсировать.
