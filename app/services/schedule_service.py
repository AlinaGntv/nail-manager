from datetime import date, datetime, time, timedelta

from app.database.repository import ScheduleRepository
from app.schemas.schedule import (
    AvailableSlot,
    BookingCreate,
    ScheduleExceptionCreate,
)
from app.utils.holidays import is_russian_holiday

SERVICE_DURATION = {
    "маникюр": timedelta(hours=1, minutes=30),
    "pedicure": timedelta(hours=2),
    "педикюр": timedelta(hours=2),
    "gelpolish": timedelta(hours=2),
    "покрытие": timedelta(hours=2),
    "гель-лак": timedelta(hours=2),
    "наращивание": timedelta(hours=3),
    "extension": timedelta(hours=3),
    "френч": timedelta(hours=3),
    "manicure": timedelta(hours=1, minutes=30),
}

BUFFER = timedelta(minutes=30)


class ScheduleService:
    """Business logic for schedule management and slot availability."""

    def __init__(self, repository: ScheduleRepository) -> None:
        self._repo = repository

    def get_duration(self, service: str) -> timedelta:
        """Return estimated duration for a service, defaulting to 1.5 hours."""
        key = service.lower().strip()
        for name, duration in SERVICE_DURATION.items():
            if name in key:
                return duration
        return timedelta(hours=1, minutes=30)

    async def get_available_slots(
        self,
        target_date: date,
        service: str = "",
    ) -> list[AvailableSlot]:
        """Return free time slots for a given date and service."""
        if is_russian_holiday(target_date):
            return []

        exception = await self._repo.get_exception(target_date)
        if exception and exception.is_day_off:
            return []

        if exception and exception.start_time and exception.end_time:
            day_start = exception.start_time
            day_end = exception.end_time
        else:
            schedule = await self._repo.get_schedule_for_day(target_date.weekday())
            if not schedule:
                return []
            day_start = schedule.start_time
            day_end = schedule.end_time

        duration = self.get_duration(service) if service else timedelta(hours=1, minutes=30)
        bookings = await self._repo.get_bookings_for_date(target_date)

        slots: list[AvailableSlot] = []
        current = datetime.combine(target_date, day_start)
        end_dt = datetime.combine(target_date, day_end)

        while current + duration <= end_dt:
            slot_end = current + duration
            is_free = all(
                not (b.start_time < slot_end.time() and b.end_time > current.time())
                for b in bookings
            )
            if is_free:
                slots.append(
                    AvailableSlot(
                        start_time=current.time(),
                        end_time=slot_end.time(),
                    )
                )
            current += duration + BUFFER

        return slots

    async def is_slot_free(
        self,
        target_date: date,
        start: time,
        end: time,
    ) -> bool:
        """Check if a specific slot is free (no overlapping bookings)."""
        if is_russian_holiday(target_date):
            return False

        exception = await self._repo.get_exception(target_date)
        if exception and exception.is_day_off:
            return False

        if exception and exception.start_time and exception.end_time:
            if start < exception.start_time or end > exception.end_time:
                return False
        else:
            schedule = await self._repo.get_schedule_for_day(target_date.weekday())
            if not schedule:
                return False
            if start < schedule.start_time or end > schedule.end_time:
                return False

        return await self._repo.is_slot_free(target_date, start, end)

    async def block_date(self, target_date: date, reason: str = "") -> None:
        """Mark a date as a day off."""
        await self._repo.create_exception(
            ScheduleExceptionCreate(
                date=target_date,
                is_day_off=True,
                reason=reason or "Выходной",
            )
        )

    async def unblock_date(self, target_date: date) -> bool:
        """Remove a day-off exception, restoring base schedule."""
        return await self._repo.delete_exception(target_date)

    async def set_custom_hours(
        self,
        target_date: date,
        start: time,
        end: time,
    ) -> None:
        """Set custom working hours for a specific date."""
        await self._repo.create_exception(
            ScheduleExceptionCreate(
                date=target_date,
                start_time=start,
                end_time=end,
                is_day_off=False,
                reason="Индивидуальные часы",
            )
        )

    async def format_week_schedule(self) -> str:
        """Format the current week's schedule as a human-readable string."""
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        lines: list[str] = ["Расписание на неделю:", ""]

        for i, day_name in enumerate(days):
            check_date = monday + timedelta(days=i)
            exception = await self._repo.get_exception(check_date)
            if exception:
                if exception.is_day_off:
                    lines.append(f"  {day_name} ({check_date.strftime('%d.%m')}): выходной")
                elif exception.start_time and exception.end_time:
                    lines.append(
                        f"  {day_name} ({check_date.strftime('%d.%m')}): "
                        f"{exception.start_time.strftime('%H:%M')}-{exception.end_time.strftime('%H:%M')} (индивидуальные)"
                    )
            else:
                schedule = await self._repo.get_schedule_for_day(i)
                if schedule:
                    lines.append(
                        f"  {day_name} ({check_date.strftime('%d.%m')}): "
                        f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                    )
                else:
                    lines.append(f"  {day_name} ({check_date.strftime('%d.%m')}): нет расписания")

        return "\n".join(lines)

    async def format_available_slots(
        self,
        target_date: date,
        service: str = "",
    ) -> str:
        """Format available slots for a date as a human-readable string."""
        exception = await self._repo.get_exception(target_date)
        if exception and exception.is_day_off:
            return f"На {target_date.strftime('%d.%m.%Y')} выходной"

        if is_russian_holiday(target_date):
            return f"На {target_date.strftime('%d.%m.%Y')} государственный праздник (выходной)"

        slots = await self.get_available_slots(target_date, service)
        if not slots:
            return f"На {target_date.strftime('%d.%m.%Y')} свободных слотов нет"

        lines = [f"Свободные слоты на {target_date.strftime('%d.%m.%Y')}:"]
        for slot in slots:
            lines.append(f"  {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}")
        return "\n".join(lines)

    async def create_booking(
        self,
        client_name: str,
        client_phone: str,
        service: str,
        target_date: date,
        start_time: time,
        end_time: time,
        lead_id: int | None = None,
    ) -> bool:
        """Create a booking if the slot is free. Returns True on success."""
        if not await self.is_slot_free(target_date, start_time, end_time):
            return False
        await self._repo.create_booking(
            BookingCreate(
                client_name=client_name,
                client_phone=client_phone,
                service=service,
                date=target_date,
                start_time=start_time,
                end_time=end_time,
                lead_id=lead_id,
            )
        )
        return True
