# Сценарий Reels v21 — «Уролог не стучится»

Версия для предсказуемого производства через Artlist. Визуально ролик выглядит как один непрерывный дубль, но собирается из коротких генераций со скрытыми стыками. Это обязательное условие качества, а не творческая опция.

Исходники:

- лицо: `out/ref_face.jpg` и `out/ref_face2.jpg`;
- голосовой референс Баценко: `out/doctor_voice_ref.wav` или исходная запись `Баценко 1.MOV`;
- `out/drive_v20_15s.wav` использовать только как архивный референс тембра — текст и тайминг в нём устарели;
- новый мастер после утверждения озвучки сохранить как `out/drive_v21_15s.wav`, а 8-секундный фрагмент для lip-sync — как `out/drive_v21_dialogue_ref_8s.wav`;
- утверждённый образ: `out/start_still_v20.jpg` — только как референс внешности и костюма, не как первый кадр ролика.

---

## Главная задача

Собери один вертикальный ролик 15 секунд, 9:16, для Reels/TikTok.

Результат должен восприниматься как единый пролёт камеры:

1. бёрнаут;
2. взгляд изнутри витрины;
3. пролом безопасного стекла;
4. осколки полностью закрывают кадр;
5. из осколков открывается тот же мужчина, уже остановившийся без шлема;
6. он спокойно произносит панч в камеру.

Не пытайся получить всё одной 15-секундной генерацией. Создай четыре клипа и спрячь монтаж в дыме, motion blur и полноэкранных осколках. Если среда не умеет монтировать, верни четыре принятых клипа, ключевые кадры и монтажную карту — не выдавай один сырой реролл за готовый ролик.

Никакой рекламы: без логотипа, названия клиники, телефона, бейджа и призыва записаться.

Это постановочный кинотрюк с закалённым бутафорским стеклом. Магазин закрыт и пуст. Никого нет внутри. Без крови, травм и пострадавших.

---

## Неподвижные параметры continuity

Они одинаковы во всех ключевых кадрах и клипах:

- один и тот же Александр Баценко с приложенных фото;
- сохраняются форма глаз, носа, губ, челюсти, линия роста волос и возрастная узнаваемость;
- допускается только деликатная ретушь: свежая кожа и мягче тени под глазами; не превращать его в другого или слишком молодого мужчину;
- белый медицинский халат, светло-голубая рубашка, тёмно-синий галстук;
- без петлички, ручки в кармане, бейджа и логотипа;
- тёмный chrome cafe-racer с круглой фарой и нечитаемым номером;
- яркий солнечный день, мягкий ключ спереди-слева и заполнение лица;
- один и тот же пустой стеклянный фасад без букв и вывесок;
- направление движения мотоцикла и света не меняется между планами.

Шлем находится на голове только в клипах A и B. После полноэкранного облака осколков клип C начинается с уже снятым шлемом. Не генерировать снятие шлема в кадре: это частая причина деформации лица, рук и головы.

---

## Голос, новый текст и интонация

Старую конструкцию «если что-то беспокоит» не использовать: сочетание коротких служебных слов провоцирует запинку и делает финальную фразу монотонной.

Новый текст — точно эти слова, без добавлений:

> Это не скорая по простате.  
> Это я.  
> Что-то беспокоит внизу?  
> Не гоняй по форумам.  
> Заедь нормально.

Интонационная партитура:

1. «Это **не СКО-рая** по простате» — спокойно, сухо, с лёгкой иронией; ударение **СКО-рая**, как в «скорая помощь».
2. «Это я» — коротко, увереннее и чуть тише; после фразы осмысленная пауза.
3. «Что-то беспокоит внизу?» — живой внимательный вопрос без колебания и без запинки; слова «что-то» произнести слитно и легко.
4. «**Не гоняй** по форумам» — доброжелательно, но твёрдо; смысловое ударение на «не гоняй».
5. «Заедь нормально» — теплее, чуть медленнее и ниже по тону, с улыбкой в голосе; это финальный панч.

