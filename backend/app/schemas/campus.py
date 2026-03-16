"""Campus Pydantic schemas."""

from pydantic import BaseModel


class CampusResponse(BaseModel):
    CampusID: int
    CampusName: str

    model_config = {"from_attributes": True}
