import os
import json
import datetime
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 🔐 Scopes: только чтение
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# ✅ Восстановить credentials.json из переменной среды
if not os.path.exists("credentials.json"):
    creds_data = os.environ.get("CREDENTIALS_JSON")
    if creds_data:
        with open("credentials.json", "w") as f:
            f.write(creds_data)
    else:
        raise Exception("❗️Переменная CREDENTIALS_JSON не найдена")

# 🔑 Получить Google Calendar сервис
def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            auth_url, _ = flow.authorization_url(prompt='consent')

            print("\n🔗 Перейди по этой ссылке для авторизации:\n", auth_url)
            code = input("👉 Вставь код авторизации: ")
            flow.fetch_token(code=code)
            creds = flow.credentials

            # Сохраняем токен
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

# 📣 Отправка в Discord
def send_to_discord(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if webhook_url:
        response = requests.post(webhook_url, json={"content": message})
        if response.status_code != 204:
            print("❗ Ошибка при отправке в Discord:", response.text)
    else:
        print("❗ DISCORD_WEBHOOK_URL не установлена")

# 📅 Поиск ближайших событий
def check_upcoming_events():
    service = get_calendar_service()
    now = datetime.datetime.utcnow()
    now_iso = now.isoformat() + 'Z'
    future = (now + datetime.timedelta(hours=1)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now_iso,
        timeMax=future,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        print("ℹ️ Нет событий в ближайший час.")
        return

    for event in events:
        summary = event.get('summary', 'Без названия')
        start = event['start'].get('dateTime', event['start'].get('date'))
        message = f"📅 Событие: **{summary}**\n🕒 Время: {start}"
        send_to_discord(message)

# ▶️ Старт
if __name__ == '__main__':
    send_to_discord("✅ Бот запущен и работает.")
    check_upcoming_events()