Не читать как рекламный диктор и не переигрывать. Нужна дуга: сухая шутка → узнавание → заботливый вопрос → твёрдый совет → тёплый панч.

Целевая длина чистой речи с паузами — 6.3–6.8 секунды. Если получилось длиннее 7.0 секунды, сделать новый дубль с более собранными паузами; не ускорять и не растягивать готовый голос программно.

После утверждения озвучки собрать `out/drive_v21_15s.wav`:

- речь ориентировочно начинается около 7.1 секунды;
- после последнего слова оставить не менее 0.8 секунды полной тишины;
- точные границы определить по фактическому waveform, а не назначать заранее.

Финальная голосовая дорожка — утверждённый мастер WAV, а не речь, заново придуманная видеомоделью. Аудиореференс нужен модели только для движения губ. После генерации удалить её голос и вернуть мастер WAV без изменения скорости.

---

## Производственный порядок

1. Сначала утвердить мастер-кадр лица без шлема для диалога.
2. Утвердить новую озвучку и измерить её реальные границы речи.
3. Затем получить и принять клип D с речью. Это главный кадр ролика.
4. После него делать клипы C, B и A — в таком порядке.
5. Каждый следующий стартовый кадр строить из принятого кадра предыдущего клипа или из общего мастер-референса.
6. На каждом этапе проверять только критерии данного клипа. Не рероллить хороший диалог из-за неудачного экшена.

Рекомендуемая модель: Seedance 2.5 I2V 1080p с image/audio reference. Для клипа D допустим Kling v3 Pro I2V Audio 1080p, если он лучше сохраняет лицо и русский lip-sync. Сначала делать один тест, а не пачку дорогих рероллов.

---

## Ключевые кадры

Нужно создать и утвердить четыре отдельных вертикальных кадра. Во всех использовать оба фото лица и один мастер-референс костюма.

### KF-D — диалог, главный референс

Первым создаётся именно этот кадр.

```text
Photoreal cinematic vertical 9:16 DAYLIGHT portrait of the EXACT same Alexander Batsenko as both face references. Preserve his real identity, facial proportions, eyes, nose, lips, jaw and hairline. Subtle healthy grooming only: rested skin and softly filled under-eye shadows; do not make him a different or much younger man.

He is seated naturally astride the same dark chrome cafe-racer, motorcycle fully stopped. No helmet on his head; no helmet near his face. Medium shot from chest height, head, shoulders, chest, white lab coat, navy tie and handlebar all visible. He looks directly into the lens with a restrained knowing half-smile, mouth fully closed.

Bright sunny city street, soft frontal-left daylight and warm fill under the eyes. Behind him is the same empty storefront with shattered safety-glass fragments low on the floor, no people. Clean commercial realism, natural skin texture, stable symmetrical hands on the handlebar.

No lavalier microphone, no badge, no pen, no logo, no text, no signage, no readable license plate, no watermark. No harsh eye shadows, no beauty-plastic face, no extreme close-up.
```

Принять только если лицо узнаваемо без пояснений, обе руки анатомичны, петлички нет, рот закрыт, кадр достаточно широкий для титров.

### KF-A — бёрнаут

Низкий широкий план. Шлем надет, гоглы подняты. Заднее колесо и зона будущего дыма видимы. Переднее колесо чистое. Не использовать KF-D как первый кадр этого клипа.

### KF-B — взгляд изнутри витрины

Камера внутри пустого помещения и смотрит наружу через целый лист стекла. Мотоцикл с водителем в шлеме снаружи, по центру траектории. Дневной свет и направление движения совпадают с KF-A.

### KF-C — после осколков

Полноэкранные осколки и белый дым начинают расходиться. За ними виден уже остановившийся мотоцикл и тот же мужчина без шлема в среднем плане. KF-C должен композиционно переходить в KF-D.

---

## Монтажная карта и промпты клипов

Генерировать клипы длиннее нужного участка и выбирать стабильный фрагмент. Ни один генеративный таймкод не считать точным до просмотра результата.

