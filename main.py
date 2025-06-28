import os
import json
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Проверка переменных окружения
if not all(key in os.environ for key in ["CREDENTIALS_JSON", "TOKEN_JSON", "DISCORD_WEBHOOK_URL"]):
    raise Exception("❗️Отсутствует одна из переменных окружения: CREDENTIALS_JSON, TOKEN_JSON или DISCORD_WEBHOOK_URL")

# Загрузка переменных
credentials_json = json.loads(os.environ["CREDENTIALS_JSON"])
token_json = json.loads(os.environ["TOKEN_JSON"])
webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

# Авторизация
creds = Credentials.from_authorized_user_info(info=token_json)

# Получаем сервис Google Calendar
service = build("calendar", "v3", credentials=creds)

def check_upcoming_events():
    print("📅 Получение списка календарей...")
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list["items"]:
        print(f"- {calendar['summary']} (ID: {calendar['id']})")

    # Используется основной календарь — замени, если нужно
    calendar_id = "primary"

    now = datetime.utcnow().isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(hours=12)).isoformat() + "Z"

    print(f"\n🔍 Поиск событий с {now} по {end_time} в календаре: {calendar_id}")

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=end_time,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    if not events:
        print("⛔️ Нет событий.")
        return

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "Без названия")
        event_time = datetime.fromisoformat(start.replace("Z", "+00:00")).strftime("%H:%M %d.%m.%Y")

        message = f"📌 **{summary}**\n🕒 {event_time}"
        print(f"📤 Отправка в Discord: {message}")
        requests.post(webhook_url, json={"content": message})

# Запуск
check_upcoming_events()
