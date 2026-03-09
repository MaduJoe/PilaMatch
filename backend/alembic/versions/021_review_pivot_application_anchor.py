"""Pivot reviews from contract_id to application_id anchor.

- reviews: add application_id FK, make contract_id nullable
- reviews: replace unique constraint

Revision ID: 021_review_application_anchor
Revises: 020_backup_instructors
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision = "021_review_application_anchor"
down_revision = "020_backup_instructors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("reviews") as batch_op:
        # Add application_id FK
        batch_op.add_column(
            sa.Column("application_id", sa.CHAR(36), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_review_application",
            "applications",
            ["application_id"],
            ["id"],
            ondelete="CASCADE",
        )
        # Make contract_id nullable
        batch_op.alter_column("contract_id", existing_type=sa.CHAR(36), nullable=True)
        # Drop old unique constraint, add new one
        batch_op.drop_constraint("uq_review_contract_reviewer", type_="unique")
        batch_op.create_unique_constraint(
            "uq_review_application_reviewer",
            ["application_id", "reviewer_user_id"],
        )

    op.create_index("ix_reviews_application_id", "reviews", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_reviews_application_id", table_name="reviews")

    with op.batch_alter_table("reviews") as batch_op:
        batch_op.drop_constraint("uq_review_application_reviewer", type_="unique")
        batch_op.create_unique_constraint(
            "uq_review_contract_reviewer",
            ["contract_id", "reviewer_user_id"],
        )
        batch_op.alter_column("contract_id", existing_type=sa.CHAR(36), nullable=False)
        batch_op.drop_constraint("fk_review_application", type_="foreignkey")
        batch_op.drop_column("application_id")