| Финал | Клип | Что происходит | Скрытый стык |
|---|---|---|---|
| 0.000–2.200 | A | бёрнаут с заднего колеса | белый дым закрывает 70–100% кадра |
| 2.200–5.250 | B | вид изнутри, разгон и полный пролом стекла | осколки закрывают 100% кадра |
| 5.250–старт речи | C | осколки расходятся, байк уже остановлен, взгляд в камеру | мягкий match cut в тот же средний план |
| старт речи–15.000 | D | речь и финальная улыбка | нет |

### Клип A — 4 секунды, в монтаж 0.0–2.2

```text
Vertical 9:16 photoreal daylight action shot. Low wide camera beside the clean FRONT wheel of the same dark chrome cafe-racer. The helmeted doctor in the white lab coat performs a controlled stationary burnout. The REAR tire spins; dense white smoke comes only from the rear tire and trails behind the motorcycle. The front tire remains clean and rolls neither upward nor sideways. The bike stays on both wheels. Camera glides toward the expanding smoke until bright white smoke naturally fills the frame. No speech, mouth closed, no stunt tricks, no wheelie, no people, no text.
```

### Клип B — 5 секунд, в монтаж 2.2–5.25

```text
Vertical 9:16 photoreal daylight controlled film stunt, viewed from INSIDE an empty closed storefront looking OUT through one large tempered prop-glass pane. The same helmeted doctor on the same cafe-racer accelerates straight toward camera. At impact, the front wheel passes through and the ENTIRE pane disintegrates into thousands of small sparkling safety-glass pieces. The sheet does not remain standing and does not merely crack. Sunlit fragments and white smoke rush toward camera until they fully occlude the lens. No blood, no injury, no people, no speech, no jump or wheelie, no readable text.
```

Сделать событие простым: один разгон, один удар, один полный разлёт. Не просить одновременно проезд камеры с улицы внутрь — переход внутрь уже скрыт дымом между A и B.

### Клип C — 4 секунды, в монтаж 5.25–до фактического старта речи

```text
Vertical 9:16 photoreal daylight continuation beginning with sparkling safety-glass fragments and white smoke completely covering the lens. The particles clear to reveal the SAME Alexander Batsenko, exact identity from the face references, already safely stopped astride the same motorcycle INSIDE the empty storefront. His helmet is already off and out of frame. Medium shot at chest height: head, shoulders, chest, white coat, navy tie and handlebar visible. He settles his posture, keeps his mouth fully closed and looks into the lens with a restrained knowing half-smile. Soft even daylight fills both eyes. Camera eases into the exact composition of KF-D and becomes still. No speech, no hand near face, no lavalier, no extra person, no text.
```

### Клип D — 8 секунд, в монтаж примерно 7.0–15.0

После утверждения нового голоса вырезать из `out/drive_v21_15s.wav` точный участок 7.000–15.000 и сохранить его как `out/drive_v21_dialogue_ref_8s.wav`. В начале аудиореференса должно остаться примерно 0.1 секунды тишины перед первой фонемой. Стартовый кадр — утверждённый KF-D.

```text
Vertical 9:16 photoreal locked medium shot based on the approved start image. Preserve the EXACT man's identity, age, hairline, facial structure, clothes, motorcycle, background and daylight for the entire shot. He remains seated and nearly still, looking directly into the lens. Natural micro-movements only: breathing, one subtle blink and a restrained half-smile.

Use the attached Russian audio only as the lip-motion timing reference. Begin with the mouth fully closed during the short initial silence. Then produce accurate, restrained Russian lip sync for the attached speech without changing his face, teeth or jaw. When speech ends, close the mouth completely and hold eye contact through the final frame.

Locked camera, medium framing throughout: head, shoulders, chest, white coat and handlebar remain visible. No push-in, no crop, no head turn, no hand gesture, no microphone, no new objects, no background morphing, no generated captions.
```

