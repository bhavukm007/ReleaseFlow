from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.release import Release, ReleaseCollaborator, ReleaseRole
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User


def team_membership(db: Session, team_id: UUID, user_id: UUID) -> TeamMember | None:
    return db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))


def require_team_role(db: Session, team_id: UUID, user: User, roles: set[TeamRole] | None = None) -> TeamMember:
    member = team_membership(db, team_id, user.id)
    if member is None or (roles is not None and member.role not in roles):
        raise HTTPException(status_code=404, detail="Team not found")
    return member


ReleasePermission = str

ROLE_PERMISSIONS: dict[str, set[ReleasePermission]] = {
    "owner": {"view", "edit", "checklist", "manage_collaborators", "delete"},
    ReleaseRole.admin.value: {"view", "edit", "checklist", "manage_collaborators"},
    ReleaseRole.other.value: {"view", "checklist"},
}


def release_access_role(db: Session, release: Release, user_id: UUID) -> str | ReleaseRole | None:
    if release.owner_id == user_id:
        return "owner"
    return db.scalar(
        select(ReleaseCollaborator.role).where(
            ReleaseCollaborator.release_id == release.id,
            ReleaseCollaborator.user_id == user_id,
        )
    )


def require_release_access(
    db: Session,
    release_id: int,
    user: User,
    *,
    permission: ReleasePermission = "view",
) -> Release:
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    role = release_access_role(db, release, user.id)
    role_value = role.value if isinstance(role, ReleaseRole) else role
    if role_value is None or permission not in ROLE_PERMISSIONS[role_value]:
        raise HTTPException(status_code=404, detail="Release not found")
    return release


def require_team(db: Session, team_id: UUID, user: User) -> Team:
    require_team_role(db, team_id, user)
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
