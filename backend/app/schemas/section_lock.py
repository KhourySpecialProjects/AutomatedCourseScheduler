"""Section Lock Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class SectionLockResponse(BaseModel):
    """Returned on successful lock acquisition or refresh."""

    section_lock_id: int
    section_id: int
    locked_by: int
    locked_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class ScheduleActiveLockResponse(BaseModel):
    """Returned for each active lock when polling a schedule's lock state."""

    section_id: int
    locked_by: int
    display_name: str
    expires_at: datetime

    model_config = {"from_attributes": True}
