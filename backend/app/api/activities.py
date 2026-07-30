from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import and_, or_, select

from app.api.dependencies import CurrentUser, Db
from app.models.activity import Activity
from app.models.release import Release
from app.models.release import ReleaseCollaborator
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.activity import ActivityRead

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityRead])
def recent_activities(
    db: Db,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[ActivityRead]:
    team_ids = select(TeamMember.team_id).where(TeamMember.user_id == user.id)
    shared_ids = select(ReleaseCollaborator.release_id).where(ReleaseCollaborator.user_id == user.id)
    accessible_ids = select(Release.id).where(or_(Release.owner_id == user.id, Release.id.in_(shared_ids)))
    query = (
        select(Activity, User.full_name)
        .join(User, User.id == Activity.user_id)
        .where(or_(
            Activity.user_id == user.id,
            Activity.release_id.in_(accessible_ids),
            and_(Activity.release_id.is_(None), Activity.team_id.in_(team_ids)),
        ))
        .order_by(Activity.created_at.desc())
        .limit(limit)
    )
    return [
        ActivityRead(
            id=event.id,
            release_id=event.release_id,
            team_id=event.team_id,
            user_id=event.user_id,
            user_name=user_name,
            action=event.action,
            metadata=event.details,
            created_at=event.created_at,
        )
        for event, user_name in db.execute(query)
    ]
