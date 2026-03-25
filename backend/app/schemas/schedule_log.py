"""Schedule Log Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel

class ScheduleLogResponse(BaseModel):
    schedule_log_id: int 
    content: str 
    schedule_id: int 
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

