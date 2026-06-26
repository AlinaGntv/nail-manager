# Telegram Nail AI Manager

Telegram AI-менеджер для мастера маникюра Анны.

Бот работает через FastAPI webhook, отвечает клиентам через OpenAI Responses API, собирает имя, телефон, услугу, желаемые дату и время, сохраняет готовую запись в SQLite и Google Sheets, а затем отправляет мастеру уведомление в Telegram.

## Настройка

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте `.env`:

```bash
copy .env.example .env
```

3. Заполните реальные ключи:

```env
OPENAI_API_KEY=sk-your-openai-api-key
BOT_TOKEN=123456789:telegram-bot-token
MANAGER_CHAT_ID=123456789
GOOGLE_SERVICE_ACCOUNT_FILE=./secrets/google-service-account.json
GOOGLE_SHEET_ID=your-google-sheet-id
```

4. При необходимости измените бизнес-настройки без правки кода:

```env
MASTER_NAME=Анна
WORK_HOURS=пн-сб 10:00-20:00
STUDIO_ADDRESS=г. Москва, ул. Примерная, 10, кабинет 5
MANICURE_PRICE=от 1500 руб.
PEDICURE_PRICE=от 2200 руб.
GEL_POLISH_PRICE=от 2000 руб.
NAIL_EXTENSION_PRICE=от 3500 руб.
```

## Локальный запуск

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Проверка:

```bash
curl http://localhost:8000/health
```

## Docker

```bash
docker compose up -d
```

## Webhook Telegram

Telegram должен видеть публичный HTTPS URL. Для локального теста используйте ngrok или cloudflared.

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://example.com/telegram/webhook" \
  -d "secret_token=change-me"
```

`secret_token` должен совпадать с `TELEGRAM_WEBHOOK_SECRET`.
