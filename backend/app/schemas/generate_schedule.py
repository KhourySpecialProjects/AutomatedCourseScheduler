"""Schedule generation request Pydantic schemas."""

from pydantic import BaseModel

from app.schemas.algorithm_input import AlgorithmParameters


class GenerateScheduleRequest(BaseModel):
    parameters: AlgorithmParameters = AlgorithmParameters()
    # TODO (future): hard/soft constraint overrides


class RegenerateScheduleRequest(BaseModel):
    parameters: AlgorithmParameters = AlgorithmParameters()
    # TODO (future): specify which sections to fill, constraint overrides
