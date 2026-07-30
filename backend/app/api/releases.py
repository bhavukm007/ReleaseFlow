from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.database.session import get_db
from app.models.release import Release, ReleaseCollaborator
from app.models.user import User
from app.models.team import TeamMember
from app.schemas.release import (
    ChecklistUpdate,
    CollaboratorCreate,
    CollaboratorRoleUpdate,
    InfoUpdate,
    ReleaseCreate,
    ReleaseRead,
    ReleaseUpdate,
    StepsUpdate,
)
from app.services.activity import read_activities, record
from app.services import release as service
from app.services.permissions import require_release_access, require_team_role
from app.services.realtime import realtime

router = APIRouter(prefix="/releases", tags=["releases"])
Db = Annotated[Session, Depends(get_db)]


def recipients(db: Session, release: Release) -> set[UUID]:
    return {release.owner_id, *db.scalars(
        select(ReleaseCollaborator.user_id).where(ReleaseCollaborator.release_id == release.id)
    )}


def announce(background: BackgroundTasks, db: Session, release: Release, event_type: str) -> None:
    background.add_task(realtime.publish, recipients(db, release), {"type": event_type, "release_id": release.id})


@router.get("", response_model=list[ReleaseRead])
def list_all(
    db: Db, user: CurrentUser, team_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ReleaseRead]:
    return [service.serialize(db, item, user.id) for item in service.list_releases(db, user.id, team_id=team_id, offset=offset, limit=limit)]


@router.get("/{release_id}", response_model=ReleaseRead)
def get_one(release_id: int, db: Db, user: CurrentUser) -> ReleaseRead:
    return service.serialize(db, require_release_access(db, release_id, user), user.id)


