import os
import json
import time
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import unicodedata

# 🔧 Функция для удаления некорректных символов
def sanitize(text):
    return unicodedata.normalize("NFKD", text).encode("utf-8", "ignore").decode("utf-8")

# 🔐 Получение переменных окружения
CREDENTIALS_JSON = os.environ.get("CREDENTIALS_JSON")
TOKEN_JSON = os.environ.get("TOKEN_JSON")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not all([CREDENTIALS_JSON, TOKEN_JSON, DISCORD_WEBHOOK_URL]):
    raise Exception("❗️Отсутствует одна из переменных окружения: CREDENTIALS_JSON, TOKEN_JSON или DISCORD_WEBHOOK_URL")

# 📂 Сохранение токенов во временные файлы
with open("credentials.json", "w", encoding="utf-8") as f:
    f.write(CREDENTIALS_JSON)

with open("token.json", "w", encoding="utf-8") as f:
    f.write(TOKEN_JSON)

# 📌 Хранилище ID уже отправленных событий
sent_event_ids = set()

def get_calendar_service():
    creds = Credentials.from_authorized_user_file("token.json")
    service = build("calendar", "v3", credentials=creds)
    return service

def send_to_discord(summary, start_time_fmt):
    embed = {
        "title": sanitize(f"📌 {summary}"),
        "description": sanitize(f"🕒 {start_time_fmt}"),
        "color": 0x00AEEF
    }

    payload = {
        "username": "CalendarBot",
        "embeds": [embed]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"❌ Ошибка отправки в Discord: {response.status_code} — {response.text}")

def check_upcoming_events():
    print("🔄 Проверка событий...")
    service = get_calendar_service()

    now = datetime.utcnow().isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(hours=12)).isoformat() + "Z"

    calendars = service.calendarList().list().execute().get("items", [])

    for calendar in calendars:
        calendar_id = calendar["id"]
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        for event in events:
            event_id = event["id"]
            if event_id in sent_event_ids:
                continue

            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get("summary", "Без названия")

            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                start_time_fmt = dt.strftime("%H:%M %d.%m.%Y")
            except Exception:
                start_time_fmt = start

            send_to_discord(summary, start_time_fmt)
            sent_event_ids.add(event_id)

print("✅ Bot started. 🕒 Каждую минуту проверка...")
while True:
    try:
        check_upcoming_events()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    time.sleep(60)
