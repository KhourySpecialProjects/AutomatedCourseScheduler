"""Schedule Log Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel

class ScheduleLogResponse(BaseModel):
    schedule_log_id: int | None = None
    content: str | None = None
    schedule_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}

