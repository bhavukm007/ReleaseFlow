from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActivityRead(BaseModel):
    id: UUID
    release_id: int | None
    team_id: UUID | None
    user_id: UUID
    user_name: str
    action: str
    metadata: dict
    created_at: datetime
