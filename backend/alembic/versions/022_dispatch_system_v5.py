"""Add dispatch system v5.0 - auto dispatch, trust verification, handoff templates.

New tables: instructor_availabilities, dispatch_records, checkin_records,
completion_confirmations, handoff_templates.
Modified: job_posts, applications, instructor_profiles, handoff_notes.

Revision ID: 022_dispatch_system_v5
Revises: 021_review_application_anchor
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa

revision = "022_dispatch_system_v5"
down_revision = "021_review_application_anchor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # NEW TABLES
    # =========================================================================

    # -- instructor_availabilities ---------------------------------------------
    op.create_table(
        "instructor_availabilities",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "instructor_id",
            sa.CHAR(36),
            sa.ForeignKey("instructor_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_available", sa.Boolean, default=False, nullable=False),
        sa.Column("available_until", sa.DateTime, nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("categories", sa.JSON, default="[]"),
        sa.Column("max_distance_km", sa.Numeric(5, 1), default=10.0, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_availability_spatial",
        "instructor_availabilities",
        ["is_available", "latitude", "longitude"],
    )
    op.create_index(
        "ix_instructor_availabilities_instructor_id",
        "instructor_availabilities",
        ["instructor_id"],
    )
    op.create_index(
        "ix_instructor_availabilities_user_id",
        "instructor_availabilities",
        ["user_id"],
    )

    # -- dispatch_records ------------------------------------------------------
    op.create_table(
        "dispatch_records",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "job_post_id",
            sa.CHAR(36),
            sa.ForeignKey("job_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "instructor_id",
            sa.CHAR(36),
            sa.ForeignKey("instructor_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("wave_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), default="dispatched", nullable=False),
        sa.Column("dispatched_at", sa.DateTime, nullable=False),
        sa.Column("responded_at", sa.DateTime, nullable=True),
        sa.Column("distance_km", sa.Numeric(6, 2), nullable=True),
        sa.Column("matching_score", sa.Integer, nullable=True),
        sa.Column("reliability_score", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_dispatch_job_status",
        "dispatch_records",
        ["job_post_id", "status"],
    )
    op.create_index(
        "ix_dispatch_records_job_post_id",
        "dispatch_records",
        ["job_post_id"],
    )
    op.create_index(
        "ix_dispatch_records_instructor_id",
        "dispatch_records",
        ["instructor_id"],
    )

    # -- checkin_records -------------------------------------------------------
    op.create_table(
        "checkin_records",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "job_post_id",
            sa.CHAR(36),
            sa.ForeignKey("job_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.CHAR(36),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "instructor_user_id",
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("studio_latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("studio_longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("checkin_latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("checkin_longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("distance_meters", sa.Numeric(8, 1), nullable=False),
        sa.Column("is_valid", sa.Boolean, nullable=False),
        sa.Column("checked_in_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_checkin_records_job_post_id",
        "checkin_records",
        ["job_post_id"],
    )
    op.create_index(
        "ix_checkin_records_instructor_user_id",
        "checkin_records",
        ["instructor_user_id"],
    )

    # -- completion_confirmations ----------------------------------------------
    op.create_table(
        "completion_confirmations",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "job_post_id",
            sa.CHAR(36),
            sa.ForeignKey("job_posts.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.CHAR(36),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "studio_user_id",
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "instructor_user_id",
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("studio_confirmed", sa.Boolean, default=False, nullable=False),
        sa.Column("instructor_confirmed", sa.Boolean, default=False, nullable=False),
        sa.Column("studio_confirmed_at", sa.DateTime, nullable=True),
        sa.Column("instructor_confirmed_at", sa.DateTime, nullable=True),
        sa.Column("is_complete", sa.Boolean, default=False, nullable=False),
        sa.Column("auto_completed", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_completion_confirmations_job_post_id",
        "completion_confirmations",
        ["job_post_id"],
    )
    op.create_index(
        "ix_completion_confirmations_application_id",
        "completion_confirmations",
        ["application_id"],
    )

    # -- handoff_templates -----------------------------------------------------
    op.create_table(
        "handoff_templates",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "studio_id",
            sa.CHAR(36),
            sa.ForeignKey("studio_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("class_topic", sa.String(200), nullable=True),
        sa.Column("class_sequence_info", sa.Text, nullable=True),
        sa.Column("atmosphere_preference", sa.String(50), nullable=True),
        sa.Column("member_caution_tags", sa.JSON, default="[]"),
        sa.Column("member_free_text", sa.Text, nullable=True),
        sa.Column("equipment_notes", sa.Text, nullable=True),
        sa.Column("additional_notes", sa.Text, nullable=True),
        sa.Column("usage_count", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_handoff_templates_studio_id",
        "handoff_templates",
        ["studio_id"],
    )

    # =========================================================================
    # MODIFIED TABLES
    # =========================================================================

    # -- job_posts -------------------------------------------------------------
    with op.batch_alter_table("job_posts") as batch_op:
        batch_op.add_column(
            sa.Column("dispatch_mode", sa.String(20), server_default="manual", nullable=False),
        )
        batch_op.add_column(
            sa.Column("urgency_score", sa.Numeric(5, 1), nullable=True),
        )
        batch_op.add_column(
            sa.Column("dispatch_wave", sa.Integer, server_default="0", nullable=False),
        )
        batch_op.add_column(
            sa.Column("dispatch_started_at", sa.DateTime, nullable=True),
        )
        batch_op.add_column(
            sa.Column("auto_accepted_at", sa.DateTime, nullable=True),
        )
        batch_op.add_column(
            sa.Column("matched_instructor_id", sa.CHAR(36), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_job_posts_matched_instructor",
            "instructor_profiles",
            ["matched_instructor_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # -- applications ----------------------------------------------------------
    with op.batch_alter_table("applications") as batch_op:
        batch_op.add_column(
            sa.Column("dispatch_record_id", sa.CHAR(36), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_applications_dispatch_record",
            "dispatch_records",
            ["dispatch_record_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # -- instructor_profiles ---------------------------------------------------
    with op.batch_alter_table("instructor_profiles") as batch_op:
        batch_op.add_column(
            sa.Column("dispatch_success_rate", sa.Numeric(4, 3), server_default="0", nullable=False),
        )
        batch_op.add_column(
            sa.Column("total_dispatches", sa.Integer, server_default="0", nullable=False),
        )
        batch_op.add_column(
            sa.Column("total_dispatch_accepts", sa.Integer, server_default="0", nullable=False),
        )
        batch_op.add_column(
            sa.Column("total_checkins", sa.Integer, server_default="0", nullable=False),
        )
        batch_op.add_column(
            sa.Column("avg_checkin_distance_m", sa.Numeric(8, 1), nullable=True),
        )
        batch_op.add_column(
            sa.Column("total_completions", sa.Integer, server_default="0", nullable=False),
        )

    # -- handoff_notes ---------------------------------------------------------
    with op.batch_alter_table("handoff_notes") as batch_op:
        batch_op.add_column(
            sa.Column("template_id", sa.CHAR(36), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_handoff_notes_template",
            "handoff_templates",
            ["template_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.add_column(
            sa.Column("completeness_score", sa.Numeric(3, 2), server_default="0", nullable=False),
        )
        batch_op.add_column(
            sa.Column("member_caution_tags", sa.JSON, nullable=True),
        )
        batch_op.add_column(
            sa.Column("member_free_text", sa.Text, nullable=True),
        )
        batch_op.add_column(
            sa.Column("instructor_feedback", sa.Text, nullable=True),
        )
        batch_op.add_column(
            sa.Column("instructor_feedback_at", sa.DateTime, nullable=True),
        )


def downgrade() -> None:
    # =========================================================================
    # REVERSE MODIFIED TABLES (reverse order of upgrade)
    # =========================================================================

    # -- handoff_notes ---------------------------------------------------------
    with op.batch_alter_table("handoff_notes") as batch_op:
        batch_op.drop_column("instructor_feedback_at")
        batch_op.drop_column("instructor_feedback")
        batch_op.drop_column("member_free_text")
        batch_op.drop_column("member_caution_tags")
        batch_op.drop_column("completeness_score")
        batch_op.drop_constraint("fk_handoff_notes_template", type_="foreignkey")
        batch_op.drop_column("template_id")

    # -- instructor_profiles ---------------------------------------------------
    with op.batch_alter_table("instructor_profiles") as batch_op:
        batch_op.drop_column("total_completions")
        batch_op.drop_column("avg_checkin_distance_m")
        batch_op.drop_column("total_checkins")
        batch_op.drop_column("total_dispatch_accepts")
        batch_op.drop_column("total_dispatches")
        batch_op.drop_column("dispatch_success_rate")

    # -- applications ----------------------------------------------------------
    with op.batch_alter_table("applications") as batch_op:
        batch_op.drop_constraint("fk_applications_dispatch_record", type_="foreignkey")
        batch_op.drop_column("dispatch_record_id")

    # -- job_posts -------------------------------------------------------------
    with op.batch_alter_table("job_posts") as batch_op:
        batch_op.drop_constraint("fk_job_posts_matched_instructor", type_="foreignkey")
        batch_op.drop_column("matched_instructor_id")
        batch_op.drop_column("auto_accepted_at")
        batch_op.drop_column("dispatch_started_at")
        batch_op.drop_column("dispatch_wave")
        batch_op.drop_column("urgency_score")
        batch_op.drop_column("dispatch_mode")

    # =========================================================================
    # DROP NEW TABLES (reverse order of creation)
    # =========================================================================

    # -- handoff_templates -----------------------------------------------------
    op.drop_index("ix_handoff_templates_studio_id", table_name="handoff_templates")
    op.drop_table("handoff_templates")

    # -- completion_confirmations ----------------------------------------------
    op.drop_index("ix_completion_confirmations_application_id", table_name="completion_confirmations")
    op.drop_index("ix_completion_confirmations_job_post_id", table_name="completion_confirmations")
    op.drop_table("completion_confirmations")

    # -- checkin_records -------------------------------------------------------
    op.drop_index("ix_checkin_records_instructor_user_id", table_name="checkin_records")
    op.drop_index("ix_checkin_records_job_post_id", table_name="checkin_records")
    op.drop_table("checkin_records")

    # -- dispatch_records ------------------------------------------------------
    op.drop_index("ix_dispatch_records_instructor_id", table_name="dispatch_records")
    op.drop_index("ix_dispatch_records_job_post_id", table_name="dispatch_records")
    op.drop_index("ix_dispatch_job_status", table_name="dispatch_records")
    op.drop_table("dispatch_records")

    # -- instructor_availabilities ---------------------------------------------
    op.drop_index("ix_instructor_availabilities_user_id", table_name="instructor_availabilities")
    op.drop_index("ix_instructor_availabilities_instructor_id", table_name="instructor_availabilities")
    op.drop_index("ix_availability_spatial", table_name="instructor_availabilities")
    op.drop_table("instructor_availabilities")
