from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.release import Release
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User


def team_membership(db: Session, team_id: UUID, user_id: UUID) -> TeamMember | None:
    return db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))


def require_team_role(db: Session, team_id: UUID, user: User, roles: set[TeamRole] | None = None) -> TeamMember:
    member = team_membership(db, team_id, user.id)
    if member is None or (roles is not None and member.role not in roles):
        raise HTTPException(status_code=404, detail="Team not found")
    return member


def require_release_access(db: Session, release_id: int, user: User, *, destructive: bool = False) -> Release:
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    if release.team_id is None:
        if release.owner_id != user.id:
            raise HTTPException(status_code=404, detail="Release not found")
    else:
        membership = team_membership(db, release.team_id, user.id)
        if membership is None or (destructive and membership.role not in {TeamRole.owner, TeamRole.admin}):
            raise HTTPException(status_code=404, detail="Release not found")
    return release


def require_team(db: Session, team_id: UUID, user: User) -> Team:
    require_team_role(db, team_id, user)
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
