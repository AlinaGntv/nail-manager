from telegram import ReplyKeyboardRemove


def remove_keyboard() -> ReplyKeyboardRemove:
    """Return a keyboard remover to keep the dialog clean."""
    return ReplyKeyboardRemove()
