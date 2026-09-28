#!/usr/bin/env python3
import json
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


ROOT = Path("/Users/pavelkuzauka/Cursor_Folders/Meta/meta")
VIDEO_DIR = ROOT / "image/concepts/video/final/youtube_ready"
CLIENT_SECRET = Path(
    "/Users/pavelkuzauka/Downloads/"
    "client_secret_146696885298-n1hua3e664682f52tcf94ncbkgg3kmmj.apps.googleusercontent.com.json"
)
TOKEN_FILE = ROOT / ".youtube_token.json"
RESULTS_FILE = VIDEO_DIR / "upload_results.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
]

VIDEOS = [
    {
        "file": "01_bacenko_rope_v15_ni_ru.mp4",
        "thumbnail": "previews/01_v15_ni.jpg",
        "title": "Как верёвочка ни вьётся – к урологу придётся",
        "description": (
            "Короткое напоминание от уролога Александра Баценко: регулярная забота "
            "о мужском здоровье лучше откладывания симптомов на потом.\n\n"
            "При жалобах и изменениях самочувствия обратитесь к врачу. Ролик не "
            "заменяет медицинскую консультацию.\n\n"
            "Подробнее: https://kravira.by\n\n"
            "#уролог #Баценко #мужскоездоровье #Кравира #Shorts"
        ),
        "tags": ["уролог", "Александр Баценко", "мужское здоровье", "профилактика", "Кравира", "Минск"],
        "category_id": "27",
    },
    {
        "file": "02_bacenko_moto_v19_ru.mp4",
        "thumbnail": "previews/02_v19_title.jpg",
        "title": "Это не скорая по простате – это Баценко",
        "description": (
            "Что-то беспокоит внизу? Не ищите диагноз на форумах. Уролог Александр "
            "Баценко напоминает: симптомы лучше обсудить с врачом очно.\n\n"
            "Ролик не заменяет консультацию и не содержит диагноза.\n\n"
            "Подробнее об урологии: https://kravira.by\n\n"
            "#уролог #Баценко #мужскоездоровье #Кравира #Минск #Shorts"
        ),
        "tags": ["уролог", "Александр Баценко", "мужское здоровье", "Кравира", "Минск", "врач"],
        "category_id": "27",
    },
    {
        "file": "03_bacenko_superhero_scenario_ru.mp4",
        "thumbnail": "previews/03_scenario_outro.jpg",
        "title": "У каждого мужчины должен быть свой супергерой",
        "description": (
            "Никаких секретов – контроль показателей, разумная нагрузка, нормальный "
            "сон и рекомендации врача. В роли уролога – Александр Баценко.\n\n"
            "План обследования и лечения всегда подбирается индивидуально после "
            "очной консультации.\n\n"
            "Подробнее: https://kravira.by\n\n"
            "#уролог #профилактика #мужскоездоровье #Кравира #Shorts"
        ),
        "tags": ["уролог", "профилактика", "мужское здоровье", "Александр Баценко", "Кравира", "врач"],
        "category_id": "27",
    },
    {
        "file": "04_bacenko_stop_suffering_virus_ru.mp4",
        "thumbnail": "previews/04_virus_blurred.jpg",
        "title": "Хватит терпеть по-тихому – сходи к урологу",
        "description": (
            "Мужское здоровье – не тема для стыда. Если появились боль, жжение, "
            "изменения мочеиспускания или другие симптомы, не откладывайте разговор "
            "с врачом.\n\n"
            "Александр Баценко – уролог медицинского центра «Кравира». Ролик не "
            "заменяет медицинскую консультацию.\n\n"
            "Подробнее: https://kravira.by\n\n"
            "#уролог #мужскоездоровье #Баценко #Кравира #Минск #Shorts"
        ),
        "tags": ["уролог", "симптомы", "мужское здоровье", "Александр Баценко", "Кравира", "Минск"],
        "category_id": "27",
    },
    {
        "file": "05_bacenko_dance_v25_ru.mp4",
        "thumbnail": "previews/05_v25_dash.jpg",
        "title": "Приём окончен – доктор в ритме",
        "description": (
            "Когда приём окончен, а энергия осталась. Александр Баценко – уролог "
            "медицинского центра «Кравира».\n\n"
            "Полезные ролики о мужском здоровье смотрите на канале.\n\n"
            "#Баценко #уролог #Кравира #Минск #Shorts"
        ),
        "tags": ["Александр Баценко", "уролог", "Кравира", "врач", "Минск", "доктор в ритме"],
        "category_id": "22",
    },
]


