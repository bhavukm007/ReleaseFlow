from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, Db
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, token_hash, verify_password
from app.models.auth_session import AuthSession
from app.models.release import Release
from app.models.team import TeamInvitation, TeamMember
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserRead
from app.services.activity import record
from app.services.realtime import realtime

router = APIRouter(prefix="/auth", tags=["authentication"])
REFRESH_COOKIE = "releaseflow_refresh"
LEGACY_OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")


def user_read(user: User) -> UserRead:
    return UserRead(id=user.id, full_name=user.full_name, email=user.email, created_at=user.created_at, last_login=user.last_login)


def issue_tokens(db: Db, user: User, response: Response) -> AuthResponse:
    access, access_expires = create_access_token(user.id)
    refresh, refresh_hash, refresh_expires = create_refresh_token(user.id)
    db.add(AuthSession(user_id=user.id, token_hash=refresh_hash, expires_at=refresh_expires))
    db.commit()
    response.set_cookie(
        REFRESH_COOKIE, refresh, httponly=True, secure=get_settings().cookie_secure,
        samesite="none" if get_settings().cookie_secure else "lax",
        max_age=get_settings().refresh_token_days * 86400, path="/auth",
    )
    return AuthResponse(access_token=access, expires_at=access_expires, user=user_read(user))


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, response: Response, background: BackgroundTasks, db: Db) -> AuthResponse:
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(full_name=data.full_name, email=email, hashed_password=hash_password(data.password))
    db.add(user)
    try:
        db.flush()
        db.execute(update(Release).where(Release.owner_id == LEGACY_OWNER_ID).values(owner_id=user.id))
        invitations = list(db.scalars(select(TeamInvitation).where(TeamInvitation.email == email)))
        joined_team_ids = [invitation.team_id for invitation in invitations]
        for invitation in invitations:
            db.add(TeamMember(team_id=invitation.team_id, user_id=user.id, role=invitation.role))
            record(
                db,
                user.id,
                "member_joined",
                team_id=invitation.team_id,
                metadata={"email": email, "source": "pending_invitation"},
            )
            db.delete(invitation)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    for team_id in joined_team_ids:
        recipients = set(db.scalars(select(TeamMember.user_id).where(TeamMember.team_id == team_id)))
        background.add_task(realtime.publish, recipients, {"type": "team.member_joined", "team_id": team_id})
    return issue_tokens(db, user, response)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, response: Response, db: Db) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return issue_tokens(db, user, response)


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Db) -> AuthResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    user_id = decode_token(token, "refresh")
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(token), AuthSession.revoked_at.is_(None)))
    user = db.get(User, user_id)
    if session is None or user is None:
        raise HTTPException(status_code=401, detail="Refresh token is no longer valid")
    session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return issue_tokens(db, user, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Db) -> Response:
    token = request.cookies.get(REFRESH_COOKIE)
    if token:
        session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(token), AuthSession.revoked_at.is_(None)))
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
    response.delete_cookie(REFRESH_COOKIE, path="/auth", secure=get_settings().cookie_secure, samesite="none" if get_settings().cookie_secure else "lax")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return user_read(user)
