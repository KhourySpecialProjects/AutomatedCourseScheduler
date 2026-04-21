"""Time Block Pydantic schemas."""

from pydantic import BaseModel, Field


class TimeBlockResponse(BaseModel):
    """Full representation of a time block returned by the API."""

    time_block_id: int
    meeting_days: str
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    campus_id: int
    block_group: str | None = None

    model_config = {"from_attributes": True}


class TimeBlockCreate(BaseModel):
    """Payload for creating a new time block.

    `meeting_days` should be a compact string of uppercase day letters,
    e.g. "MWF" for Monday/Wednesday/Friday or "TR" for Tuesday/Thursday.

    `start_time` and `end_time` must be in "HH:MM" 24-hour format.

    `block_group` is optional.  Set it to the same 8-character hex string on
    two sibling rows to mark them as a split block (e.g. "T 9:50–11:30" and
    "R 1:30–2:50" both with the same block_group).  Split blocks are excluded
    from auto-assignment and must be assigned manually.
    """

    meeting_days: str = Field(..., min_length=1, description="Day letters, e.g. 'MWF' or 'TR'")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    campus_id: int
    block_group: str | None = Field(
        default=None,
        max_length=8,
        description="8-character hex string linking two rows of a split block pair",
    )


class TimeBlockUpdate(BaseModel):
    """Partial update payload for a time block.  All fields are optional —
    only the fields included in the request body will be updated."""

    meeting_days: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    campus_id: int | None = None
    block_group: str | None = Field(default=None, max_length=8)
