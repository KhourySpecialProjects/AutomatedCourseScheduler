"""Campus Pydantic schemas."""

from pydantic import BaseModel


class CampusResponse(BaseModel):
    campus_id: int
    name: str

    model_config = {"from_attributes": True}
