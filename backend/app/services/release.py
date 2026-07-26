from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.release import Release
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


def list_releases(db: Session) -> list[Release]:
    return list(db.scalars(select(Release).order_by(Release.due_date, Release.id)))


def create_release(db: Session, data: ReleaseCreate) -> Release:
    release = Release(**data.model_dump(), steps=default_steps())
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
