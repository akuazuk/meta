# Google Ads creative images

Папка: `/Users/pavelkuzauka/Cursor_Folders/Meta/meta/image/google_ads/`

Стиль: славянские лица, teal-клиника, намёк на услугу, без логотипа и читаемого текста.

## Справки (важно: школа / абитуриент / детсад)

| Файл | Тема |
|------|------|
| `ads_spravki_school_1x1.png` | Школьница + мама + справка |
| `ads_spravki_school_boy_1x1.png` | Школьник + папа + справка |
| `ads_spravki_abiturent_1x1.png` | Абитуриентка + медосмотр |
| `ads_spravki_kindergarten_1x1.png` | Малыш + мама + справка в сад |
| `ads_spravki_1x1.png` | Общий (ранний) |

→ кампании: `MRS_Per_Max_Spravki`, `MRS Справки_wk`, `Справка для Абитуриента`

## Остальные направления (v1 + v2)

| Направление | Файлы | Кампании |
|-------------|-------|----------|
| Эндоскопия / ФГДС | `ads_endoscopy_fgds_1x1.png`, `ads_endoscopy_fgds_v2_1x1.png` | Эндоскопия_wk, ФГДС_Max |
| Колоноскопия | `ads_colonoscopy_1x1.png`, `ads_colonoscopy_v2_1x1.png` | Колоноскопия_wk |
| Гастроэнтеролог | `ads_gastroenterologist_1x1.png`, `ads_gastroenterologist_v2_1x1.png` | Гастроэнтеролог_wk |
| Гинекология | `ads_gynecology_1x1.png`, `ads_gynecology_v2_1x1.png` | Per_Max_Gynecolog |
| Урология | `ads_urology_1x1.png`, `ads_urology_v2_1x1.png` | Per_Max_Urolog |
| Флебология | `ads_phlebology_1x1.png`, `ads_phlebology_v2_1x1.png` | Per_Max_Flebolog |
| ЛОР | `ads_lor_1x1.png`, `ads_lor_v2_1x1.png` | Per_Max_Lor |
| Лазер | `ads_laser_1x1.png`, `ads_laser_v2_1x1.png` | Per_Max_Laser |
| Невролог | `ads_neurology_1x1.png`, `ads_neurology_v2_1x1.png` | Невролог_Per_Max |
| Эндокринолог | `ads_endocrinology_1x1.png`, `ads_endocrinology_v2_1x1.png` | Per_Max_Endokrinolog |
| Кардиолог | `ads_cardiology_1x1.png`, `ads_cardiology_v2_1x1.png` | Кардиолог_wk |
| Терапия | `ads_therapy_1x1.png`, `ads_therapy_v2_1x1.png` | Терапия_wk |
| Проктолог | `ads_proctology_1x1.png`, `ads_proctology_v2_1x1.png` | Проктолог_wk |
| Аллерголог | `ads_allergology_1x1.png`, `ads_allergology_v2_1x1.png` | Аллерголог_wk |
| УЗИ | `ads_ultrasound_1x1.png`, `ads_ultrasound_v2_1x1.png` | УЗИ_wk |
| Demand Gen / общий | `ads_demand_gen_clinic_1x1.png`, `ads_demand_gen_v2_1x1.png`, `ads_general_clinic_16x9.png` | Demand_Gen, Video |

Ранние endoscopy_happy_* — запасные.

## Загрузка в Google Ads (2026-08-05)
Скрипт: `scripts/upload_google_ads_images.py`

- **PMax:** square 1200×1200 + landscape 1200×628 → `SQUARE_MARKETING_IMAGE` / `MARKETING_IMAGE`
- **Search:** `AD_IMAGE` на ad groups по направлениям + общие на кампанию
- **Demand Gen (video):** картинки не вешались (видео-объявления)

Lor PMax был на лимите слотов — частично заменены stock; Search ЛОР получил картинки полностью.
