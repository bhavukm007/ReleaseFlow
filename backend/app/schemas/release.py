from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.release import ReleaseRole

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
AccessRole = Literal["owner", "admin", "other"]


class CollaboratorCreate(BaseModel):
    email: EmailStr
    role: ReleaseRole = ReleaseRole.other


class CollaboratorRead(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    role: AccessRole


class CollaboratorRoleUpdate(BaseModel):
    role: ReleaseRole


def default_steps() -> dict[str, bool]:
    return {name: False for name in DEFAULT_STEP_NAMES}


class ReleaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    due_date: date
    additional_info: str | None = Field(default=None, max_length=10_000)
    checklist_items: list[str] | None = None
    team_id: UUID | None = None
    collaborators: list[CollaboratorCreate] = Field(default_factory=list, max_length=50)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        return value

    @field_validator("checklist_items")
    @classmethod
    def clean_checklist(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("A release must contain at least one checklist item")
        if len(set(item.casefold() for item in cleaned)) != len(cleaned):
            raise ValueError("Checklist item names must be unique")
        if any(len(item) > 200 for item in cleaned):
            raise ValueError("Checklist item names cannot exceed 200 characters")
        return cleaned

    @field_validator("collaborators")
    @classmethod
    def unique_collaborators(cls, value: list[CollaboratorCreate]) -> list[CollaboratorCreate]:
        emails = [str(item.email).lower() for item in value]
        if len(set(emails)) != len(emails):
            raise ValueError("Collaborator emails must be unique")
        return value


class ReleaseUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    due_date: date
    additional_info: str | None = Field(default=None, max_length=10_000)


class StepsUpdate(BaseModel):
    steps: dict[str, bool]

    @field_validator("steps")
    @classmethod
    def exact_steps(cls, value: dict[str, bool]) -> dict[str, bool]:
        if set(value) != set(DEFAULT_STEP_NAMES):
            raise ValueError("Steps must contain exactly the eight default steps")
        return {name: value[name] for name in DEFAULT_STEP_NAMES}


class ChecklistItem(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    completed: bool = False


class ChecklistUpdate(BaseModel):
    items: list[ChecklistItem] = Field(min_length=1)

    @field_validator("items")
    @classmethod
    def unique_names(cls, value: list[ChecklistItem]) -> list[ChecklistItem]:
        names = [item.name.strip() for item in value]
        if len(set(name.casefold() for name in names)) != len(names):
            raise ValueError("Checklist item names must be unique")
        return [ChecklistItem(name=name, completed=item.completed) for name, item in zip(names, value, strict=True)]


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
    owner_id: UUID
    team_id: UUID | None
    access_role: AccessRole
    collaborators: list[CollaboratorRead]
