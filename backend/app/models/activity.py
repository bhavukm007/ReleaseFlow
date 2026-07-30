from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    release_id: Mapped[int | None] = mapped_column(ForeignKey("releases.id", ondelete="SET NULL"), index=True)
    team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    details: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
