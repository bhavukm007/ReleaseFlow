from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    additional_info: Mapped[str | None] = mapped_column(Text)
    steps: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    owner = relationship("User", back_populates="releases", foreign_keys=[owner_id])
    collaborators = relationship("ReleaseCollaborator", cascade="all, delete-orphan", passive_deletes=True)


class ReleaseRole(str, Enum):
    admin = "admin"
    other = "other"


class ReleaseCollaborator(Base):
    __tablename__ = "release_collaborators"
    __table_args__ = (UniqueConstraint("release_id", "user_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[ReleaseRole] = mapped_column(SqlEnum(ReleaseRole, name="release_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
