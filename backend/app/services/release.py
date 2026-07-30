from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.release import Release
from app.models.team import TeamMember
from app.schemas.release import ReleaseCreate, ReleaseRead, ReleaseUpdate, default_steps


def status_for(steps: dict[str, bool]) -> str:
    completed = sum(steps.values())
    return "planned" if completed == 0 else "done" if completed == len(steps) else "ongoing"


def serialize(release: Release) -> ReleaseRead:
    completed = sum(release.steps.values())
    return ReleaseRead.model_validate(
        {
            **release.__dict__,
            "status": status_for(release.steps),
            "completed_steps": completed,
            "total_steps": len(release.steps),
        }
    )


def list_releases(db: Session, user_id: UUID, *, team_id: UUID | None = None, offset: int = 0, limit: int = 100) -> list[Release]:
    memberships = select(TeamMember.team_id).where(TeamMember.user_id == user_id)
    access = or_(Release.owner_id == user_id, Release.team_id.in_(memberships))
    query = select(Release).where(access)
    if team_id is None:
        query = query.where(Release.team_id.is_(None))
    else:
        query = query.where(Release.team_id == team_id)
    return list(db.scalars(query.order_by(Release.due_date, Release.id).offset(offset).limit(limit)))


def create_release(db: Session, data: ReleaseCreate, owner_id: UUID) -> Release:
    values = data.model_dump(exclude={"checklist_items"})
    checklist = data.checklist_items
    steps = {name: False for name in checklist} if checklist else default_steps()
    release = Release(**values, owner_id=owner_id, steps=steps)
    db.add(release)
    db.commit()
    db.refresh(release)
    return release


def update_release(db: Session, release: Release, data: ReleaseUpdate) -> Release:
    for key, value in data.model_dump().items():
        setattr(release, key, value)
    db.commit()
    db.refresh(release)
    return release


def save(db: Session, release: Release) -> Release:
    db.add(release)
    db.commit()
    db.refresh(release)
    return release
