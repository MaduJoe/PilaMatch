"""Pivot: urgent substitute matching

- instructor_profiles: add latitude, longitude, completed_substitute_count
- job_posts: add latitude, longitude, is_urgent (indexed)
- applications: add contact_revealed, contact_revealed_at
- reviews: add time_punctuality, professionalism, would_rehire

Revision ID: 015_pivot_urgent_sub
Revises: 014_payment_cancel_webhook
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015_pivot_urgent_sub'
down_revision = '014_payment_cancel_webhook'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- instructor_profiles --------------------------------------------------
    op.add_column(
        'instructor_profiles',
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        'instructor_profiles',
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        'instructor_profiles',
        sa.Column('completed_substitute_count', sa.Integer(), server_default='0', nullable=False),
    )

    # -- job_posts -------------------------------------------------------------
    op.add_column(
        'job_posts',
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        'job_posts',
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        'job_posts',
        sa.Column('is_urgent', sa.Boolean(), server_default='0', nullable=False),
    )
    op.create_index('ix_job_posts_is_urgent', 'job_posts', ['is_urgent'])

    # -- applications ----------------------------------------------------------
    op.add_column(
        'applications',
        sa.Column('contact_revealed', sa.Boolean(), server_default='0', nullable=False),
    )
    op.add_column(
        'applications',
        sa.Column('contact_revealed_at', sa.DateTime(), nullable=True),
    )

    # -- reviews ---------------------------------------------------------------
    op.add_column(
        'reviews',
        sa.Column('time_punctuality', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'reviews',
        sa.Column('professionalism', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'reviews',
        sa.Column('would_rehire', sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    # -- reviews (reverse order) -----------------------------------------------
    op.drop_column('reviews', 'would_rehire')
    op.drop_column('reviews', 'professionalism')
    op.drop_column('reviews', 'time_punctuality')

    # -- applications ----------------------------------------------------------
    op.drop_column('applications', 'contact_revealed_at')
    op.drop_column('applications', 'contact_revealed')

    # -- job_posts -------------------------------------------------------------
    op.drop_index('ix_job_posts_is_urgent', table_name='job_posts')
    op.drop_column('job_posts', 'is_urgent')
    op.drop_column('job_posts', 'longitude')
    op.drop_column('job_posts', 'latitude')

    # -- instructor_profiles ---------------------------------------------------
    op.drop_column('instructor_profiles', 'completed_substitute_count')
    op.drop_column('instructor_profiles', 'longitude')
    op.drop_column('instructor_profiles', 'latitude')
