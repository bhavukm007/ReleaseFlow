from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)
Db = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = db.get(User, decode_token(credentials.credentials, "access"))
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
