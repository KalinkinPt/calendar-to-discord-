# Calendar to Discord Notifier

Автоматически проверяет события в Google Календаре и отправляет уведомления в Discord.

## Как настроить:

1. Скачайте `credentials.json` в Google Cloud (OAuth 2.0 Client ID).
2. Запустите `main.py` локально, чтобы получить `token.json`.
3. Добавьте в Railway переменные:
   - `CREDENTIALS_JSON`: содержимое файла `credentials.json`
   - `DISCORD_WEBHOOK_URL`: ваш Discord Webhook

4. Настройте Cron Job в Railway на запуск `python main.py` каждые 15 минут.

