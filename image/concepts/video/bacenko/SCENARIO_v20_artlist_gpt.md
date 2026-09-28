# Сценарий Reels v20 — «Уролог не стучится»

Для агента GPT в Artlist. Скопировать файл целиком в чат. Приложить 1–2 фото лица Александра Баценко.

---

## Задача агенту

Собери **один** вертикальный ролик 15 секунд, 9:16, для Reels/TikTok.

Порядок:

1. Старт-кадр (image-to-image с фото лица).
2. Голос (клонирование с записи Баценко, если есть файл; иначе TTS по промпту ниже, мужской тёплый уверенный, русский).
3. Видео image-to-video: старт-кадр + промпт таймлайна + аудио как тайминг губ.
4. Финальный звук — **наш голос**, не родной звук модели. Если модель переозвучила сама — замени дорожку на наш WAV/MP3.
5. Титры поверх, karaoke, Montserrat ExtraBold.

Не делай рекламу: без логотипа, без «запишись», без телефона, без названия клиники.

Это **киношный трюк** с безопасным закалённым стеклом-бутафорией. Магазин пустой. Никого нет внутри. Никто не пострадал. Без крови, без травм.

---

## Кто в кадре

Александр Баценко — **тот же человек**, что на приложенных фото. Не «похожий врач», не другой актёр, не 20-летний.

Омоложение **на 8–10 лет с первого кадра**: гладкая живая кожа, без мешков и тёмных теней под глазами, меньше залома между бровями и носогубных, чуть плотнее линия волос. Узнаваемый тот же человек.

Одежда: белый медицинский халат, светло-голубая рубашка, тёмно-синий галстук. **Без петлички**, без бейджа, без лого.

Шлем: открытый винтажный, гоглы подняты на лоб — лицо видно. Во время разгона шлем на голове. Перед речью снимает одной рукой.

Мотоцикл: тёмный chrome cafe-racer / naked, круглая фара. Номер нечитаемый.

---

## Идея

Первые ~8 секунд — экшен без слов: бёрнаут, камера залетает внутрь витрины, он таранит стекло, осколки в объектив, стоп, снимает шлем. Потом тишина и спокойный панч в камеру. Контраст «разнёс витрину → говорит тихо и по-доброму» и есть шутка.

---

## Текст (точно эти слова, ничего не добавлять)

Ударение в «скорая» как в устойчивом «скорая помощь» (СКО-рая), не «скорАя».

Темп спокойный, короткая пауза после каждой строки:

> Это не скорая по простате.  
> Это я.  
> Если что-то беспокоит внизу — не гоняй по форумам, заедь нормально.

Голос: тёплый уверенный мужской врач, лёгкая усмешка, естественный русский, чёткая дикция. Только этот текст.

Промпт для TTS / voice clone:

```
Warm confident male doctor speaking to camera with a slight smirk. Natural Russian, clear diction, short pause after each sentence. Stress in "скорая" as in the set phrase "скорая помощь". Only this exact text, nothing else:

Это не скорая по простате.
Это я.
Если что-то беспокоит внизу — не гоняй по форумам, заедь нормально.
```

Собери drive-аудио на 15 секунд:

- 0.0–8.1 с — тишина (рот в видео закрыт)
- 8.1–14.0 с — речь
- 14.0–15.0 с — тишина (рот закрыт, лёгкая улыбка)

---

## Свет и локация

**День.** Яркая солнечная городская улица. Мягкий рассеянный ключ спереди-слева, заполнение на лицо, без теней в глазницах.

Не ночь, не неон, не тёмный паркинг, не мятный холл, не белый кабинет.

За спиной — большой пустой стеклянный фасад, полки внутри, никого нет. Без вывесок и читаемых букв.

Бёрнаут: дым **из-под заднего** колеса, шлейф позади байка. Переднее колесо чистое.

---

## Таймлайн — один непрерывный дубль, без склеек

