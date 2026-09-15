"""add structured symptom and medical report records

Revision ID: 0002_structured_medical_records
Revises: 0001_baseline
Create Date: 2026-09-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_structured_medical_records"
down_revision: Union[str, Sequence[str], None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "symptom_checks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("duration", sa.String(length=200), nullable=True),
        sa.Column("urgency", sa.String(length=30), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("possible_explanations", sa.JSON(), nullable=False),
        sa.Column("next_steps", sa.JSON(), nullable=False),
        sa.Column("red_flags", sa.JSON(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_symptom_checks_user_id", "symptom_checks", ["user_id"], unique=False)
    op.create_index("ix_symptom_checks_conversation_id", "symptom_checks", ["conversation_id"], unique=False)
    op.create_index("ix_symptom_checks_created_at", "symptom_checks", ["created_at"], unique=False)

    op.create_table(
        "medical_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("instruction", sa.String(length=1000), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_medical_reports_user_id", "medical_reports", ["user_id"], unique=False)
    op.create_index("ix_medical_reports_conversation_id", "medical_reports", ["conversation_id"], unique=False)
    op.create_index("ix_medical_reports_created_at", "medical_reports", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_medical_reports_created_at", table_name="medical_reports")
    op.drop_index("ix_medical_reports_conversation_id", table_name="medical_reports")
    op.drop_index("ix_medical_reports_user_id", table_name="medical_reports")
    op.drop_table("medical_reports")
    op.drop_index("ix_symptom_checks_created_at", table_name="symptom_checks")
    op.drop_index("ix_symptom_checks_conversation_id", table_name="symptom_checks")
    op.drop_index("ix_symptom_checks_user_id", table_name="symptom_checks")
    op.drop_table("symptom_checks")
