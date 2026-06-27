from datetime import date, time, timedelta

from telegram import CallbackQuery, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import get_settings
from app.services.lead_service import LeadService
from app.services.schedule_service import ScheduleService
from app.telegram.keyboards import (
    back_to_main,
    confirm_booking,
    main_menu,
    master_dates_inline,
    master_schedule_menu,
    remove_keyboard,
    service_detail,
    services_menu,
)
from app.utils.logger import logger


# ======================================================================
# Client-facing handlers
# ======================================================================


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие + главное меню."""
    if not update.effective_message or not update.effective_user:
        return

    name = update.effective_user.first_name or ""
    greeting = (
        f"Привет, {name}! 💖\n\n"
        "Я — помощница Анны, мастера маникюра.\n"
        "Помогу выбрать услугу и записаться на удобное время.\n\n"
        "Выбери, что тебя интересует:"
    )

    await update.effective_message.reply_text(
        greeting,
        reply_markup=main_menu(),
    )


async def menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на кнопки главного и вложенных меню."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data

    try:
        settings = get_settings()

        if data == "menu:main":
            await query.answer()
            await _show_main(query)

        elif data == "menu:services":
            await query.answer()
            text = (
                "Выбери услугу, чтобы узнать подробности и цены 💅\n\n"
                "Каждая процедура выполняется Анной лично, "
                "с вниманием к деталям и комфорту."
            )
            await query.edit_message_text(text, reply_markup=services_menu())

        elif data == "menu:address":
            await query.answer()
            text = (
                f"📍 {settings.studio_address}\n\n"
                f"🚗 {settings.route_description}\n\n"
                f"🕐 {settings.work_hours}"
            )
            await query.edit_message_text(text, reply_markup=back_to_main())

        elif data == "menu:schedule":
            await query.answer()
            text = (
                "Чтобы узнать свободное время, напиши:\n\n"
                "   « Хочу маникюр в субботу »\n\n"
                "Я покажу доступные слоты и помогу записаться ✨"
            )
            await query.edit_message_text(text, reply_markup=back_to_main())

        elif data == "menu:book":
            await query.answer()
            text = (
                "Давай запишемся! ✨\n\n"
                "Напиши, какая услуга интересует и на какой день удобно.\n"
                "Например: «Покрытие гель-лак, среда после обеда»"
            )
            await query.edit_message_text(text, reply_markup=back_to_main())

        elif data.startswith("service:"):
            await query.answer()
            service = data.split(":", 1)[1]
            text = _service_description(service)
            await query.edit_message_text(text, reply_markup=service_detail(service))

        elif data.startswith("book_service:"):
            await query.answer()
            service = data.split(":", 1)[1]
            text = (
                f"Отличный выбор! 💖\n\n"
                f"Услуга: {service}\n\n"
                "Напиши удобную дату и время, например:\n"
                "   « Суббота, 10:00 »\n"
                "   « 5 июля после обеда »"
            )
            await query.edit_message_text(text, reply_markup=back_to_main())

        elif data == "booking:confirm":
            await query.answer()
            await query.edit_message_text(
                "Заявка отправлена! 🎉\n\n"
                "Анна свяжется с тобой для подтверждения записи.\n"
                "Спасибо, что выбрала нас! 💖",
                reply_markup=back_to_main(),
            )

        elif data == "booking:retry":
            await query.answer()
            await query.edit_message_text(
                "Без проблем! Напиши заново удобное время, и я всё исправлю ✨",
                reply_markup=back_to_main(),
            )

        else:
            await query.answer()

    except Exception as exc:
        logger.exception("Error handling callback {}: {}", data, exc)
        try:
            await query.answer("Произошла ошибка, попробуйте ещё раз", show_alert=True)
        except Exception:
            pass


async def _show_main(query: CallbackQuery) -> None:
    """Показать главное меню через callback."""
    name = query.from_user.first_name if query.from_user else ""
    greeting = (
        f"Привет, {name}! 💖\n\n"
        "Я — помощница Анны, мастера маникюра.\n"
        "Помогу выбрать услугу и записаться на удобное время.\n\n"
        "Выбери, что тебя интересует:"
    )
    await query.edit_message_text(greeting, reply_markup=main_menu())


def _service_description(service: str) -> str:
    """Вернуть красивое описание услуги с ценой."""
    settings = get_settings()
    descriptions = {
        "Маникюр": (
            "Классический или аппаратный маникюр 💅\n\n"
            f"Цена: {settings.manicure_price}\n"
            "Длительность: ~1.5 часа\n\n"
            "Включает обработку кутикулы, покрытие базой и финиш.\n"
            "Идеально для тех, кто любит ухоженные натуральные ногти."
        ),
        "Педикюр": (
            "Комфортный педикюр с заботой о каждом пальчике 🦶\n\n"
            f"Цена: {settings.pedicure_price}\n"
            "Длительность: ~2 часа\n\n"
            "Обработка стоп, кутиducible, покрытие по желанию.\n"
            "В уютной обстановке с чашкой чая."
        ),
        "Покрытие гель-лак": (
            "Стойкое покрытие гель-лак налюбой дизайн 💖\n\n"
            f"Цена: {settings.gel_polish_price}\n"
            "Длительность: ~2 часа\n\n"
            "Широкая палитра оттенков: нюд, классика, сезонные тренды.\n"
            "Держится до 3 недель без сколов."
        ),
        "Наращивание": (
            "Наращивание на формах или типсах ✨\n\n"
            f"Цена: {settings.nail_extension_price}\n"
            "Длительность: ~3 часа\n\n"
            "Любая длина и форма: от классического овала до стилетто.\n"
            "Безопасные материалы, укрепление натурального ногтя."
        ),
    }
    return descriptions.get(service, f"{service}\n\nУточни цену у мастера.")


# ======================================================================
# Client message handler (AI dialog)
# ======================================================================


def build_message_handler(lead_service: LeadService) -> MessageHandler:
    """Обработка текстовых сообщений клиента (AI-диалог)."""

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


def build_start_handler() -> CommandHandler:
    """Create the Telegram /start command handler."""
    return CommandHandler("start", start)


# ======================================================================
# Master-only schedule handlers
# ======================================================================


def _is_master(update: Update) -> bool:
    """Check if the message sender is the master (manager)."""
    settings = get_settings()
    return update.effective_user is not None and update.effective_user.id == settings.manager_chat_id


def _parse_date(text: str) -> date | None:
    """Parse a DD.MM date string into a date object (current year assumed)."""
    try:
        parts = text.strip().split(".")
        day = int(parts[0])
        month = int(parts[1])
        return date(date.today().year, month, day)
    except (ValueError, IndexError):
        return None


def _parse_time_range(text: str) -> tuple[time, time] | None:
    """Parse a HH:MM-HH:MM time range string."""
    try:
        parts = text.strip().split("-")
        start_parts = parts[0].strip().split(":")
        end_parts = parts[1].strip().split(":")
        start = time(int(start_parts[0]), int(start_parts[1]))
        end = time(int(end_parts[0]), int(end_parts[1]))
        return start, end
    except (ValueError, IndexError):
        return None


async def _show_schedule(update: Update, schedule_service: ScheduleService) -> None:
    """Показать расписание на неделю."""
    if not update.effective_message:
        return
    text = await schedule_service.format_week_schedule()
    await update.effective_message.reply_text(text, reply_markup=master_schedule_menu())


async def master_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка callback-кнопок мастера."""
    query = update.callback_query
    if not query or not query.data:
        return

    if not _is_master(update):
        await query.answer("Нет доступа", show_alert=True)
        return

    await query.answer()
    data = query.data
    schedule_service: ScheduleService = ctx.bot_data["schedule_service"]

    if data == "master:menu":
        text = "Панель управления расписанием 📋"
        await query.edit_message_text(text, reply_markup=master_schedule_menu())

    elif data == "master:schedule":
        text = await schedule_service.format_week_schedule()
        await query.edit_message_text(text, reply_markup=master_schedule_menu())

    elif data == "master:block":
        today = date.today()
        dates = [(today + timedelta(days=i)).strftime("%d.%m") for i in range(14)]
        text = "Выбери дату для блокировки 🔒"
        await query.edit_message_text(text, reply_markup=master_dates_inline(dates, "block"))

    elif data.startswith("master:block:"):
        date_str = data.split(":", 2)[2]
        target_date = _parse_date(date_str)
        if target_date:
            await schedule_service.block_date(target_date)
            await query.edit_message_text(
                f" День {target_date.strftime('%d.%m.%Y')} заблокирован (выходной)",
                reply_markup=master_schedule_menu(),
            )

    elif data == "master:unblock":
        today = date.today()
        dates = [(today + timedelta(days=i)).strftime("%d.%m") for i in range(14)]
        text = "Выбери дату для разблокировки 🔓"
        await query.edit_message_text(text, reply_markup=master_dates_inline(dates, "unblock"))

    elif data.startswith("master:unblock:"):
        date_str = data.split(":", 2)[2]
        target_date = _parse_date(date_str)
        if target_date:
            deleted = await schedule_service.unblock_date(target_date)
            status = "снята" if deleted else "не найдена"
            await query.edit_message_text(
                f"Блокировка {status} для {target_date.strftime('%d.%m.%Y')}",
                reply_markup=master_schedule_menu(),
            )

    elif data == "master:available":
        today = date.today()
        dates = [(today + timedelta(days=i)).strftime("%d.%m") for i in range(14)]
        text = "Выбери дату для просмотра свободных слотов "
        await query.edit_message_text(text, reply_markup=master_dates_inline(dates, "show_slots"))

    elif data.startswith("master:show_slots:"):
        date_str = data.split(":", 2)[2]
        target_date = _parse_date(date_str)
        if target_date:
            text = await schedule_service.format_available_slots(target_date)
            await query.edit_message_text(text, reply_markup=master_schedule_menu())


