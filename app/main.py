from contextlib import asynccontextmanager
from datetime import time
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request, status
from telegram import Update

from app.config import Settings, get_settings
from app.database.db import close_database, init_database
from app.database.repository import ScheduleRepository
from app.schemas.schedule import ScheduleCreate
from app.telegram.bot import build_application
from app.utils.logger import configure_logging, logger


settings: Settings = get_settings()
telegram_application = build_application(settings)


async def _init_default_schedule() -> None:
    """Seed base schedule пн-сб 10:00-20:00 if empty."""
    repo = ScheduleRepository()
    existing = await repo.get_all_schedule()
    if existing:
        return
    for day in range(6):  # 0=Mon .. 5=Sat
        await repo.set_schedule(
            ScheduleCreate(day_of_week=day, start_time=time(10, 0), end_time=time(20, 0))
        )
    logger.info("Default schedule initialized: Mon-Sat 10:00-20:00")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize resources required by the webhook app."""
    configure_logging(settings.log_level)
    await init_database(settings.database_url)
    await _init_default_schedule()
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

    try:
        update = Update.de_json(payload, telegram_application.bot)
        await telegram_application.process_update(update)
    except Exception as exc:
        logger.exception("Error processing update: {}", exc)
        raise

    return {"ok": True}
