"""Section Lock Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class SectionLockResponse(BaseModel):
    section_lock_id: int
    section_id: int
    locked_by: int
    locked_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}
