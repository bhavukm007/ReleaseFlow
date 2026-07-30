from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TeamRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[TeamRole] = mapped_column(SqlEnum(TeamRole, name="team_role"), nullable=False)


class TeamInvitation(Base):
    __tablename__ = "team_invitations"
    __table_args__ = (UniqueConstraint("team_id", "email"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    role: Mapped[TeamRole] = mapped_column(SqlEnum(TeamRole, name="team_role"), default=TeamRole.member, nullable=False)
    invited_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