Если lip-sync хорош, но модельный голос плох, клип принимается: модельный звук всё равно заменяется мастер-WAV. Если рот движется до первой фонемы или после последней фонемы на мастер-таймлайне — реролл клипа D.

---

## Звук

Финальный микс строится отдельно:

- мастер-голос: новый `out/drive_v21_15s.wav` без изменения скорости;
- 0.3–2.2 — двигатель и визг задней покрышки;
- 2.2–4.1 — нарастающий двигатель;
- удар стекла привязать к реальному кадру первого пролома, а не к расчётному таймкоду;
- после удара — короткий звон мелкого безопасного стекла, быстро уходящий под голос;
- с 7.0 приглушить экшен минимум на 12 dB, чтобы первая согласная фразы не терялась;
- не использовать сгенерированную речь модели и не добавлять шаги.

Голос должен быть сухим и близким; эффекты не должны маскировать слова «не скорая».

---

## Титры

Montserrat ExtraBold, белый, акцент `#4AD2FF`, тонкая тёмная обводка или тень. Центр по горизонтали, нижняя безопасная зона, но не поверх руля и подбородка.

Не ставить титры по старым фиксированным секундам. Сначала получить финальный WAV/SRT или определить границы фраз по waveform, затем привязать каждую карточку к первой слышимой фонеме и убрать на конце фразы.

Карточки:

1. **ЭТО НЕ СКОРАЯ** / **ПО ПРОСТАТЕ**
2. **ЭТО Я**
3. **ЧТО-ТО БЕСПОКОИТ** / **ВНИЗУ?**
4. **НЕ ГОНЯЙ** / **ПО ФОРУМАМ**
5. **ЗАЕДЬ НОРМАЛЬНО**

Максимум две строки, без karaoke по отдельным буквам: покарточное появление стабильнее и легче читается в динамичном Reels.

---

## Контрольные ворота

### Gate 1 — KF-D

- лицо узнаваемо и совпадает с обоими референсами;
- нет петлички, бейджа, ручки и логотипа;
- глаза освещены, рот закрыт;
- кадр средний, не макро.

### Gate 2 — клип D

- лицо не плывёт ни на одном слове;
- рот молчит до первой фонемы и полностью закрыт после последней фонемы мастер-WAV;
- нет лишних зубов, деформации подбородка и случайных жестов;
- framing не меняется.

### Gate 3 — клипы B/A/C

- B: весь лист стекла исчезает в момент удара, а осколки полностью закрывают кадр;
- A: дым идёт только от заднего колеса;
- C: лицо и одежда совпадают с KF-D, шлем уже снят, руки не касаются лица.

### Gate 4 — финал

- скрытые стыки незаметны на скорости 1× и 0.5×;
- один и тот же байк, костюм, свет и направление движения;
- исходный голос синхронен губам;
- первая фраза слышна полностью;
- титры не закрывают лицо и интерфейсные зоны Reels;
- ролик ровно 15.000 секунд, 1080×1920.

---

## Политика рероллов

- Лицо или lip-sync плохие — рероллить только D, не весь ролик.
- Стекло лишь треснуло — рероллить только B с более простым промптом; не добавлять новые действия.
- Дым из переднего колеса — рероллить только A.
- Переход C→D заметен — выбрать другой кадр выхода C или добавить 3–5 кадров мягкого дымового overlay; не морфить лицо.
- После двух одинаковых браков не повторять тот же промпт. Упростить действие или сменить модель.
- Не принимать красивый кадр, если нарушена идентичность: лицо и разборчивый текст важнее масштаба экшена.

---

## Что считается успехом

Ролик не обязан быть буквально одним сгенерированным файлом. Он обязан **выглядеть** как один быстрый непрерывный трюк, а затем как спокойное прямое обращение того же человека. Приоритеты в порядке убывания:

1. узнаваемое лицо на речи;
2. точный голос и lip-sync;
3. читаемая шутка;
4. полный разлёт стекла;
5. правильный бёрнаут;
6. иллюзия одного дубля.
