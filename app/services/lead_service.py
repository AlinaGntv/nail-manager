from telegram import User

from app.ai.openai_client import OpenAILeadClient
from app.database.models import Lead
from app.database.repository import LeadRepository
from app.google.sheets import GoogleSheetsService
from app.schemas.lead import LeadCreate, LeadUpdate
from app.services.telegram_service import TelegramService
from app.utils.logger import logger


class LeadService:
    """Business workflow for receiving messages and qualifying appointment leads."""

    def __init__(
        self,
        ai_client: OpenAILeadClient,
        lead_repository: LeadRepository,
        sheets_service: GoogleSheetsService,
        telegram_service: TelegramService,
    ) -> None:
        self._ai_client = ai_client
        self._lead_repository = lead_repository
        self._sheets_service = sheets_service
        self._telegram_service = telegram_service

    async def process_message(self, user: User, message: str) -> str:
        """Process a Telegram message and return a reply for the client."""
        lead = await self._get_or_create_lead(user)
        ai_response = await self._ai_client.get_response(
            message=message,
            known_name=lead.full_name,
            known_phone=lead.phone,
            known_service=lead.service,
            known_datetime=lead.desired_datetime,
        )

        updated_lead = await self._lead_repository.update(
            lead,
            LeadUpdate(
                full_name=ai_response.name,
                phone=ai_response.phone,
                service=ai_response.service,
                desired_datetime=ai_response.datetime,
                status="completed" if ai_response.lead_ready else "collecting",
            ),
        )

        if ai_response.lead_ready:
            await self._finalize_lead(updated_lead)

        return ai_response.reply

    async def _get_or_create_lead(self, user: User) -> Lead:
        """Return an active lead or create a new collecting lead for the user."""
        lead = await self._lead_repository.get_active_by_telegram_id(user.id)
        if lead:
            return lead

        return await self._lead_repository.create(
            LeadCreate(
                telegram_id=user.id,
                username=user.username,
                status="collecting",
            )
        )

    async def _finalize_lead(self, lead: Lead) -> None:
        """Persist a ready lead to external channels and notify the master."""
        try:
            await self._sheets_service.append_lead(lead)
        except Exception as exc:
            logger.exception("Failed to append lead id={} to Google Sheets: {}", lead.id, exc)
            raise

        try:
            await self._telegram_service.notify_manager(lead)
        except Exception as exc:
            logger.exception("Failed to notify manager about lead id={}: {}", lead.id, exc)
            raise
