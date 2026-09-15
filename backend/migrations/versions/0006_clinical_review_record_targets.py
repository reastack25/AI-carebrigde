"""add clinical review record targets

Revision ID: 0006_clinical_review_record_targets
Revises: 0005_doctor_profile_fields
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_clinical_review_record_targets"
down_revision = "0005_doctor_profile_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("clinical_reviews", sa.Column("record_type", sa.String(length=30), nullable=True))
    op.add_column("clinical_reviews", sa.Column("record_id", sa.Integer(), nullable=True))
    op.create_index("ix_clinical_reviews_record_type", "clinical_reviews", ["record_type"])
    op.create_index("ix_clinical_reviews_record_id", "clinical_reviews", ["record_id"])


def downgrade():
    op.drop_index("ix_clinical_reviews_record_id", table_name="clinical_reviews")
    op.drop_index("ix_clinical_reviews_record_type", table_name="clinical_reviews")
    op.drop_column("clinical_reviews", "record_id")
    op.drop_column("clinical_reviews", "record_type")
