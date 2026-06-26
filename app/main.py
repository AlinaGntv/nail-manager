from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request, status
from telegram import Update

from app.config import Settings, get_settings
from app.database.db import close_database, init_database
from app.telegram.bot import build_application
from app.utils.logger import configure_logging, logger


settings: Settings = get_settings()
telegram_application = build_application(settings)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize resources required by the webhook app."""
    configure_logging(settings.log_level)
    await init_database(settings.database_url)
    await telegram_application.initialize()
    await telegram_application.start()
    logger.info("Application started")

    try:
        yield
    finally:
        logger.info("Application shutdown started")
        await telegram_application.stop()
        await telegram_application.shutdown()
        await close_database()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.post(settings.telegram_webhook_path)
async def telegram_webhook(request: Request) -> dict[str, bool]:
    """Receive Telegram webhook updates and pass them to python-telegram-bot."""
    secret_header = request.headers.get("x-telegram-bot-api-secret-token")
    if settings.telegram_webhook_secret and secret_header != settings.telegram_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram webhook secret",
        )

    payload = await request.json()
    update = Update.de_json(payload, telegram_application.bot)
    await telegram_application.process_update(update)
    return {"ok": True}
