from pydantic import BaseModel, ConfigDict


class LeadBase(BaseModel):
    """Shared appointment lead fields."""

    telegram_id: int
    username: str | None = None
    full_name: str | None = None
    phone: str | None = None
    service: str | None = None
    desired_datetime: str | None = None
    status: str = "collecting"


class LeadCreate(LeadBase):
    """Lead creation payload."""


class LeadUpdate(BaseModel):
    """Lead update payload."""

    full_name: str | None = None
    phone: str | None = None
    service: str | None = None
    desired_datetime: str | None = None
    status: str | None = None


class LeadRead(LeadBase):
    """Lead output schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
