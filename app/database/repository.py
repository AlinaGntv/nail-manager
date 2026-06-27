from datetime import date, time

from sqlalchemy import desc, select

from app.database.db import get_session
from app.database.models import Booking, Lead, Schedule, ScheduleException
from app.schemas.lead import LeadCreate, LeadUpdate
from app.schemas.schedule import (
    BookingCreate,
    ScheduleCreate,
    ScheduleExceptionCreate,
)


class LeadRepository:
    """Repository for lead persistence operations."""

    async def get_active_by_telegram_id(self, telegram_id: int) -> Lead | None:
        """Return the newest collecting lead for a Telegram user."""
        async for session in get_session():
            result = await session.execute(
                select(Lead)
                .where(Lead.telegram_id == telegram_id, Lead.status == "collecting")
                .order_by(desc(Lead.created_at))
                .limit(1)
            )
            return result.scalar_one_or_none()
        return None

    async def create(self, payload: LeadCreate) -> Lead:
        """Create a new lead."""
        async for session in get_session():
            lead = Lead(**payload.model_dump())
            session.add(lead)
            await session.commit()
            await session.refresh(lead)
            return lead
        raise RuntimeError("Database session is unavailable")

    async def update(self, lead: Lead, payload: LeadUpdate) -> Lead:
        """Update a lead with provided non-null fields."""
        async for session in get_session():
            persistent_lead = await session.merge(lead)
            for field, value in payload.model_dump(exclude_unset=True).items():
                if value is not None:
                    setattr(persistent_lead, field, value)
            await session.commit()
            await session.refresh(persistent_lead)
            return persistent_lead
        raise RuntimeError("Database session is unavailable")


class ScheduleRepository:
    """Repository for schedule, exceptions, and bookings."""

    # --- Base schedule ---

    async def get_schedule_for_day(self, day_of_week: int) -> Schedule | None:
        """Return the active base schedule entry for a weekday."""
        async for session in get_session():
            result = await session.execute(
                select(Schedule).where(
                    Schedule.day_of_week == day_of_week,
                    Schedule.is_active == True,  # noqa: E712
                )
            )
            return result.scalar_one_or_none()
        return None

    async def get_all_schedule(self) -> list[Schedule]:
        """Return all active base schedule entries ordered by day_of_week."""
        async for session in get_session():
            result = await session.execute(
                select(Schedule)
                .where(Schedule.is_active == True)  # noqa: E712
                .order_by(Schedule.day_of_week)
            )
            return list(result.scalars().all())
        return []

    async def set_schedule(self, payload: ScheduleCreate) -> Schedule:
        """Create or update the base schedule for a given day_of_week."""
        async for session in get_session():
            existing = await session.execute(
                select(Schedule).where(Schedule.day_of_week == payload.day_of_week)
            )
            schedule = existing.scalar_one_or_none()
            if schedule:
                schedule.start_time = payload.start_time
                schedule.end_time = payload.end_time
                schedule.is_active = payload.is_active
            else:
                schedule = Schedule(**payload.model_dump())
                session.add(schedule)
            await session.commit()
            await session.refresh(schedule)
            return schedule
        raise RuntimeError("Database session is unavailable")

    # --- Exceptions ---

    async def get_exception(self, target_date: date) -> ScheduleException | None:
        """Return the exception entry for a specific date."""
        async for session in get_session():
            result = await session.execute(
                select(ScheduleException).where(
                    ScheduleException.date == target_date
                )
            )
            return result.scalar_one_or_none()
        return None

    async def create_exception(self, payload: ScheduleExceptionCreate) -> ScheduleException:
        """Create or replace an exception for a specific date."""
        async for session in get_session():
            existing = await session.execute(
                select(ScheduleException).where(
                    ScheduleException.date == payload.date
                )
            )
            exc = existing.scalar_one_or_none()
            if exc:
                exc.start_time = payload.start_time
                exc.end_time = payload.end_time
                exc.is_day_off = payload.is_day_off
                exc.reason = payload.reason
            else:
                exc = ScheduleException(**payload.model_dump())
                session.add(exc)
            await session.commit()
            await session.refresh(exc)
            return exc
        raise RuntimeError("Database session is unavailable")

    async def delete_exception(self, target_date: date) -> bool:
        """Remove an exception for a specific date. Returns True if deleted."""
        async for session in get_session():
            result = await session.execute(
                select(ScheduleException).where(
                    ScheduleException.date == target_date
                )
            )
            exc = result.scalar_one_or_none()
            if exc:
                await session.delete(exc)
                await session.commit()
                return True
            return False

    # --- Bookings ---

    async def get_bookings_for_date(self, target_date: date) -> list[Booking]:
        """Return all confirmed bookings for a specific date ordered by start_time."""
        async for session in get_session():
            result = await session.execute(
                select(Booking)
                .where(
                    Booking.date == target_date,
                    Booking.status == "confirmed",
                )
                .order_by(Booking.start_time)
            )
            return list(result.scalars().all())
        return []

    async def is_slot_free(
        self,
        target_date: date,
        start: time,
        end: time,
    ) -> bool:
        """Check whether a time range has no overlapping confirmed bookings."""
        async for session in get_session():
            result = await session.execute(
                select(Booking).where(
                    Booking.date == target_date,
                    Booking.status == "confirmed",
                    Booking.start_time < end,
                    Booking.end_time > start,
                )
            )
            return result.scalar_one_or_none() is None
        return True

    async def create_booking(self, payload: BookingCreate) -> Booking:
        """Persist a new confirmed booking."""
        async for session in get_session():
            booking = Booking(**payload.model_dump())
            session.add(booking)
            await session.commit()
            await session.refresh(booking)
            return booking
        raise RuntimeError("Database session is unavailable")
