"""add release-scoped collaborators

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    role = postgresql.ENUM("admin", "other", name="release_role", create_type=False)
    role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "release_collaborators",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("release_id", sa.Integer(), sa.ForeignKey("releases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("release_id", "user_id"),
    )
    op.create_index("ix_release_collaborators_release_id", "release_collaborators", ["release_id"])
    op.create_index("ix_release_collaborators_user_id", "release_collaborators", ["user_id"])


def downgrade() -> None:
    op.drop_table("release_collaborators")
    postgresql.ENUM(name="release_role").drop(op.get_bind(), checkfirst=True)
