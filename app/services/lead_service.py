from datetime import date, datetime, time, timedelta

from telegram import User

from app.ai.openai_client import OpenAILeadClient
from app.database.models import Lead
from app.database.repository import LeadRepository
from app.google.sheets import GoogleSheetsService
from app.schemas.lead import LeadCreate, LeadUpdate
from app.services.schedule_service import ScheduleService
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
        schedule_service: ScheduleService,
    ) -> None:
        self._ai_client = ai_client
        self._lead_repository = lead_repository
        self._sheets_service = sheets_service
        self._telegram_service = telegram_service
        self._schedule_service = schedule_service

    async def process_message(self, user: User, message: str) -> str:
        """Process a Telegram message and return a reply for the client."""
        lead = await self._get_or_create_lead(user)

        available_slots = await self._get_available_slots(lead.service, message)

        ai_response = await self._ai_client.get_response(
            message=message,
            known_name=lead.full_name,
            known_phone=lead.phone,
            known_service=lead.service,
            known_datetime=lead.desired_datetime,
            available_slots=available_slots,
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

    async def reset_lead(self, telegram_id: int) -> None:
        """Mark any existing collecting leads as stale."""
        lead = await self._lead_repository.get_active_by_telegram_id(telegram_id)
        if lead:
            await self._lead_repository.update(lead, LeadUpdate(status="stale"))

    async def _get_available_slots(self, service: str | None, message: str) -> str | None:
        """Try to extract a date from the message and return available slots."""
        parsed_date = self._extract_date(message)
        if not parsed_date:
            return None

        slots = await self._schedule_service.get_available_slots(
            target_date=parsed_date,
            service=service or "",
        )
        if not slots:
            return None

        lines = [f"Свободные слоты на {parsed_date.strftime('%d.%m.%Y')}:"]
        for slot in slots:
            lines.append(f"  {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}")
        return "\n".join(lines)

    def _extract_date(self, message: str) -> date | None:
        """Try to extract a date from the message text."""
        import re

        today = date.today()

        month_names = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
        }
        day_names = {
            "понедельник": 0, "вторник": 1, "среда": 2, "четверг": 3,
            "пятница": 4, "суббота": 5, "воскресенье": 6,
        }

        msg_lower = message.lower()

        for day_name, day_num in day_names.items():
            if day_name in msg_lower:
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return today + timedelta(days=days_ahead)

        for name, month_num in month_names.items():
            if name in msg_lower:
                match = re.search(rf"(\d{{1,2}})\s*{name}", msg_lower)
                if match:
                    day = int(match.group(1))
                    try:
                        return date(today.year, month_num, day)
                    except ValueError:
                        return None

        match = re.search(r"(\d{1,2})\.(\d{1,2})", message)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            try:
                return date(today.year, month, day)
            except ValueError:
                return None

        return None

    async def _finalize_lead(self, lead: Lead) -> None:
        """Persist a ready lead to external channels and notify the master."""
        if lead.desired_datetime and lead.service:
            parsed_date = self._parse_lead_date(lead.desired_datetime)
            if parsed_date:
                duration = self._schedule_service.get_duration(lead.service)
                slots = await self._schedule_service.get_available_slots(
                    target_date=parsed_date,
                    service=lead.service,
                )
                if slots:
                    slot = slots[0]
                    await self._schedule_service.create_booking(
                        client_name=lead.full_name or "Клиент",
                        client_phone=lead.phone or "",
                        service=lead.service,
                        target_date=parsed_date,
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        lead_id=lead.id,
                    )

        try:
            await self._sheets_service.append_lead(lead)
        except Exception as exc:
            logger.exception("Failed to append lead id={} to Google Sheets: {}", lead.id, exc)

        try:
            await self._telegram_service.notify_manager(lead)
        except Exception as exc:
            logger.exception("Failed to notify manager about lead id={}: {}", lead.id, exc)

    def _parse_lead_date(self, datetime_str: str) -> date | None:
        """Try to parse a date from the lead's desired_datetime string."""
        import re

        today = date.today()

        match = re.search(r"(\d{1,2})\.(\d{1,2})", datetime_str)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            try:
                return date(today.year, month, day)
            except ValueError:
                return None

        month_names = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
            "мая": 5, "июня": 6, "июля": 7, "августа": 8,
            "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
        }
        for name, month_num in month_names.items():
            if name in datetime_str.lower():
                match = re.search(rf"(\d{{1,2}})\s*{name}", datetime_str.lower())
                if match:
                    day = int(match.group(1))
                    try:
                        return date(today.year, month_num, day)
                    except ValueError:
                        return None

        return None
