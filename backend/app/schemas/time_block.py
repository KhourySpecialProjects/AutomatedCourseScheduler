"""Time Block Pydantic schemas."""

from pydantic import BaseModel


class TimeBlockResponse(BaseModel):
    """CampusTimeBlock."""

    BlockID: int | None = None
    CampusID: int | None = None
    Count: int | None = None

    model_config = {"from_attributes": True}
