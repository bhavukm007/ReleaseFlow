from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Date, DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
