from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_STEP_NAMES = (
    "Code Freeze",
    "QA Completed",
    "Documentation Updated",
    "Security Review",
    "Performance Testing",
    "Deployment Ready",
    "Production Deployment",
    "Post Deployment Verification",
)
Status = Literal["planned", "ongoing", "done"]


def default_steps() -> dict[str, bool]:
    return {name: False for name in DEFAULT_STEP_NAMES}


class ReleaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    due_date: date
    additional_info: str | None = Field(default=None, max_length=10_000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        return value


class ReleaseUpdate(ReleaseCreate):
    pass


class StepsUpdate(BaseModel):
    steps: dict[str, bool]

    @field_validator("steps")
    @classmethod
    def exact_steps(cls, value: dict[str, bool]) -> dict[str, bool]:
        if set(value) != set(DEFAULT_STEP_NAMES):
            raise ValueError("Steps must contain exactly the eight default steps")
        return {name: value[name] for name in DEFAULT_STEP_NAMES}


class InfoUpdate(BaseModel):
    additional_info: str | None = Field(default=None, max_length=10_000)


class ReleaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    due_date: date
    additional_info: str | None
    steps: dict[str, bool]
    status: Status
    completed_steps: int
    total_steps: int
    created_at: datetime
    updated_at: datetime
