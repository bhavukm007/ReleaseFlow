from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.release import Release, ReleaseCollaborator
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.release import CollaboratorRead, ReleaseCreate, ReleaseRead, ReleaseUpdate, default_steps
from app.services.permissions import release_access_role


def status_for(steps: dict[str, bool]) -> str:
    completed = sum(steps.values())
    return "planned" if completed == 0 else "done" if completed == len(steps) else "ongoing"


def serialize(db: Session, release: Release, viewer_id: UUID) -> ReleaseRead:
    completed = sum(release.steps.values())
    rows = db.execute(
        select(ReleaseCollaborator, User)
        .join(User, User.id == ReleaseCollaborator.user_id)
        .where(ReleaseCollaborator.release_id == release.id)
        .order_by(User.full_name, User.email)
    ).all()
    owner = db.get(User, release.owner_id)
    collaborators = []
    if owner:
        collaborators.append(CollaboratorRead(
            user_id=owner.id, full_name=owner.full_name, email=owner.email, role="owner"
        ))
    collaborators.extend(
        CollaboratorRead(
            user_id=user.id, full_name=user.full_name, email=user.email, role=collaborator.role.value
        )
        for collaborator, user in rows
    )
    access_role = release_access_role(db, release, viewer_id)
    access_role_value = access_role.value if hasattr(access_role, "value") else access_role
    return ReleaseRead.model_validate(
        {
            **release.__dict__,
            "status": status_for(release.steps),
            "completed_steps": completed,
            "total_steps": len(release.steps),
            "access_role": access_role_value,
            "collaborators": collaborators,
        }
    )


def list_releases(db: Session, user_id: UUID, *, team_id: UUID | None = None, offset: int = 0, limit: int = 100) -> list[Release]:
    shared_release_ids = select(ReleaseCollaborator.release_id).where(ReleaseCollaborator.user_id == user_id)
    access = or_(Release.owner_id == user_id, Release.id.in_(shared_release_ids))
    query = select(Release).where(access)
    if team_id is None:
        query = query.where(Release.team_id.is_(None))
    else:
        query = query.where(Release.team_id == team_id)
    return list(db.scalars(query.order_by(Release.due_date, Release.id).offset(offset).limit(limit)))


def create_release(db: Session, data: ReleaseCreate, owner_id: UUID) -> Release:
    values = data.model_dump(exclude={"checklist_items", "collaborators"})
    checklist = data.checklist_items
    steps = {name: False for name in checklist} if checklist else default_steps()
    release = Release(**values, owner_id=owner_id, steps=steps)
    db.add(release)
    db.flush()
    for item in data.collaborators:
        email = str(item.email).lower()
        collaborator = db.scalar(select(User).where(User.email == email))
        if collaborator is None:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"No registered user found for {email}")
        if collaborator.id == owner_id:
            db.rollback()
            raise HTTPException(status_code=422, detail="The release owner cannot also be a collaborator")
        if release.team_id and db.scalar(select(TeamMember).where(
            TeamMember.team_id == release.team_id,
            TeamMember.user_id == collaborator.id,
        )) is None:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"{email} must join the team before being added to this release")
        db.add(ReleaseCollaborator(release_id=release.id, user_id=collaborator.id, role=item.role))
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