@router.post("", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
def create(data: ReleaseCreate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    if data.team_id:
        require_team_role(db, data.team_id, user)
    release = service.create_release(db, data, user.id)
    record(db, user.id, "release_created", release_id=release.id, team_id=release.team_id, metadata={"name": release.name})
    for collaborator in data.collaborators:
        record(
            db, user.id, "collaborator_added", release_id=release.id, team_id=release.team_id,
            metadata={"email": str(collaborator.email), "role": collaborator.role.value},
        )
    db.commit()
    announce(background, db, release, "release.created")
    return service.serialize(db, release, user.id)


@router.put("/{release_id}", response_model=ReleaseRead)
def update(release_id: int, data: ReleaseUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = service.update_release(db, require_release_access(db, release_id, user, permission="edit"), data)
    record(db, user.id, "release_updated", release_id=release.id, team_id=release.team_id)
    db.commit()
    announce(background, db, release, "release.updated")
    return service.serialize(db, release, user.id)


@router.patch("/{release_id}/steps", response_model=ReleaseRead)
def update_steps(release_id: int, data: StepsUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = require_release_access(db, release_id, user, permission="checklist")
    release.steps = data.steps
    release = service.save(db, release)
    announce(background, db, release, "release.checklist")
    return service.serialize(db, release, user.id)


@router.patch("/{release_id}/checklist", response_model=ReleaseRead)
def update_checklist(release_id: int, data: ChecklistUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = require_release_access(db, release_id, user, permission="checklist")
    previous = dict(release.steps)
    release.steps = {item.name: item.completed for item in data.items}
    removed = [name for name in previous if name not in release.steps]
    added = [name for name in release.steps if name not in previous]
    renamed_from: str | None = None
    renamed_to: str | None = None
    previous_names = list(previous)
    current_names = list(release.steps)
    if (
        len(removed) == len(added) == 1
        and previous[removed[0]] == release.steps[added[0]]
        and previous_names.index(removed[0]) == current_names.index(added[0])
    ):
        renamed_from, renamed_to = removed[0], added[0]
        record(
            db, user.id, "step_renamed", release_id=release.id, team_id=release.team_id,
            metadata={"from": renamed_from, "to": renamed_to},
        )
    for name, completed in release.steps.items():
        if name != renamed_to and name in previous and previous[name] != completed:
            record(
                db, user.id, "checklist_completed" if completed else "checklist_unchecked",
                release_id=release.id, team_id=release.team_id, metadata={"step": name},
            )
    for old_name in removed:
        if old_name != renamed_from:
            record(db, user.id, "step_deleted", release_id=release.id, team_id=release.team_id, metadata={"step": old_name})
    release = service.save(db, release)
    announce(background, db, release, "release.checklist")
    return service.serialize(db, release, user.id)


@router.patch("/{release_id}/info", response_model=ReleaseRead)
def update_info(release_id: int, data: InfoUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = require_release_access(db, release_id, user, permission="edit")
    release.additional_info = data.additional_info
    release = service.save(db, release)
    record(db, user.id, "notes_updated", release_id=release.id, team_id=release.team_id)
    db.commit()
    announce(background, db, release, "release.notes")
    return service.serialize(db, release, user.id)


@router.post("/{release_id}/collaborators", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
def add_collaborator(
    release_id: int,
    data: CollaboratorCreate,
    background: BackgroundTasks,
    db: Db,
    user: CurrentUser,
) -> ReleaseRead:
    release = require_release_access(db, release_id, user, permission="manage_collaborators")
    invited = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if invited is None:
        raise HTTPException(status_code=404, detail="No registered user found with that email")
    if invited.id == release.owner_id:
        raise HTTPException(status_code=422, detail="The release owner already has full access")
    if release.team_id and db.scalar(select(TeamMember).where(
        TeamMember.team_id == release.team_id,
        TeamMember.user_id == invited.id,
    )) is None:
        raise HTTPException(status_code=422, detail="This user must join the team before being added to the release")
    existing = db.scalar(select(ReleaseCollaborator).where(
        ReleaseCollaborator.release_id == release.id,
        ReleaseCollaborator.user_id == invited.id,
    ))
    if existing:
        existing.role = data.role
        event = "collaborator_role_updated"
    else:
        db.add(ReleaseCollaborator(release_id=release.id, user_id=invited.id, role=data.role))
        event = "collaborator_added"
    record(
        db, user.id, event, release_id=release.id, team_id=release.team_id,
        metadata={"email": invited.email, "role": data.role.value},
    )
    db.commit()
    announce(background, db, release, "release.collaborators")
    return service.serialize(db, release, user.id)


@router.patch("/{release_id}/collaborators/{collaborator_id}", response_model=ReleaseRead)
def update_collaborator(
    release_id: int,
    collaborator_id: UUID,
    data: CollaboratorRoleUpdate,
    background: BackgroundTasks,
    db: Db,
    user: CurrentUser,
) -> ReleaseRead:
    release = require_release_access(db, release_id, user, permission="manage_collaborators")
    collaborator = db.scalar(select(ReleaseCollaborator).where(
        ReleaseCollaborator.release_id == release.id,
        ReleaseCollaborator.user_id == collaborator_id,
    ))
    if collaborator is None:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    collaborator.role = data.role
    record(
        db, user.id, "collaborator_role_updated", release_id=release.id, team_id=release.team_id,
        metadata={"user_id": str(collaborator_id), "role": data.role.value},
    )
    db.commit()
    announce(background, db, release, "release.collaborators")
    return service.serialize(db, release, user.id)


@router.delete("/{release_id}/collaborators/{collaborator_id}", response_model=ReleaseRead)
def remove_collaborator(
    release_id: int,
    collaborator_id: UUID,
    background: BackgroundTasks,
    db: Db,
    user: CurrentUser,
) -> ReleaseRead:
    release = require_release_access(db, release_id, user, permission="manage_collaborators")
    collaborator = db.scalar(select(ReleaseCollaborator).where(
        ReleaseCollaborator.release_id == release.id,
        ReleaseCollaborator.user_id == collaborator_id,
    ))
    if collaborator is None:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    if collaborator.user_id == user.id:
        raise HTTPException(status_code=422, detail="You cannot remove your own release access")
    target_users = recipients(db, release)
    db.delete(collaborator)
    record(
        db, user.id, "collaborator_removed", release_id=release.id, team_id=release.team_id,
        metadata={"user_id": str(collaborator_id)},
    )
    db.commit()
    background.add_task(
        realtime.publish,
        target_users,
        {"type": "release.collaborators", "release_id": release.id},
    )
    return service.serialize(db, release, user.id)


@router.get("/{release_id}/activities")
def activities(release_id: int, db: Db, user: CurrentUser) -> list:
    require_release_access(db, release_id, user)
    return read_activities(db, release_id=release_id)


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(release_id: int, background: BackgroundTasks, db: Db, user: CurrentUser) -> Response:
    release = require_release_access(db, release_id, user, permission="delete")
    target_users = recipients(db, release)
    record(db, user.id, "release_deleted", team_id=release.team_id, metadata={"release_id": release.id, "name": release.name})
    db.delete(release)
    db.commit()
    background.add_task(realtime.publish, target_users, {"type": "release.deleted", "release_id": release_id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
