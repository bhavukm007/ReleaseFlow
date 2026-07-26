from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.release import Release
from app.schemas.release import InfoUpdate, ReleaseCreate, ReleaseRead, ReleaseUpdate, StepsUpdate
from app.services import release as service

router = APIRouter(prefix="/releases", tags=["releases"])
Db = Annotated[Session, Depends(get_db)]


def require_release(release_id: int, db: Session) -> Release:
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return release


@router.get("", response_model=list[ReleaseRead])
def list_all(db: Db) -> list[ReleaseRead]:
    return [service.serialize(item) for item in service.list_releases(db)]


@router.get("/{release_id}", response_model=ReleaseRead)
def get_one(release_id: int, db: Db) -> ReleaseRead:
    return service.serialize(require_release(release_id, db))


@router.post("", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
def create(data: ReleaseCreate, db: Db) -> ReleaseRead:
    return service.serialize(service.create_release(db, data))


@router.put("/{release_id}", response_model=ReleaseRead)
def update(release_id: int, data: ReleaseUpdate, db: Db) -> ReleaseRead:
    return service.serialize(service.update_release(db, require_release(release_id, db), data))


@router.patch("/{release_id}/steps", response_model=ReleaseRead)
def update_steps(release_id: int, data: StepsUpdate, db: Db) -> ReleaseRead:
    release = require_release(release_id, db)
    release.steps = data.steps
    return service.serialize(service.save(db, release))


@router.patch("/{release_id}/info", response_model=ReleaseRead)
def update_info(release_id: int, data: InfoUpdate, db: Db) -> ReleaseRead:
    release = require_release(release_id, db)
    release.additional_info = data.additional_info
    return service.serialize(service.save(db, release))


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(release_id: int, db: Db) -> Response:
    db.delete(require_release(release_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
