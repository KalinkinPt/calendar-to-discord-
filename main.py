import os
import json
import base64
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Получаем переменные окружения
CREDENTIALS_JSON = os.environ.get("CREDENTIALS_JSON")
TOKEN_JSON = os.environ.get("TOKEN_JSON")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not CREDENTIALS_JSON or not TOKEN_JSON or not DISCORD_WEBHOOK_URL:
    raise Exception("❗️Отсутствует одна из переменных окружения: CREDENTIALS_JSON, TOKEN_JSON или DISCORD_WEBHOOK_URL")

# Загружаем учётные данные
creds = Credentials.from_authorized_user_info(json.loads(TOKEN_JSON))

# Получаем сервис календаря
service = build('calendar', 'v3', credentials=creds)

def get_upcoming_events():
    now = datetime.utcnow().isoformat() + 'Z'
    end_time = (datetime.utcnow() + timedelta(hours=12)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=end_time,
        maxResults=5,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])

def send_to_discord(events):
    if not events:
        print("Нет событий.")
        return

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'Без названия')
        message = f"📅 **{summary}**\n🕒 {start}"
        payload = {'content': message}

        r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if r.status_code == 204:
            print(f"✅ Уведомление отправлено: {summary}")
        else:
            print(f"❌ Ошибка отправки: {r.status_code}")

if __name__ == "__main__":
    events = get_upcoming_events()
    send_to_discord(events)
