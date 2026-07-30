from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.api.dependencies import CurrentUser, Db
from app.models.activity import Activity
from app.models.release import Release
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
    personal_ids = select(Release.id).where(Release.owner_id == user.id, Release.team_id.is_(None))
    query = (
        select(Activity, User.full_name)
        .join(User, User.id == Activity.user_id)
        .where(or_(Activity.user_id == user.id, Activity.team_id.in_(team_ids), Activity.release_id.in_(personal_ids)))
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
