from sqlalchemy import desc, select

from app.database.db import get_session
from app.database.models import Lead
from app.schemas.lead import LeadCreate, LeadUpdate


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
