import os
import gspread
import discord
import asyncio
from datetime import datetime
from discord import SyncWebhook, Embed
from oauth2client.service_account import ServiceAccountCredentials

# --- Настройки ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Розклад")
TIME_ZONE_OFFSET = 3  # для Киева UTC+3

# --- Авторизация Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)

# --- Загрузка таблицы ---
sheet = gc.open_by_key(GOOGLE_SHEET_ID).worksheet(SHEET_NAME)

# --- Получение расписания на сегодня ---
def get_today_schedule():
    today = datetime.utcnow().timestamp() + TIME_ZONE_OFFSET * 3600
    today_date = datetime.utcfromtimestamp(today).strftime("%d.%m.%Y")

    header_row = sheet.row_values(1)
    day_cols = {name: idx for idx, name in enumerate(header_row) if today_date in name}
    if not day_cols:
        return f"❌ У таблиці немає розкладу на {today_date}", []

    therapist_schedule = {}
    time_slots = sheet.col_values(1)[2:]  # первый столбец — время

    for therapist, col_index in day_cols.items():
        entries = sheet.col_values(col_index + 1)[2:]  # +1 потому что индексация с 0
        pairs = [(t, e) for t, e in zip(time_slots, entries) if e.strip()]
        if pairs:
            therapist_name = therapist.replace(today_date, "").strip()
            therapist_schedule[therapist_name] = pairs

    return today_date, therapist_schedule

# --- Отправка сообщения в Discord ---
def send_schedule_to_discord():
    today_date, schedule = get_today_schedule()
    webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)

    if isinstance(schedule, str):
        webhook.send(schedule)
        return

    embed = Embed(title=f"\ud83d\udcc5 Запис пацієнтів на {today_date}", color=0x3498db)

    for therapist, appointments in schedule.items():
        text = "\n".join([f"- {t} — {n}" for t, n in appointments])
        embed.add_field(name=f"\U0001f468‍⚕️ {therapist}", value=text, inline=False)

    webhook.send(embed=embed)

# --- Запуск по расписанию ---
async def run_daily():
    while True:
        now = datetime.utcnow()
        if now.hour == 4 and now.minute == 0:  # 04:00 UTC == 07:00 Kyiv
            send_schedule_to_discord()
            await asyncio.sleep(60)
        await asyncio.sleep(20)

# --- Старт ---
if __name__ == "__main__":
    print("✅ Bot started. 🕒 Щохвилини перевірка на 07:00 Kyiv...")
    asyncio.run(run_daily())
