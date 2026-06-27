from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler, ContextTypes

from app.ai.openai_client import OpenAILeadClient
from app.config import Settings
from app.database.repository import LeadRepository, ScheduleRepository
from app.google.sheets import GoogleSheetsService
from app.services.lead_service import LeadService
from app.services.schedule_service import ScheduleService
from app.services.telegram_service import TelegramService
from app.telegram.handlers import (
    build_message_handler,
    build_schedule_handlers,
    build_start_handler,
    menu_callback,
)
from app.utils.logger import logger


def build_application(settings: Settings) -> Application:
    """Build a Telegram application configured for webhook processing."""
    application = ApplicationBuilder().token(settings.bot_token).build()

    schedule_repository = ScheduleRepository()
    schedule_service = ScheduleService(repository=schedule_repository)

    lead_service = LeadService(
        ai_client=OpenAILeadClient(settings=settings),
        lead_repository=LeadRepository(),
        sheets_service=GoogleSheetsService(
            service_account_file=settings.google_service_account_file,
            sheet_id=settings.google_sheet_id,
            worksheet_name=settings.google_sheet_worksheet,
        ),
        telegram_service=TelegramService(
            bot=application.bot,
            manager_chat_id=settings.manager_chat_id,
        ),
        schedule_service=schedule_service,
    )

    # Store services in bot_data for callback handlers
    application.bot_data["schedule_service"] = schedule_service

    # Client handlers
    application.add_handler(build_start_handler())
    application.add_handler(build_message_handler(lead_service))

    # Master schedule handlers (commands + inline callbacks)
    for handler in build_schedule_handlers(schedule_service):
        application.add_handler(handler)

    # Menu callbacks — registered LAST so it doesn't block other handlers
    application.add_handler(
        CallbackQueryHandler(menu_callback, pattern=r"^menu:|^service:|^book_service:|^booking:")
    )

    # Catch-all for unhandled callbacks (debug)
    async def _debug_callback(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query:
            logger.info("UNHANDLED callback: data={} user={}", query.data, query.from_user.id if query.from_user else "?")
            await query.answer()

    application.add_handler(CallbackQueryHandler(_debug_callback))

    return application