| Сек | Картинка | Камера | Рот | Звук |
|---|---|---|---|---|
| 0.0–0.5 | Солнечный асфальт, хром, белый дым начинается | низко у переднего колеса | закрыт | холостой ход, дым |
| 0.5–1.8 | Жёсткий бёрнаут на месте, задняя покрышка, густой белый дым на светлом фоне | чуть шире | закрыт | рев, визг резины |
| 1.8–2.7 | Камера проезжает мимо него и оказывается **внутри** пустой витрины, смотрит НАРУЖУ сквозь большое стекло на него и дым | глайд внутрь | закрыт | мотор |
| 2.7–4.2 | Сквозь стекло: он разгоняется прямо в стекло и в камеру, халат развевается | изнутри, на него | закрыт | разгон |
| 4.2–4.8 | УДАР: переднее колесо пробивает, **весь** лист стекла взрывается тысячами искрящихся осколков в камеру | удар в объектив | закрыт | взрыв стекла |
| 4.8–6.2 | Слоу-мо: едет сквозь облако осколков, белый халат, солнечные блики на фрагментах | follow | закрыт | звон осколков |
| 6.2–7.9 | Нормальная скорость, тормозит, **средний план**, одной рукой снимает шлем, лицо то же, моложе, усмешка | средний, грудь–голова–руль | закрыт | тормоз |
| 7.9–8.1 | Последние осколки падают, смотрит в объектив, без наезда | тот же средний | закрыт | затихание |
| 8.1–14.0 | Сидит на байке в **том же среднем плане**, почти не двигается, говорит текст | средний, ~1.5 м, высота груди | губы по аудио | наша речь |
| 14.0–15.0 | Держит взгляд, рот полностью закрыт, спокойная улыбка | без наезда | закрыт | тишина |

Во время речи **не** уходить в экстремальный макро лица. В кадре: голова, плечи, грудь, халат, руль.

---

## Шаг 1 — старт-кадр

Формат: вертикаль 9:16. Референсы: фото лица + этот промпт.

```
Photoreal cinematic vertical 9:16 DAYLIGHT still. The EXACT same man as the reference photos: same face identity, same eyes, nose, jaw and smile, but rejuvenated by 8-10 years — smooth lively skin, NO bags and NO dark shadows under the eyes, softened frown line and nasolabial folds, slightly fuller hairline, fresh healthy look. Still clearly the same person, not a different man, not a twenty-year-old.

He sits astride a dark chrome cafe-racer motorcycle on a clean city street on a bright sunny day. White medical lab coat over a light blue shirt and navy tie, no lavalier microphone. He wears an open-face vintage motorcycle helmet with the goggles pushed UP so his whole face is clearly visible, calm confident smirk, mouth closed, one hand on the handlebar.

Behind him, a large empty glass storefront facade with clean daylight reflections, simple shelves inside, no people inside. Lighting: soft bright daylight, big soft key from the front-left filling the face evenly, gentle warm bounce from below removing eye-socket shadows, no harsh contrast, no dark night, no neon. Medium close-up three-quarter angle facing camera, shallow depth of field, crisp modern commercial look.

No text, no letters, no signage, no logos, no readable license plate, no watermark. NOT a night scene, NOT a dark parking garage, NOT a mint hallway, NOT a white cabinet office.
```

Проверь кадр до видео: тот же человек, моложе, дневной свет на лице, шлем не закрывает лицо, витрина видна.

---

## Шаг 2 — видео

Модель: Seedance 2.5 или аналог image-to-video, 15 с, 9:16. Старт = утверждённый кадр. Режим с референсом лица. Аудио = drive 15 с.

