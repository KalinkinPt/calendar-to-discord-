import os
import json
import time
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests

# Проверка переменных окружения
if not all(key in os.environ for key in ["CREDENTIALS_JSON", "TOKEN_JSON", "DISCORD_WEBHOOK_URL"]):
    raise Exception("❗️Отсутствует одна из переменных окружения: CREDENTIALS_JSON, TOKEN_JSON или DISCORD_WEBHOOK_URL")

# Инициализация переменных
CREDENTIALS_JSON = json.loads(os.environ["CREDENTIALS_JSON"])
TOKEN_JSON = json.loads(os.environ["TOKEN_JSON"])
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# Хранилище отправленных событий
sent_event_ids = set()

# Функция получения сервиса календаря
def get_calendar_service():
    creds = Credentials.from_authorized_user_info(TOKEN_JSON, ["https://www.googleapis.com/auth/calendar.readonly"])
    return build("calendar", "v3", credentials=creds)

# Функция проверки событий
def check_upcoming_events():
    print("\n📅 Проверка новых событий...")
    service = get_calendar_service()

    now = datetime.now(timezone.utc).isoformat()
    end_time = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()

    calendar_id = 'primary'  # можно заменить на конкретный ID
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        print("Нет новых событий.")
        return

    for event in events:
        event_id = event.get('id')
        if event_id in sent_event_ids:
            continue

        summary = event.get('summary', 'Без названия')
        start = event['start'].get('dateTime', event['start'].get('date'))

        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%H:%M %d.%m.%Y")

        message = f"\n📤 Отправка в Discord: \U0001F4CC **{summary}**\n\n\U0001F552 {formatted_time}"
        print(message)

        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
            sent_event_ids.add(event_id)
        except Exception as e:
            print(f"❌ Ошибка отправки в Discord: {e}")

# Бесконечный цикл с проверкой каждую минуту
if __name__ == "__main__":
    while True:
        try:
            check_upcoming_events()
        except Exception as e:
            print(f"❗️Ошибка: {e}")
        time.sleep(60)
