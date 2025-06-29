import os
import json
import discord
from discord.ext import tasks
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Load credentials from Railway environment variable
credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/calendar.readonly"]
)

calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
discord_token = os.getenv("DISCORD_BOT_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))

service = build("calendar", "v3", credentials=credentials)
intents = discord.Intents.default()
client = discord.Client(intents=intents)

def get_todays_events():
    now = datetime.utcnow().isoformat() + 'Z'
    end = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return "Сьогодні немає запланованих подій."

    message_lines = ["📅 Події на сьогодні:\n"]
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        try:
            time_part = datetime.fromisoformat(start).strftime("%H:%M")
        except:
            time_part = "🕘 Час не вказано"
        summary = event.get('summary', 'Без назви')
        message_lines.append(f"• {time_part} — {summary}")
    return "\n".join(message_lines)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    send_daily_events.start()

@tasks.loop(hours=24)
async def send_daily_events():
    now = datetime.utcnow()
    if now.hour != 4:  # щоб відправляти рівно о 07:00 за GMT+3
        return
    channel = client.get_channel(channel_id)
    if channel:
        events_message = get_todays_events()
        await channel.send(events_message)

client.run(discord_token)
