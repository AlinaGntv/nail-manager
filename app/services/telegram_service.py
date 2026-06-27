from telegram import Bot

from app.database.models import Lead


class TelegramService:
    """Service for Telegram notifications outside update handlers."""

    def __init__(self, bot: Bot, manager_chat_id: int) -> None:
        self._bot = bot
        self._manager_chat_id = manager_chat_id

    async def notify_manager(self, lead: Lead) -> None:
        """Notify the nail master about a new appointment lead."""
        username = f"@{lead.username}" if lead.username else "нет username"

        text = (
            "Новая запись! 💖\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            f"  Клиент: {lead.full_name or '—'}\n"
            f"  Телефон: {lead.phone or '—'}\n"
            f"  Услуга: {lead.service or '—'}\n"
            f"  Время: {lead.desired_datetime or '—'}\n\n"
            f"  Username: {username}\n"
            f"  Telegram ID: {lead.telegram_id}\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "Свяжитесь с клиентом для подтверждения."
        )
        await self._bot.send_message(chat_id=self._manager_chat_id, text=text)
