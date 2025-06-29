import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

# Загрузка переменных из .env
load_dotenv()

# Сохранение credentials.json из переменной окружения
with open("credentials.json", "w") as f:
    f.write(os.environ["CREDENTIALS_JSON"])

# Запуск авторизации
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

# Сохранение токена
with open("token.json", "w") as token_file:
    token_file.write(creds.to_json())

print("✅ Токен успешно сохранён в token.json")
