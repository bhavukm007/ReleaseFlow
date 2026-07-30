from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.team import TeamRole


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Team name must contain at least two characters")
        return value


class InviteCreate(BaseModel):
    email: EmailStr
    role: TeamRole = TeamRole.member


class TransferOwnership(BaseModel):
    user_id: UUID


class MemberRead(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    role: TeamRole


class InvitationRead(BaseModel):
    id: UUID
    email: EmailStr
    role: TeamRole
    created_at: datetime


class TeamRead(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    role: TeamRole
    created_at: datetime
    members: list[MemberRead] = Field(default_factory=list)
    invitations: list[InvitationRead] = Field(default_factory=list)
