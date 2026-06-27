from datetime import date, time

from pydantic import BaseModel, ConfigDict


class ScheduleBase(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time


class ScheduleCreate(ScheduleBase):
    is_active: bool = True


class ScheduleRead(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class ScheduleExceptionBase(BaseModel):
    date: date
    start_time: time | None = None
    end_time: time | None = None
    is_day_off: bool = False
    reason: str | None = None


class ScheduleExceptionCreate(ScheduleExceptionBase):
    pass


class ScheduleExceptionRead(ScheduleExceptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BookingBase(BaseModel):
    client_name: str
    client_phone: str
    service: str
    date: date
    start_time: time
    end_time: time


class BookingCreate(BookingBase):
    lead_id: int | None = None


class BookingRead(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    lead_id: int | None = None


class AvailableSlot(BaseModel):
    start_time: time
    end_time: time
