# Логотип Кравира

## Рабочие файлы

- `image/brand/logo_transparent.png` – основной прозрачный PNG (RGBA)
- `image/brand/logo_transparent@2x.png` – увеличенная версия
- `image/logo_1.PNG` – исходник с чёрным фоном (для пересборки)
- `image/logo_circle.png` – только знак (щит)

## Про `_logo.eps`

Текущий `image/_logo.eps` – **не настоящий EPS**, а AppleDouble/sidecar macOS
(файл метаданных после скачивания с Google Drive). Для векторной вёрстки он не подходит.

Нужно заново скачать настоящий `.eps` / `.svg` / `.pdf` с Drive и положить в `image/brand/`.

Пока используем прозрачный PNG, собранный скриптом:

```bash
source .venv/bin/activate
python -m scripts.build_ad_banners
```