```
Continuous single 15-second vertical 9:16 cinematic DAYLIGHT action shot, ONE take, no cuts. The man is the EXACT same person as the start frame and the face references: same face, rejuvenated look with smooth skin and no dark shadows under the eyes, as in the start frame. He must stay recognizably THAT man for the whole shot, especially while speaking. White lab coat, light blue shirt, navy tie, open-face vintage helmet with goggles pushed up, no lavalier microphone. Same bright sunny city street and same empty glass storefront as the start frame. Keep the soft even daylight on his face for the whole shot — no dark night, no neon, no harsh shadows in the eye sockets.

CONTROLLED FILM STUNT with a tempered safety-glass prop storefront. The store is empty, no people inside, nobody is hurt, no blood.

CRITICAL AUDIO: the attached soundtrack is the ONLY speech timing reference. While the soundtrack is silent his mouth stays FULLY closed. Speech runs from 8.1 to 14.0 seconds — lips move ONLY in that window, matching the audio rhythm.

CRITICAL GLASS EVENT: the big glass pane MUST completely shatter and disintegrate. It is NOT allowed to stay intact, NOT allowed to only crack, NOT allowed to bend. At impact the entire sheet explodes into thousands of separate flying shards that fill the frame and fly toward the camera, sparkling in the sunlight.

CRITICAL MOTORCYCLE PHYSICS: burnout on the REAR tire, smoke from the rear wheel behind the bike, front wheel clean.

CRITICAL FRAMING: never push into an extreme macro close-up. During the speech keep a MEDIUM shot: head, shoulders, chest, white coat and the handlebar visible, camera at chest height about 1.5 meters away.

FORBIDDEN: intact or merely cracked glass at impact, changing his face into a different man, extreme macro close-up, night lighting, wheelie, jumping the bike, flips or tricks, full 360 spin, 720 spin, jump cuts, second person in frame, readable text or signage or license plate, helmet covering his face while he speaks, blood, injury, lip movement while the audio is silent, walking away, walking backward.

Timeline:
0.0-0.5s low angle at the front wheel on sunlit asphalt, chrome glints, white tire smoke starting. Mouth closed.
0.5-1.8s hard burnout in place: rear tire spins, thick white smoke billows bright against the sunlit street. Mouth closed.
1.8-2.7s the camera glides past him and moves INSIDE the empty storefront, looking back OUT through the big glass pane at him and the smoke.
2.7-4.2s seen from inside through the glass, he accelerates straight at the glass and the camera, coat flaring back, motion blur. Mouth closed.
4.2-4.8s IMPACT: the front wheel smashes through and the ENTIRE glass pane explodes into thousands of sparkling shards flying at the camera, sunlight glinting on every fragment, smoke pouring in.
4.8-6.2s slow motion: he rides through the cloud of glass shards, white coat billowing, fragments suspended in bright air.
6.2-7.9s normal speed, he brakes and stops in a MEDIUM shot, pulls the helmet OFF with one hand revealing his full recognizable younger-looking face, knowing smirk. Mouth closed.
7.9-8.1s last shards fall, he looks into the lens and settles. No push-in.
8.1-14.0s he stays seated on the bike in the SAME medium framing, almost no body movement, and speaks the attached Russian lines with accurate lip sync: Это не скорая по простате. Это я. Если что-то беспокоит внизу — не гоняй по форумам, заедь нормально.
14.0-15.0s holds eye contact, mouth FULLY closed, slight calm smile, no lip movement at all.

Photoreal, cinematic, bright clean daylight, sparkling glass particles, volumetric white smoke, shallow depth of field.
```

---

## Шаг 3 — титры

Шрифт Montserrat ExtraBold, белый, акцент бирюзовый `#4AD2FF`, центр внизу, обводка. Появляются только на речи.

| Время | Текст на экране |
|---|---|
| 8.1–9.6 | **ЭТО НЕ СКОРАЯ** / **ПО ПРОСТАТЕ** |
| 9.6–10.2 | **ЭТО Я** |
| 10.2–12.2 | ЕСЛИ ЧТО-ТО / БЕСПОКОИТ ВНИЗУ |
| 12.2–13.2 | **НЕ ГОНЯЙ** / **ПО ФОРУМАМ** |
| 13.2–14.0 | **ЗАЕДЬ НОРМАЛЬНО** |

Если губы модели открылись позже (часто +0.3–0.5 с после её же звука) — сдвинь титры и нашу речь на кадр, где рот реально открывается, а не на старт аудиодорожки модели.

---

## SFX (по кадру события)

- 0.5–1.8 — визг задней резины, дым
- 2.7–4.2 — разгон
- 4.2–4.8 — удар и разлёт стекла (якорь на кадр пролома)
- 4.8–6.2 — звон осколков
- После любого ретайминга пересчитать задержки SFX заново

Не подкладывать фейковые шаги.

---

## Браки — сразу рерол

- Стекло только треснуло или осталось целым
- Дым из-под **переднего** колеса
- Другое лицо на речи
- Ночь / неон / тёмные глазницы
- Петличка
- Шлем на лице во время речи
- Макро только глаз/рта на тексте
- 360/720, вилли, прыжки, трюки
- Читаемые буквы, номер, лого
- Кровь, люди в магазине
- Рот шевелится в тишине
- Склейка нескольких клипов вместо одного дубля

---

## Чеклист перед сдачей

- [ ] Тот же человек, моложе на 8–10 лет, дневной свет на лице
- [ ] Один дубль 15 с, 9:16
- [ ] Витрина реально разлетается
- [ ] Бёрнаут с заднего колеса
- [ ] Шлем снят до речи, средний план на тексте
- [ ] Финальный звук = наш голос и наш текст
- [ ] Титры по фразам, без рекламы
- [ ] Хвост 14.0–15.0: рот закрыт
