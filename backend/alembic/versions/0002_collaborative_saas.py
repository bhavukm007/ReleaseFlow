"""add authentication, ownership, teams, invitations and activity

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

LEGACY_USER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    role = postgresql.ENUM("owner", "admin", "member", name="team_role", create_type=False)
    role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_teams_owner_id", "teams", ["owner_id"])
    op.create_table(
        "team_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.UniqueConstraint("team_id", "user_id"),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"])
    op.create_table(
        "team_invitations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("invited_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("team_id", "email"),
    )
    op.create_index("ix_team_invitations_team_id", "team_invitations", ["team_id"])
    op.create_index("ix_team_invitations_email", "team_invitations", ["email"])
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.execute(
        sa.text(
            "INSERT INTO users (id, full_name, email, hashed_password, created_at, updated_at) "
            f"VALUES ('{LEGACY_USER_ID}'::uuid, 'Legacy Release Owner', 'legacy@releaseflow.invalid', "
            "'!account-disabled', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )
    op.add_column("releases", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.add_column("releases", sa.Column("team_id", sa.Uuid(), nullable=True))
    op.execute(sa.text(f"UPDATE releases SET owner_id = '{LEGACY_USER_ID}'::uuid WHERE owner_id IS NULL"))
    op.alter_column("releases", "owner_id", nullable=False)
    op.create_foreign_key("fk_releases_owner", "releases", "users", ["owner_id"], ["id"])
    op.create_foreign_key("fk_releases_team", "releases", "teams", ["team_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_releases_owner_id", "releases", ["owner_id"])
    op.create_index("ix_releases_team_id", "releases", ["team_id"])
    op.create_table(
        "activities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("release_id", sa.Integer(), sa.ForeignKey("releases.id", ondelete="SET NULL")),
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_activities_release_id", "activities", ["release_id"])
    op.create_index("ix_activities_team_id", "activities", ["team_id"])
    op.create_index("ix_activities_user_id", "activities", ["user_id"])
    op.create_index("ix_activities_action", "activities", ["action"])
    op.create_index("ix_activities_created_at", "activities", ["created_at"])


def downgrade() -> None:
    op.drop_table("activities")
    op.drop_index("ix_releases_team_id", table_name="releases")
    op.drop_index("ix_releases_owner_id", table_name="releases")
    op.drop_constraint("fk_releases_team", "releases", type_="foreignkey")
    op.drop_constraint("fk_releases_owner", "releases", type_="foreignkey")
    op.drop_column("releases", "team_id")
    op.drop_column("releases", "owner_id")
    op.drop_table("auth_sessions")
    op.drop_table("team_invitations")
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_table("users")
    sa.Enum(name="team_role").drop(op.get_bind(), checkfirst=True)
