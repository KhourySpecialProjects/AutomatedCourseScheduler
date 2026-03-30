"""Campus Pydantic schemas."""

from pydantic import BaseModel


class CampusResponse(BaseModel):
    campus_id: int
    name: str
    active: bool

    model_config = {"from_attributes": True}


class CampusCreate(BaseModel):
    name: str
    active: bool = True


class CampusUpdate(BaseModel):
    name: str | None = None
    active: bool | None = None
