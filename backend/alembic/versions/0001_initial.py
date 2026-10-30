"""initial schema

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("source_host", sa.String, nullable=False),
        sa.Column("base_score", sa.Integer, nullable=False),
        sa.CheckConstraint("base_score BETWEEN 1 AND 40", name="ck_alerts_base_score"),
    )
    op.create_table(
        "cases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "case_alerts",
        sa.Column(
            "case_id", sa.Integer, sa.ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("alert_id", sa.Integer, sa.ForeignKey("alerts.id"), primary_key=True),
        sa.Column(
            "added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "case_policies",
        sa.Column(
            "case_id", sa.Integer, sa.ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("policy_name", sa.String, primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("case_policies")
    op.drop_table("case_alerts")
    op.drop_table("cases")
    op.drop_table("alerts")
