"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table("workflow_definitions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("category", sa.String(120)), sa.Column("owner", sa.String(120)), sa.Column("department", sa.String(120)), sa.Column("location", sa.String(120)), sa.Column("instructions", sa.Text()), sa.Column("recurrence_type", sa.String(20), nullable=False), sa.Column("recurrence_rule", sa.JSON(), nullable=False), sa.Column("due_time", sa.Time(), nullable=False), sa.Column("timezone", sa.String(64), nullable=False), sa.Column("business_day_policy", sa.String(20), nullable=False), sa.Column("completion_method_settings", sa.JSON(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_table("recipients", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_index("ix_recipients_email", "recipients", ["email"], unique=True)

    op.create_table("workflow_occurrences", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("workflow_definition_id", sa.Integer(), sa.ForeignKey("workflow_definitions.id")), sa.Column("due_at", sa.DateTime(timezone=True), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("completed_by_user_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("completion_source", sa.String(20)), sa.Column("completion_note", sa.Text()), sa.Column("deferred_until", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_unique_constraint("uq_occurrence_due", "workflow_occurrences", ["workflow_definition_id", "due_at"])

    op.create_table("workflow_recipients", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("workflow_definition_id", sa.Integer(), sa.ForeignKey("workflow_definitions.id")), sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("recipients.id")), sa.Column("recipient_type", sa.String(20), nullable=False), sa.Column("can_complete", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.create_unique_constraint("uq_workflow_recipient", "workflow_recipients", ["workflow_definition_id", "recipient_id", "recipient_type"])

    op.create_table("reminder_rules", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("workflow_definition_id", sa.Integer(), sa.ForeignKey("workflow_definitions.id")), sa.Column("offset_type", sa.String(20), nullable=False), sa.Column("offset_value", sa.Integer(), nullable=False), sa.Column("offset_unit", sa.String(20), nullable=False), sa.Column("repeat_until_completed", sa.Boolean(), nullable=False), sa.Column("repeat_interval_value", sa.Integer()), sa.Column("repeat_interval_unit", sa.String(20)), sa.Column("escalation_enabled", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)))

    op.create_table("reminder_send_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("workflow_occurrence_id", sa.Integer(), sa.ForeignKey("workflow_occurrences.id")), sa.Column("reminder_rule_id", sa.Integer(), sa.ForeignKey("reminder_rules.id")), sa.Column("recipient_email", sa.String(255), nullable=False), sa.Column("graph_message_id", sa.String(255)), sa.Column("internet_message_id", sa.String(255)), sa.Column("conversation_id", sa.String(255)), sa.Column("sent_at", sa.DateTime(timezone=True)), sa.Column("delivery_status", sa.String(30), nullable=False), sa.Column("error_message", sa.Text()))

    op.create_table("inbound_email_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("graph_message_id", sa.String(255), nullable=False), sa.Column("internet_message_id", sa.String(255)), sa.Column("conversation_id", sa.String(255)), sa.Column("sender_email", sa.String(255), nullable=False), sa.Column("subject", sa.String(500), nullable=False), sa.Column("body_preview", sa.Text()), sa.Column("received_at", sa.DateTime(timezone=True)), sa.Column("processed_at", sa.DateTime(timezone=True)), sa.Column("processing_status", sa.String(30), nullable=False), sa.Column("matched_occurrence_id", sa.Integer(), sa.ForeignKey("workflow_occurrences.id")), sa.Column("parse_result", sa.JSON()), sa.Column("error_message", sa.Text()))
    op.create_index("ix_inbound_email_logs_graph_message_id", "inbound_email_logs", ["graph_message_id"], unique=True)

    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("actor", sa.String(255), nullable=False), sa.Column("action", sa.String(120), nullable=False), sa.Column("entity_type", sa.String(120), nullable=False), sa.Column("entity_id", sa.String(120), nullable=False), sa.Column("timestamp", sa.DateTime(timezone=True)), sa.Column("details", sa.JSON()))


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("inbound_email_logs")
    op.drop_table("reminder_send_logs")
    op.drop_table("reminder_rules")
    op.drop_table("workflow_recipients")
    op.drop_table("workflow_occurrences")
    op.drop_table("recipients")
    op.drop_table("workflow_definitions")
    op.drop_table("users")
