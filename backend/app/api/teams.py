from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import delete, select

from app.api.dependencies import CurrentUser, Db
from app.models.team import Team, TeamInvitation, TeamMember, TeamRole
from app.models.user import User
from app.schemas.team import InvitationRead, InviteCreate, MemberRead, TeamCreate, TeamRead, TransferOwnership
from app.services.activity import record
from app.services.permissions import require_team, require_team_role
from app.services.realtime import realtime

router = APIRouter(prefix="/teams", tags=["teams"])


def team_recipients(db: Db, team_id: UUID) -> set[UUID]:
    return set(db.scalars(select(TeamMember.user_id).where(TeamMember.team_id == team_id)))


def serialize_team(db: Db, team: Team, current_user: User) -> TeamRead:
    memberships = db.execute(
        select(TeamMember, User).join(User, User.id == TeamMember.user_id).where(TeamMember.team_id == team.id)
    ).all()
    current = next(member for member, _ in memberships if member.user_id == current_user.id)
    invitations = list(db.scalars(select(TeamInvitation).where(TeamInvitation.team_id == team.id)))
    return TeamRead(
        id=team.id, name=team.name, owner_id=team.owner_id, role=current.role, created_at=team.created_at,
        members=[MemberRead(user_id=user.id, full_name=user.full_name, email=user.email, role=member.role) for member, user in memberships],
        invitations=[InvitationRead(id=item.id, email=item.email, role=item.role, created_at=item.created_at) for item in invitations],
    )


@router.get("", response_model=list[TeamRead])
def list_teams(db: Db, user: CurrentUser) -> list[TeamRead]:
    teams = list(db.scalars(select(Team).join(TeamMember).where(TeamMember.user_id == user.id).order_by(Team.created_at.desc())))
    return [serialize_team(db, team, user) for team in teams]


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(data: TeamCreate, background: BackgroundTasks, db: Db, user: CurrentUser) -> TeamRead:
    team = Team(name=data.name.strip(), owner_id=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.owner))
    record(db, user.id, "team_created", team_id=team.id, metadata={"team_name": team.name})
    db.commit()
    db.refresh(team)
    background.add_task(realtime.publish, {user.id}, {"type": "team.created", "team_id": team.id})
    return serialize_team(db, team, user)


@router.get("/{team_id}", response_model=TeamRead)
def get_team(team_id: UUID, db: Db, user: CurrentUser) -> TeamRead:
    return serialize_team(db, require_team(db, team_id, user), user)


@router.post("/{team_id}/invitations", status_code=status.HTTP_201_CREATED)
def invite(team_id: UUID, data: InviteCreate, background: BackgroundTasks, db: Db, user: CurrentUser) -> dict[str, str]:
    require_team_role(db, team_id, user, {TeamRole.owner, TeamRole.admin})
    if data.role == TeamRole.owner:
        raise HTTPException(status_code=422, detail="Use ownership transfer to assign the owner role")
    email = data.email.lower()
    invited = db.scalar(select(User).where(User.email == email))
    if invited:
        existing = db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == invited.id))
        if not existing:
            db.add(TeamMember(team_id=team_id, user_id=invited.id, role=data.role))
            record(db, user.id, "member_joined", team_id=team_id, metadata={"email": email})
        result = "member_added"
    else:
        existing_invite = db.scalar(select(TeamInvitation).where(TeamInvitation.team_id == team_id, TeamInvitation.email == email))
        if existing_invite:
            existing_invite.role = data.role
        else:
            db.add(TeamInvitation(team_id=team_id, email=email, role=data.role, invited_by=user.id))
        record(db, user.id, "member_invited", team_id=team_id, metadata={"email": email})
        result = "invitation_pending"
    db.commit()
    background.add_task(
        realtime.publish,
        team_recipients(db, team_id),
        {"type": "team.member_joined" if result == "member_added" else "team.invitation_created", "team_id": team_id},
    )
    return {"status": result}


@router.delete("/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(team_id: UUID, member_id: UUID, background: BackgroundTasks, db: Db, user: CurrentUser) -> None:
    require_team_role(db, team_id, user, {TeamRole.owner, TeamRole.admin})
    member = db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == member_id))
    if member is None or member.role == TeamRole.owner:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    record(db, user.id, "member_removed", team_id=team_id, metadata={"user_id": str(member_id)})
    db.commit()
    background.add_task(realtime.publish, team_recipients(db, team_id) | {member_id}, {"type": "team.member_removed", "team_id": team_id})


@router.post("/{team_id}/transfer", response_model=TeamRead)
def transfer(team_id: UUID, data: TransferOwnership, background: BackgroundTasks, db: Db, user: CurrentUser) -> TeamRead:
    require_team_role(db, team_id, user, {TeamRole.owner})
    team = require_team(db, team_id, user)
    target = db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == data.user_id))
    current = db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user.id))
    if target is None or current is None:
        raise HTTPException(status_code=404, detail="Member not found")
    target.role, current.role, team.owner_id = TeamRole.owner, TeamRole.admin, target.user_id
    db.commit()
    background.add_task(realtime.publish, team_recipients(db, team_id), {"type": "team.updated", "team_id": team_id})
    return serialize_team(db, team, user)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: UUID, background: BackgroundTasks, db: Db, user: CurrentUser) -> None:
    require_team_role(db, team_id, user, {TeamRole.owner})
    targets = team_recipients(db, team_id)
    db.execute(delete(Team).where(Team.id == team_id))
    db.commit()
    background.add_task(realtime.publish, targets, {"type": "team.deleted", "team_id": team_id})
