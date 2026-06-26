from telegram.ext import Application, ApplicationBuilder

from app.ai.openai_client import OpenAILeadClient
from app.config import Settings
from app.database.repository import LeadRepository
from app.google.sheets import GoogleSheetsService
from app.services.lead_service import LeadService
from app.services.telegram_service import TelegramService
from app.telegram.handlers import build_message_handler, build_start_handler


def build_application(settings: Settings) -> Application:
    """Build a Telegram application configured for webhook processing."""
    application = ApplicationBuilder().token(settings.bot_token).build()

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
    )

    application.add_handler(build_start_handler())
    application.add_handler(build_message_handler(lead_service))
    return application
