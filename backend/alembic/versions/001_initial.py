"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table('users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Instructor profiles table
    op.create_table('instructor_profiles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('bio', sa.Text()),
        sa.Column('phone', sa.String(20)),
        sa.Column('profile_image_url', sa.String(500)),
        sa.Column('categories', sa.JSON(), default=[]),
        sa.Column('specialties', sa.JSON(), default=[]),
        sa.Column('certifications', sa.JSON(), default=[]),
        sa.Column('experience_years', sa.Integer(), default=0),
        sa.Column('hourly_rate_min', sa.Numeric(10, 2)),
        sa.Column('hourly_rate_max', sa.Numeric(10, 2)),
        sa.Column('available_regions', sa.JSON(), default=[]),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=True),
        sa.Column('rating_average', sa.Numeric(3, 2), default=0),
        sa.Column('review_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Studio profiles table
    op.create_table('studio_profiles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('business_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', sa.String(500)),
        sa.Column('region', sa.String(100)),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('categories', sa.JSON(), default=[]),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('rating_average', sa.Numeric(3, 2), default=0),
        sa.Column('review_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Job posts table
    op.create_table('job_posts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('studio_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('job_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_sessions', sa.Integer(), default=1),
        sa.Column('required_experience_years', sa.Integer(), default=0),
        sa.Column('required_certifications', sa.JSON(), default=[]),
        sa.Column('region', sa.String(100)),
        sa.Column('address', sa.String(500)),
        sa.Column('application_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['studio_id'], ['studio_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_posts_studio_id', 'job_posts', ['studio_id'])
    op.create_index('ix_job_posts_category', 'job_posts', ['category'])
    op.create_index('ix_job_posts_status', 'job_posts', ['status'])
    op.create_index('ix_job_posts_date', 'job_posts', ['date'])

    # Applications table
    op.create_table('applications',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('job_post_id', sa.String(36), nullable=False),
        sa.Column('instructor_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('cover_letter', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_post_id'], ['job_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructor_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_post_id', 'instructor_id', name='uq_application_job_instructor')
    )
    op.create_index('ix_applications_job_post_id', 'applications', ['job_post_id'])
    op.create_index('ix_applications_instructor_id', 'applications', ['instructor_id'])

    # Offers table
    op.create_table('offers',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('application_id', sa.String(36)),
        sa.Column('studio_id', sa.String(36), nullable=False),
        sa.Column('instructor_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('proposed_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studio_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructor_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id')
    )
    op.create_index('ix_offers_studio_id', 'offers', ['studio_id'])
    op.create_index('ix_offers_instructor_id', 'offers', ['instructor_id'])

    # Contracts table
    op.create_table('contracts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('offer_id', sa.String(36), nullable=False),
        sa.Column('studio_id', sa.String(36), nullable=False),
        sa.Column('instructor_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_sessions', sa.Integer(), default=1),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('cancellation_reason', sa.Text()),
        sa.Column('cancelled_by_user_id', sa.String(36)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['studio_id'], ['studio_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructor_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cancelled_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('offer_id')
    )
    op.create_index('ix_contracts_studio_id', 'contracts', ['studio_id'])
    op.create_index('ix_contracts_instructor_id', 'contracts', ['instructor_id'])
    op.create_index('ix_contracts_status', 'contracts', ['status'])

    # Contract event logs table
    op.create_table('contract_event_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('contract_id', sa.String(36), nullable=False),
        sa.Column('actor_user_id', sa.String(36), nullable=False),
        sa.Column('from_status', sa.String(20)),
        sa.Column('to_status', sa.String(20), nullable=False),
        sa.Column('note', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contract_event_logs_contract_id', 'contract_event_logs', ['contract_id'])

    # Payments table
    op.create_table('payments',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('contract_id', sa.String(36), nullable=False),
        sa.Column('payer_user_id', sa.String(36), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('platform_fee', sa.Numeric(10, 2), default=0),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('payment_key', sa.String(200)),
        sa.Column('order_id', sa.String(200), nullable=False),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('pg_response', sa.JSON()),
        sa.Column('failure_reason', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payer_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_id'),
        sa.UniqueConstraint('payment_key'),
        sa.UniqueConstraint('order_id')
    )
    op.create_index('ix_payments_status', 'payments', ['status'])

    # Payouts table
    op.create_table('payouts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('contract_id', sa.String(36), nullable=False),
        sa.Column('payee_user_id', sa.String(36), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('bank_code', sa.String(10)),
        sa.Column('account_number', sa.String(50)),
        sa.Column('account_holder', sa.String(100)),
        sa.Column('transfer_reference', sa.String(200)),
        sa.Column('failure_reason', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payee_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_id')
    )
    op.create_index('ix_payouts_status', 'payouts', ['status'])

    # Chat threads table
    op.create_table('chat_threads',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('scope', sa.String(20), nullable=False),
        sa.Column('job_post_id', sa.String(36)),
        sa.Column('contract_id', sa.String(36)),
        sa.Column('studio_id', sa.String(36), nullable=False),
        sa.Column('instructor_id', sa.String(36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_post_id'], ['job_posts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['studio_id'], ['studio_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructor_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_id')
    )

    # Chat messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('thread_id', sa.String(36), nullable=False),
        sa.Column('sender_user_id', sa.String(36)),
        sa.Column('message_type', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_thread_id', 'chat_messages', ['thread_id'])

    # Reviews table
    op.create_table('reviews',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('contract_id', sa.String(36), nullable=False),
        sa.Column('reviewer_user_id', sa.String(36), nullable=False),
        sa.Column('reviewee_instructor_id', sa.String(36)),
        sa.Column('reviewee_studio_id', sa.String(36)),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['reviewee_instructor_id'], ['instructor_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewee_studio_id'], ['studio_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_id', 'reviewer_user_id', name='uq_review_contract_reviewer'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating_range')
    )
    op.create_index('ix_reviews_contract_id', 'reviews', ['contract_id'])

    # Reports table
    op.create_table('reports',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('reporter_user_id', sa.String(36), nullable=False),
        sa.Column('reported_user_id', sa.String(36), nullable=False),
        sa.Column('report_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('resolution_note', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reporter_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['reported_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reports_status', 'reports', ['status'])

    # Blocks table
    op.create_table('blocks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('blocker_user_id', sa.String(36), nullable=False),
        sa.Column('blocked_user_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['blocker_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['blocked_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Support tickets table
    op.create_table('support_tickets',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('resolution_note', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_support_tickets_status', 'support_tickets', ['status'])


def downgrade() -> None:
    op.drop_table('support_tickets')
    op.drop_table('blocks')
    op.drop_table('reports')
    op.drop_table('reviews')
    op.drop_table('chat_messages')
    op.drop_table('chat_threads')
    op.drop_table('payouts')
    op.drop_table('payments')
    op.drop_table('contract_event_logs')
    op.drop_table('contracts')
    op.drop_table('offers')
    op.drop_table('applications')
    op.drop_table('job_posts')
    op.drop_table('studio_profiles')
    op.drop_table('instructor_profiles')
    op.drop_table('users')
