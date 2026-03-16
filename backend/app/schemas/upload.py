"""Upload Pydantic schemas."""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    status: str  # "success", "partial", "failed"
    message: str
    records_processed: int = 0
    records_successful: int = 0
    records_failed: int = 0
    errors: list[str] | None = None
