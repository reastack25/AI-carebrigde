"""add consent and clinical reviews

Revision ID: 0004_care_consent_clinical_reviews
Revises: 0003_medications
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_care_consent_clinical_reviews"
down_revision = "0003_medications"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "care_consents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_care_consents_patient_id", "care_consents", ["patient_id"])
    op.create_index("ix_care_consents_doctor_id", "care_consents", ["doctor_id"])

    op.create_table(
        "clinical_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_clinical_reviews_patient_id", "clinical_reviews", ["patient_id"])
    op.create_index("ix_clinical_reviews_doctor_id", "clinical_reviews", ["doctor_id"])
    op.create_index("ix_clinical_reviews_created_at", "clinical_reviews", ["created_at"])


def downgrade():
    op.drop_index("ix_clinical_reviews_created_at", table_name="clinical_reviews")
    op.drop_index("ix_clinical_reviews_doctor_id", table_name="clinical_reviews")
    op.drop_index("ix_clinical_reviews_patient_id", table_name="clinical_reviews")
    op.drop_table("clinical_reviews")
    op.drop_index("ix_care_consents_doctor_id", table_name="care_consents")
    op.drop_index("ix_care_consents_patient_id", table_name="care_consents")
    op.drop_table("care_consents")
