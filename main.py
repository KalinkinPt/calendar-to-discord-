# main.py
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, timedelta
import discord
import asyncio
import os

# Константы
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
SERVICE_ACCOUNT_FILE = "service_account.json"
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Авторизация
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)

# Получение событий на сегодня
now = datetime.utcnow()
start_of_day = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
end_of_day = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'

events_result = service.events().list(
    calendarId=CALENDAR_ID,
    timeMin=start_of_day,
    timeMax=end_of_day,
    singleEvents=True,
    orderBy='startTime'
).execute()
events = events_result.get('items', [])

# Форматирование сообщений
if not events:
    message = "📅 На сегодня событий в календаре нет."
else:
    message = "📅 Расписание на сегодня:\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        time_str = dt.strftime('%H:%M')
        summary = event.get('summary', 'Без названия')
        message += f"🕒 {time_str} — {summary}\n"

# Отправка в Discord
import requests
response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

if response.status_code == 204:
    print("Успешно отправлено в Discord")
else:
    print(f"Ошибка отправки: {response.status_code}\n{response.text}")
