from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.database.session import get_db
from app.models.release import Release
from app.models.team import TeamMember
from app.schemas.release import ChecklistUpdate, InfoUpdate, ReleaseCreate, ReleaseRead, ReleaseUpdate, StepsUpdate
from app.services.activity import read_activities, record
from app.services import release as service
from app.services.permissions import require_release_access, require_team_role
from app.services.realtime import realtime

router = APIRouter(prefix="/releases", tags=["releases"])
Db = Annotated[Session, Depends(get_db)]


def recipients(db: Session, release: Release) -> set[UUID]:
    if release.team_id is None:
        return {release.owner_id}
    return set(db.scalars(select(TeamMember.user_id).where(TeamMember.team_id == release.team_id)))


def announce(background: BackgroundTasks, db: Session, release: Release, event_type: str) -> None:
    background.add_task(realtime.publish, recipients(db, release), {"type": event_type, "release_id": release.id})


@router.get("", response_model=list[ReleaseRead])
def list_all(
    db: Db, user: CurrentUser, team_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ReleaseRead]:
    return [service.serialize(item) for item in service.list_releases(db, user.id, team_id=team_id, offset=offset, limit=limit)]


@router.get("/{release_id}", response_model=ReleaseRead)
def get_one(release_id: int, db: Db, user: CurrentUser) -> ReleaseRead:
    return service.serialize(require_release_access(db, release_id, user))


@router.post("", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
def create(data: ReleaseCreate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    if data.team_id:
        require_team_role(db, data.team_id, user)
    release = service.create_release(db, data, user.id)
    record(db, user.id, "release_created", release_id=release.id, team_id=release.team_id, metadata={"name": release.name})
    db.commit()
    announce(background, db, release, "release.created")
    return service.serialize(release)


@router.put("/{release_id}", response_model=ReleaseRead)
def update(release_id: int, data: ReleaseUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = service.update_release(db, require_release_access(db, release_id, user), data)
    record(db, user.id, "release_updated", release_id=release.id, team_id=release.team_id)
    db.commit()
    announce(background, db, release, "release.updated")
    return service.serialize(release)


@router.patch("/{release_id}/steps", response_model=ReleaseRead)
def update_steps(release_id: int, data: StepsUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = require_release_access(db, release_id, user)
    release.steps = data.steps
    release = service.save(db, release)
    announce(background, db, release, "release.checklist")
    return service.serialize(release)


@router.patch("/{release_id}/checklist", response_model=ReleaseRead)
def update_checklist(release_id: int, data: ChecklistUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = require_release_access(db, release_id, user)
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
    return service.serialize(release)


@router.patch("/{release_id}/info", response_model=ReleaseRead)
def update_info(release_id: int, data: InfoUpdate, background: BackgroundTasks, db: Db, user: CurrentUser) -> ReleaseRead:
    release = require_release_access(db, release_id, user)
    release.additional_info = data.additional_info
    release = service.save(db, release)
    record(db, user.id, "notes_updated", release_id=release.id, team_id=release.team_id)
    db.commit()
    announce(background, db, release, "release.notes")
    return service.serialize(release)


@router.get("/{release_id}/activities")
def activities(release_id: int, db: Db, user: CurrentUser) -> list:
    require_release_access(db, release_id, user)
    return read_activities(db, release_id=release_id)


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(release_id: int, background: BackgroundTasks, db: Db, user: CurrentUser) -> Response:
    release = require_release_access(db, release_id, user, destructive=True)
    target_users = recipients(db, release)
    record(db, user.id, "release_deleted", team_id=release.team_id, metadata={"release_id": release.id, "name": release.name})
    db.delete(release)
    db.commit()
    background.add_task(realtime.publish, target_users, {"type": "release.deleted", "release_id": release_id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