def build_schedule_handlers(
    schedule_service: ScheduleService,
) -> list[CommandHandler | CallbackQueryHandler]:
    """Create command + callback handlers for master schedule management."""
    handlers: list[CommandHandler | CallbackQueryHandler] = []

    # Store schedule_service in bot_data for callback handlers
    async def _init(ctx: ContextTypes.DEFAULT_TYPE) -> None:
        ctx.bot_data["schedule_service"] = schedule_service

    # We'll attach this as a post_init callback in bot.py

    async def _schedule(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if _is_master(update):
            await _show_schedule(update, schedule_service)

    async def _block(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not _is_master(update) or not update.effective_message:
            return
        args = ctx.args or []
        if not args:
            await update.effective_message.reply_text(
                "Укажите дату: /block 28.06"
            )
            return
        target_date = _parse_date(args[0])
        if not target_date:
            await update.effective_message.reply_text(
                "Неверный формат. Используйте ДД.ММ: /block 28.06"
            )
            return
        await schedule_service.block_date(target_date)
        await update.effective_message.reply_text(
            f" День {target_date.strftime('%d.%m.%Y')} заблокирован"
        )

    async def _unblock(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not _is_master(update) or not update.effective_message:
            return
        args = ctx.args or []
        if not args:
            await update.effective_message.reply_text(
                "Укажите дату: /unblock 28.06"
            )
            return
        target_date = _parse_date(args[0])
        if not target_date:
            await update.effective_message.reply_text(
                "Неверный формат. Используйте ДД.ММ: /unblock 28.06"
            )
            return
        deleted = await schedule_service.unblock_date(target_date)
        if deleted:
            await update.effective_message.reply_text(
                f"Блокировка снята с {target_date.strftime('%d.%m.%Y')}"
            )
        else:
            await update.effective_message.reply_text(
                f"Блокировка не найдена для {target_date.strftime('%d.%m.%Y')}"
            )

    async def _sethours(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not _is_master(update) or not update.effective_message:
            return
        args = ctx.args or []
        if len(args) < 2:
            await update.effective_message.reply_text(
                "Укажите дату и время: /sethours 01.07 12-18"
            )
            return
        target_date = _parse_date(args[0])
        if not target_date:
            await update.effective_message.reply_text("Неверный формат даты. ДД.ММ")
            return
        time_range = _parse_time_range(args[1])
        if not time_range:
            await update.effective_message.reply_text("Неверный формат. ЧЧ:ММ-ЧЧ:ММ")
            return
        start, end = time_range
        await schedule_service.set_custom_hours(target_date, start, end)
        await update.effective_message.reply_text(
            f"На {target_date.strftime('%d.%m.%Y')}: {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
        )

    async def _available(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not _is_master(update) or not update.effective_message:
            return
        args = ctx.args or []
        if not args:
            await update.effective_message.reply_text("Укажите дату: /available 28.06")
            return
        target_date = _parse_date(args[0])
        if not target_date:
            await update.effective_message.reply_text("Неверный формат. ДД.ММ")
            return
        text = await schedule_service.format_available_slots(target_date)
        await update.effective_message.reply_text(text)

    handlers.append(CommandHandler("schedule", _schedule))
    handlers.append(CommandHandler("block", _block))
    handlers.append(CommandHandler("unblock", _unblock))
    handlers.append(CommandHandler("sethours", _sethours))
    handlers.append(CommandHandler("available", _available))
    handlers.append(CallbackQueryHandler(master_callback, pattern=r"^master:"))

    return handlers
