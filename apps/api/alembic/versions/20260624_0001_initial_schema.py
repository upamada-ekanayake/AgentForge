"""create initial AgentForge schema

Revision ID: 20260624_0001
Revises:
Create Date: 2026-06-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260624_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


workspace_role = postgresql.ENUM(
    "owner",
    "admin",
    "member",
    name="workspace_role",
    create_type=False,
)
document_status = postgresql.ENUM(
    "uploaded",
    "processing",
    "ready",
    "failed",
    name="document_status",
    create_type=False,
)
application_status = postgresql.ENUM(
    "draft",
    "matched",
    "applied",
    "interviewing",
    "offered",
    "rejected",
    "withdrawn",
    name="application_status",
    create_type=False,
)
agent_run_status = postgresql.ENUM(
    "pending",
    "running",
    "succeeded",
    "failed",
    "canceled",
    name="agent_run_status",
    create_type=False,
)
agent_step_status = postgresql.ENUM(
    "pending",
    "running",
    "succeeded",
    "failed",
    "skipped",
    name="agent_step_status",
    create_type=False,
)
agent_log_level = postgresql.ENUM(
    "debug",
    "info",
    "warning",
    "error",
    name="agent_log_level",
    create_type=False,
)


def id_column() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )


def timestamp_columns() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    bind = op.get_bind()
    workspace_role.create(bind, checkfirst=True)
    document_status.create(bind, checkfirst=True)
    application_status.create(bind, checkfirst=True)
    agent_run_status.create(bind, checkfirst=True)
    agent_step_status.create(bind, checkfirst=True)
    agent_log_level.create(bind, checkfirst=True)

    op.create_table(
        "users",
        id_column(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "workspaces",
        id_column(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspaces_name"), "workspaces", ["name"])
    op.create_index(op.f("ix_workspaces_owner_id"), "workspaces", ["owner_id"])

    op.create_table(
        "workspace_members",
        id_column(),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            workspace_role,
            nullable=False,
        ),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_members_user",
        ),
    )
    op.create_index(
        op.f("ix_workspace_members_user_id"),
        "workspace_members",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_workspace_members_workspace_id"),
        "workspace_members",
        ["workspace_id"],
    )

    op.create_table(
        "documents",
        id_column(),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", document_status, nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_user_id"), "documents", ["user_id"])
    op.create_index(
        op.f("ix_documents_workspace_id"),
        "documents",
        ["workspace_id"],
    )

    op.create_table(
        "internship_posts",
        id_column(),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_internship_posts_company_name"),
        "internship_posts",
        ["company_name"],
    )
    op.create_index(
        op.f("ix_internship_posts_created_by_id"),
        "internship_posts",
        ["created_by_id"],
    )
    op.create_index(
        op.f("ix_internship_posts_title"),
        "internship_posts",
        ["title"],
    )
    op.create_index(
        op.f("ix_internship_posts_workspace_id"),
        "internship_posts",
        ["workspace_id"],
    )

    op.create_table(
        "document_chunks",
        id_column(),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("qdrant_point_id", sa.String(length=255), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_order",
        ),
    )
    op.create_index(
        op.f("ix_document_chunks_document_id"),
        "document_chunks",
        ["document_id"],
    )
    op.create_index(
        op.f("ix_document_chunks_qdrant_point_id"),
        "document_chunks",
        ["qdrant_point_id"],
    )

    op.create_table(
        "applications",
        id_column(),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("internship_post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", application_status, nullable=False),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["internship_post_id"],
            ["internship_posts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "user_id",
            "internship_post_id",
            name="uq_applications_workspace_user_post",
        ),
    )
    op.create_index(
        op.f("ix_applications_document_id"),
        "applications",
        ["document_id"],
    )
    op.create_index(
        op.f("ix_applications_internship_post_id"),
        "applications",
        ["internship_post_id"],
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"])
    op.create_index(
        op.f("ix_applications_workspace_id"),
        "applications",
        ["workspace_id"],
    )

    op.create_table(
        "agent_runs",
        id_column(),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_type", sa.String(length=120), nullable=False),
        sa.Column("status", agent_run_status, nullable=False),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_runs_application_id"),
        "agent_runs",
        ["application_id"],
    )
    op.create_index(op.f("ix_agent_runs_run_type"), "agent_runs", ["run_type"])
    op.create_index(op.f("ix_agent_runs_status"), "agent_runs", ["status"])
    op.create_index(op.f("ix_agent_runs_user_id"), "agent_runs", ["user_id"])
    op.create_index(
        op.f("ix_agent_runs_workspace_id"),
        "agent_runs",
        ["workspace_id"],
    )

    op.create_table(
        "agent_steps",
        id_column(),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=False),
        sa.Column("status", agent_step_status, nullable=False),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["agent_run_id"],
            ["agent_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_run_id", "step_order", name="uq_agent_steps_order"),
    )
    op.create_index(
        op.f("ix_agent_steps_agent_name"),
        "agent_steps",
        ["agent_name"],
    )
    op.create_index(
        op.f("ix_agent_steps_agent_run_id"),
        "agent_steps",
        ["agent_run_id"],
    )
    op.create_index(op.f("ix_agent_steps_status"), "agent_steps", ["status"])

    op.create_table(
        "agent_logs",
        id_column(),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("level", agent_log_level, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(
            ["agent_run_id"],
            ["agent_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_step_id"],
            ["agent_steps.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_logs_agent_run_id"),
        "agent_logs",
        ["agent_run_id"],
    )
    op.create_index(
        op.f("ix_agent_logs_agent_step_id"),
        "agent_logs",
        ["agent_step_id"],
    )
    op.create_index(op.f("ix_agent_logs_level"), "agent_logs", ["level"])


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_logs_level"), table_name="agent_logs")
    op.drop_index(op.f("ix_agent_logs_agent_step_id"), table_name="agent_logs")
    op.drop_index(op.f("ix_agent_logs_agent_run_id"), table_name="agent_logs")
    op.drop_table("agent_logs")

    op.drop_index(op.f("ix_agent_steps_status"), table_name="agent_steps")
    op.drop_index(op.f("ix_agent_steps_agent_run_id"), table_name="agent_steps")
    op.drop_index(op.f("ix_agent_steps_agent_name"), table_name="agent_steps")
    op.drop_table("agent_steps")

    op.drop_index(op.f("ix_agent_runs_workspace_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_user_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_status"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_run_type"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_application_id"), table_name="agent_runs")
    op.drop_table("agent_runs")

    op.drop_index(op.f("ix_applications_workspace_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_user_id"), table_name="applications")
    op.drop_index(
        op.f("ix_applications_internship_post_id"),
        table_name="applications",
    )
    op.drop_index(op.f("ix_applications_document_id"), table_name="applications")
    op.drop_table("applications")

    op.drop_index(
        op.f("ix_document_chunks_qdrant_point_id"),
        table_name="document_chunks",
    )
    op.drop_index(
        op.f("ix_document_chunks_document_id"),
        table_name="document_chunks",
    )
    op.drop_table("document_chunks")

    op.drop_index(
        op.f("ix_internship_posts_workspace_id"),
        table_name="internship_posts",
    )
    op.drop_index(op.f("ix_internship_posts_title"), table_name="internship_posts")
    op.drop_index(
        op.f("ix_internship_posts_created_by_id"),
        table_name="internship_posts",
    )
    op.drop_index(
        op.f("ix_internship_posts_company_name"),
        table_name="internship_posts",
    )
    op.drop_table("internship_posts")

    op.drop_index(op.f("ix_documents_workspace_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_user_id"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(
        op.f("ix_workspace_members_workspace_id"),
        table_name="workspace_members",
    )
    op.drop_index(op.f("ix_workspace_members_user_id"), table_name="workspace_members")
    op.drop_table("workspace_members")

    op.drop_index(op.f("ix_workspaces_owner_id"), table_name="workspaces")
    op.drop_index(op.f("ix_workspaces_name"), table_name="workspaces")
    op.drop_table("workspaces")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    agent_log_level.drop(bind, checkfirst=True)
    agent_step_status.drop(bind, checkfirst=True)
    agent_run_status.drop(bind, checkfirst=True)
    application_status.drop(bind, checkfirst=True)
    document_status.drop(bind, checkfirst=True)
    workspace_role.drop(bind, checkfirst=True)
