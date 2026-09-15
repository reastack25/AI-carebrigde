"""add structured medication records

Revision ID: 0003_medications
Revises: 0002_structured_medical_records
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_medications"
down_revision: Union[str, Sequence[str], None] = "0002_structured_medical_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("dosage", sa.String(length=255), nullable=True),
        sa.Column("frequency", sa.String(length=255), nullable=True),
        sa.Column("duration", sa.String(length=255), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("user_id", "conversation_id", "created_at"):
        op.create_index(f"ix_medications_{column}", "medications", [column], unique=False)


def downgrade() -> None:
    for column in ("created_at", "conversation_id", "user_id"):
        op.drop_index(f"ix_medications_{column}", table_name="medications")
    op.drop_table("medications")