def load_results():
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    return {"channel": {}, "videos": {}}


def save_results(results):
    RESULTS_FILE.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def authenticate():
    credentials = None
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
        credentials = flow.run_local_server(
            host="localhost",
            port=8765,
            open_browser=False,
            authorization_prompt_message="AUTH_URL: {url}",
            success_message="Доступ к YouTube подтверждён. Можно закрыть эту вкладку.",
            prompt="consent",
            login_hint="kravira.minsk@gmail.com",
        )
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def execute_with_retry(request, retries=5):
    for attempt in range(retries):
        try:
            return request.execute()
        except HttpError as exc:
            if exc.resp.status not in (500, 502, 503, 504) or attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def resumable_upload(youtube, item):
    body = {
        "snippet": {
            "title": item["title"],
            "description": item["description"],
            "tags": item["tags"],
            "categoryId": item["category_id"],
            "defaultLanguage": "ru",
            "defaultAudioLanguage": "ru",
        },
        "status": {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True,
        },
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(
            str(VIDEO_DIR / item["file"]),
            mimetype="video/mp4",
            chunksize=8 * 1024 * 1024,
            resumable=True,
        ),
        notifySubscribers=False,
    )
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"UPLOAD_PROGRESS {item['file']} {int(status.progress() * 100)}%", flush=True)
        except HttpError as exc:
            if exc.resp.status not in (500, 502, 503, 504):
                raise
            time.sleep(2)
    return response["id"]


def main():
    credentials = authenticate()
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    results = load_results()

    channel_response = execute_with_retry(
        youtube.channels().list(part="snippet", mine=True)
    )
    channels = channel_response.get("items", [])
    if len(channels) != 1:
        raise RuntimeError(f"Ожидался один YouTube-канал, найдено: {len(channels)}")
    channel = channels[0]
    custom_url = channel["snippet"].get("customUrl", "")
    title = channel["snippet"].get("title", "")
    if custom_url.lower() != "@kravira_by":
        raise RuntimeError(
            f"Подключён неожиданный канал: {title} ({custom_url}). "
            "Загрузка остановлена до создания видео."
        )
    results["channel"] = {
        "id": channel["id"],
        "title": title,
        "custom_url": custom_url,
    }
    save_results(results)
    print(f"CHANNEL {title} {custom_url}", flush=True)

    for item in VIDEOS:
        if item["file"] in results["videos"]:
            print(f"SKIP_EXISTING {item['file']}", flush=True)
            continue
        video_id = resumable_upload(youtube, item)
        video_url = f"https://youtu.be/{video_id}"
        record = {
            "video_id": video_id,
            "url": video_url,
            "privacy_status": "unlisted",
            "title": item["title"],
            "thumbnail_status": "not_attempted",
        }
        results["videos"][item["file"]] = record
        save_results(results)
        print(f"UPLOADED {item['file']} {video_url}", flush=True)

        thumbnail = VIDEO_DIR / item["thumbnail"]
        try:
            execute_with_retry(
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail), mimetype="image/jpeg"),
                )
            )
            record["thumbnail_status"] = "uploaded"
        except HttpError as exc:
            record["thumbnail_status"] = f"failed: HTTP {exc.resp.status}"
        save_results(results)

    print("ALL_UPLOADS_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
