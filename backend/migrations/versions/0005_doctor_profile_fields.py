"""add professional doctor profile fields

Revision ID: 0005_doctor_profile_fields
Revises: 0004_care_consent_clinical_reviews
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_doctor_profile_fields"
down_revision = "0004_care_consent_clinical_reviews"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("specialty", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("license_number", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("facility", sa.String(length=160), nullable=True))


def downgrade():
    op.drop_column("users", "facility")
    op.drop_column("users", "license_number")
    op.drop_column("users", "specialty")
