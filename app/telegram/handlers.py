from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from app.services.lead_service import LeadService
from app.telegram.keyboards import remove_keyboard
from app.utils.logger import logger


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a greeting when a user starts the bot."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text(
        "Здравствуйте! Я помогу записаться к Анне. Напишите, какая услуга интересует и на какой день удобно.",
        reply_markup=remove_keyboard(),
    )


def build_start_handler() -> CommandHandler:
    """Create the Telegram /start command handler."""
    return CommandHandler("start", start)


def build_message_handler(lead_service: LeadService) -> MessageHandler:
    """Create the text message handler with injected business service."""

    async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_message or not update.effective_user:
            return

        text = update.effective_message.text
        if not text:
            return

        logger.info(
            "Incoming message from telegram_id={} username={}: {}",
            update.effective_user.id,
            update.effective_user.username,
            text,
        )
        reply = await lead_service.process_message(update.effective_user, text)
        await update.effective_message.reply_text(reply, reply_markup=remove_keyboard())

    return MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
