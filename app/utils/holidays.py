from datetime import date

# Fixed-date Russian public holidays (month, day)
_FIXED_HOLIDAYS = [
    (1, 1),  # Новогодние каникулы
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),  # Рождество
    (1, 8),
    (2, 23),  # День защитника Отечества
    (3, 8),  # Международный женский день
    (5, 1),  # Праздник Весны и Труда
    (5, 9),  # День Победы
    (6, 12),  # День России
    (11, 4),  # День народного единства
]


def is_russian_holiday(target_date: date) -> bool:
    """Return True if the given date is a fixed Russian public holiday."""
    return (target_date.month, target_date.day) in _FIXED_HOLIDAYS
