# NEW Dataset: Pixel + Conversions API (MRS ad account)

Dataset для ad account `2649521998797481` (business 脸谱网).  
Старый pixel `1524169318700997` **не трогаем** на переходный период.

## Текущий NEW dataset

| | |
|---|---|
| Имя | `Kravira_MRS_CAPI` |
| Dataset / Pixel ID | **`1064023126171171`** |
| Ad account | `2649521998797481` |
| Business | `684085081667854` |
| Custom conversions | `MRS_Ph_Spec`, `MRS_Try_Spec` |

`.env`:

```env
META_DATASET_ID_MRS=1064023126171171
META_TEST_EVENT_CODE_MRS=          # код из Test Events, пока тестируем
```

CAPI с `META_ACCESS_TOKEN_MRS` проверен — события принимаются.

---

## Шаг 1. Events Manager — включить CAPI + Pixel

**UI не обязателен**, если CAPI уже шлёт события. Настройка выполняется скриптом:

```bash
python -m scripts.setup_mrs_capi_dataset --apply
python -m scripts.setup_mrs_capi_dataset --check
```

Скрипт через API:
- включает automatic advanced matching (`em`, `ph`, `fn`, `ln`, `ct`, `country`);
- отправляет bootstrap CAPI-события (`PageView`, `MRS_FB_onlineBooking`, `Test_F_*`, …);
- создаёт custom conversions и website-аудитории.

Если нужен именно UI: Events Manager → dataset → Settings → Conversions API →
**Conversions API and Meta Pixel** → включить **Event ID**.

Опционально: **Generate access token** в Settings dataset.  
Для репозитория достаточно `META_ACCESS_TOKEN_MRS` (System User `MRS_S_User`).

---

## Шаг 2. Домен

Business Settings → Brand safety → **Domains** → Add **`kravira.by`** → verify (DNS или meta-tag).

---

## Шаг 3. Карта событий (как на OLD pixel)

| Событие | Назначение |
|---|---|
| `PageView` | Стандарт |
| `MRS_FB_onlineBooking` | Запись онлайн — **главная** для ads |
| `Test_F_Ph` | Клик по телефону |
| `Test_F_try` | Попытка записи (Aibolit) |
| `Test_F_online` | Онлайн-запись |
| `MRS_FB_hr` | HR |
| `Test_F_Yackevich` | Страница врача |

---

## Шаг 4. GTM — dual pixel (переход 2–4 недели)

**Старый** (пока оставить): `1524169318700997`  
**Новый**: `1064023126171171`

### Base code (новый pixel)

```html
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '1064023126171171');
fbq('track', 'PageView');
</script>
```

### Custom event с дедупом (пример booking)

```javascript
function mrsEventId() {
  return 'mrs_' + Date.now() + '_' + Math.random().toString(36).slice(2);
}

function trackMrsBooking() {
  var eventId = mrsEventId();

  // Browser
  fbq('trackCustom', 'MRS_FB_onlineBooking', {}, { eventID: eventId });

  // Server (CAPI) — тот же eventId
  fetch('https://kravira.by/api/meta/capi', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event_name: 'MRS_FB_onlineBooking',
      event_id: eventId,
      event_source_url: location.href,
      fbp: getCookie('_fbp'),
      fbc: getCookie('_fbc')
    }),
    keepalive: true
  });
}
```

На бэкенде вызывать `send_web_event()` из `src/conversions/capi_web.py`.

---

## Шаг 5. Тест

1. Events Manager → **Test Events** → скопировать код → `META_TEST_EVENT_CODE_MRS=...`
2. Запуск:

```bash
python -m scripts.send_test_web_event
python -m scripts.send_test_web_event --event Test_F_Ph
```

3. В Test Events должны быть события **Browser** и **Server** с одним `event_id` (после GTM).

---

## Шаг 6. Custom conversions (уже созданы)

| ID | Имя | Правило |
|---|---|---|
| `1077660694742370` | MRS_Ph_Spec | `Test_F_Ph` + URL `kravira.by` |
| `2580723799055564` | MRS_Try_Spec | `Test_F_try` + URL `kravira.by` |

---

## Шаг 7. Ads (NEW account)

`promoted_object`:

```python
{
    "pixel_id": "1064023126171171",
    "custom_event_type": "OTHER",
    "custom_event_str": "MRS_FB_onlineBooking",
}
```

Website-аудитории (`MRS_Try_180_days` и др.) — после 3–7 дней накопления событий.

---

## Диагностика

| Проблема | Решение |
|---|---|
| CAPI 400 Invalid appsecret_proof | Для MRS использовать `capi_web.py` (HTTP), не SDK со старым APP_ID |
| Dataset Events Manager «Not receiving events» | Проверить GTM init ID + Test Events |
| Дубли в отчётах | Один `event_id` в fbq и CAPI |
| EMQ низкий | Передавать `fbp`, `fbc`, IP, UA |

---

## Когда убрать OLD pixel

Когда в NEW dataset:
- `MRS_FB_onlineBooking` стабильно >50–100/нед
- Diagnostics → Pixel + CAPI connected, dedup OK
- Ads в NEW account оптимизируются нормально

Тогда убрать `1524169318700997` из GTM.
