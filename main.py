import os
import json
import datetime
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Завантаження облікових даних
credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/calendar.readonly"],
)

calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

service = build("calendar", "v3", credentials=credentials)
now = datetime.datetime.utcnow().isoformat() + "Z"
end_of_day = (datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat() + "Z"

events_result = service.events().list(
    calendarId=calendar_id,
    timeMin=now,
    timeMax=end_of_day,
    singleEvents=True,
    orderBy="startTime"
).execute()
events = events_result.get("items", [])

if not events:
    message = "📅 Сьогодні немає запланованих подій."
else:
    message = "**Сьогоднішні події:**\n"
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        start_time = datetime.datetime.fromisoformat(start).strftime("%H:%M")
        summary = event.get("summary", "Без назви")
        message += f"- `{start_time}` – {summary}\n"

requests.post(webhook_url, json={"content": message})