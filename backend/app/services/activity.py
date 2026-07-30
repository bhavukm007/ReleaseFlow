from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import ActivityRead


def record(db: Session, user_id: UUID, action: str, *, release_id: int | None = None, team_id: UUID | None = None, metadata: dict | None = None) -> Activity:
    event = Activity(user_id=user_id, action=action, release_id=release_id, team_id=team_id, details=metadata or {})
    db.add(event)
    return event


def read_activities(db: Session, *, release_id: int | None = None, team_id: UUID | None = None, limit: int = 50) -> list[ActivityRead]:
    query = select(Activity, User.full_name).join(User, User.id == Activity.user_id)
    if release_id is not None:
        query = query.where(Activity.release_id == release_id)
    if team_id is not None:
        query = query.where(Activity.team_id == team_id)
    rows = db.execute(query.order_by(Activity.created_at.desc()).limit(limit)).all()
    return [
        ActivityRead(
            id=event.id, release_id=event.release_id, team_id=event.team_id, user_id=event.user_id,
            user_name=name, action=event.action, metadata=event.details, created_at=event.created_at,
        )
        for event, name in rows
    ]
