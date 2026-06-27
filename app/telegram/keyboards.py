from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Return a keyboard remover to keep the dialog clean."""
    return ReplyKeyboardRemove()


# --- Client-facing keyboards ---


def main_menu() -> InlineKeyboardMarkup:
    """Главное меню клиента — приветствие + основные действия."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💅 Услуги и цены", callback_data="menu:services")],
            [InlineKeyboardButton("📍 Адрес и проход", callback_data="menu:address")],
            [InlineKeyboardButton("🕐 Расписание", callback_data="menu:schedule")],
            [InlineKeyboardButton("✨ Записаться", callback_data="menu:book")],
        ]
    )


def services_menu() -> InlineKeyboardMarkup:
    """Меню услуг — выбор категории."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(" Маникюр", callback_data="service:Маникюр")],
            [InlineKeyboardButton(" Педикюр", callback_data="service:Педикюр")],
            [InlineKeyboardButton("💅 Покрытие гель-лак", callback_data="service:Покрытие гель-лак")],
            [InlineKeyboardButton("✨ Наращивание", callback_data="service:Наращивание")],
            [InlineKeyboardButton("← Назад", callback_data="menu:main")],
        ]
    )


def service_detail(service: str) -> InlineKeyboardMarkup:
    """Кнопка записи после просмотра услуги."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✨ Записаться на " + service.lower(), callback_data=f"book_service:{service}")],
            [InlineKeyboardButton("← Назад", callback_data="menu:services")],
        ]
    )


def confirm_booking() -> InlineKeyboardMarkup:
    """Подтверждение записи."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(" Да, всё верно", callback_data="booking:confirm"),
                InlineKeyboardButton(" Исправить", callback_data="booking:retry"),
            ],
        ]
    )


def back_to_main() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("← В меню", callback_data="menu:main")]]
    )


# --- Master schedule keyboards ---


def master_schedule_menu() -> InlineKeyboardMarkup:
    """Меню управления расписанием для мастера."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📅 Расписание на неделю", callback_data="master:schedule")],
            [InlineKeyboardButton("🔒 Заблокировать день", callback_data="master:block")],
            [InlineKeyboardButton("🔓 Разблокировать день", callback_data="master:unblock")],
            [InlineKeyboardButton("⏰ Свободные слоты", callback_data="master:available")],
        ]
    )


def master_dates_inline(dates: list[str], action: str) -> InlineKeyboardMarkup:
    """Inline-кнопки с датами для выбора (master action)."""
    buttons = [
        [InlineKeyboardButton(d, callback_data=f"master:{action}:{d}")]
        for d in dates
    ]
    buttons.append([InlineKeyboardButton("← Назад", callback_data="master:menu")])
    return InlineKeyboardMarkup(buttons)
