"""create releases table"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "releases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("additional_info", sa.Text()),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_releases_name", "releases", ["name"])
    op.create_index("ix_releases_due_date", "releases", ["due_date"])


def downgrade() -> None:
    op.drop_table("releases")
