import os
import json
import requests
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pytz

# Проверка переменных окружения
if not all([os.getenv("CREDENTIALS_JSON"), os.getenv("TOKEN_JSON"), os.getenv("DISCORD_WEBHOOK_URL")]):
    raise Exception("❗️Отсутствует одна из переменных окружения: CREDENTIALS_JSON, TOKEN_JSON или DISCORD_WEBHOOK_URL")

CREDENTIALS_JSON = json.loads(os.getenv("CREDENTIALS_JSON"))
TOKEN_JSON = json.loads(os.getenv("TOKEN_JSON"))
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Читаем список уже отправленных ID событий
sent_events_file = "sent_events.json"
if os.path.exists(sent_events_file):
    with open(sent_events_file, "r") as f:
        sent_events = set(json.load(f))
else:
    sent_events = set()

def get_calendar_service():
    creds = Credentials.from_authorized_user_info(info=TOKEN_JSON, scopes=['https://www.googleapis.com/auth/calendar.readonly'])
    return build('calendar', 'v3', credentials=creds)

def send_event_to_discord(event):
    title = event.get("summary", "Без названия")
    start_time = event["start"].get("dateTime", event["start"].get("date"))
    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    date_str = dt.strftime("%d.%m.%Y")
    time_str = dt.strftime("%H:%M")

    embed = {
        "title": "📌 " + title,
        "color": 0x3498db,
        "fields": [
            {"name": "🗓️ Дата", "value": date_str, "inline": True},
            {"name": "🕒 Час", "value": time_str, "inline": True}
        ],
        "footer": {"text": "Google Calendar Bot"},
    }

    payload = {
        "username": "CalendarBot",
        "embeds": [embed]
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print("❌ Не отправлено:", response.text)

def check_upcoming_events():
    print("📅 Получение списка календарей...")
    service = get_calendar_service()
    calendar_list = service.calendarList().list().execute()

    now = datetime.now(timezone.utc)
    end_time = now + timedelta(hours=12)
    time_min = now.isoformat()
    time_max = end_time.isoformat()

    for calendar in calendar_list['items']:
        cal_id = calendar['id']
        print(f"\n🔍 Проверка календаря: {calendar['summary']} ({cal_id})")
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        for event in events:
            if event['id'] not in sent_events:
                send_event_to_discord(event)
                sent_events.add(event['id'])

    with open(sent_events_file, "w") as f:
        json.dump(list(sent_events), f)

def send_daily_schedule():
    print("📤 Отправка утреннего расписания...")
    service = get_calendar_service()
    calendar_list = service.calendarList().list().execute()

    kyiv = pytz.timezone('Europe/Kyiv')
    now_kyiv = datetime.now(kyiv)
    start_of_day = datetime(now_kyiv.year, now_kyiv.month, now_kyiv.day, 0, 0, tzinfo=kyiv)
    end_of_day = start_of_day + timedelta(days=1)

    events_today = []
    for calendar in calendar_list['items']:
        events_result = service.events().list(
            calendarId=calendar['id'],
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events_today.extend(events_result.get('items', []))

    events_today.sort(key=lambda e: e["start"].get("dateTime", e["start"].get("date")))
    schedule_lines = []
    for event in events_today:
        title = event.get("summary", "Без названия")
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00")).astimezone(kyiv)
        schedule_lines.append(f"**{dt.strftime('%H:%M')}** — {title}")

    if schedule_lines:
        payload = {
            "username": "CalendarBot",
            "embeds": [{
                "title": "📅 Расписание на сегодня",
                "description": "\n".join(schedule_lines),
                "color": 0x2ecc71,
                "footer": {"text": "Google Calendar Bot"},
            }]
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            print("❌ Ошибка отправки расписания:", response.text)
        else:
            print("✅ Утреннее сообщение успешно отправлено.")
    else:
        print("ℹ️ Сегодня нет событий для отправки.")

# Основной цикл
if __name__ == "__main__":
    import time
    last_daily_sent = None
    print("✅ Bot started. ⏰ Каждую минуту проверка...")
    while True:
        try:
            check_upcoming_events()

            kyiv = pytz.timezone('Europe/Kyiv')
            now_kyiv = datetime.now(kyiv)
            if now_kyiv.hour == 8 and (last_daily_sent != now_kyiv.date()):
                send_daily_schedule()
                last_daily_sent = now_kyiv.date()

        except Exception as e:
            print("❌ Ошибка:", e)

        time.sleep(60)
