from datetime import datetime, time

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CompletionSource, OccurrenceStatus, RecipientType, RecurrenceType, Role


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.viewer.value)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkflowDefinition(Base, TimestampMixin):
    __tablename__ = "workflow_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    owner: Mapped[str | None] = mapped_column(String(120), index=True)
    department: Mapped[str | None] = mapped_column(String(120), index=True)
    location: Mapped[str | None] = mapped_column(String(120), index=True)
    instructions: Mapped[str | None] = mapped_column(Text)
    recurrence_type: Mapped[str] = mapped_column(String(20), default=RecurrenceType.monthly.value)
    recurrence_rule: Mapped[dict] = mapped_column(JSON, default=dict)
    due_time: Mapped[time] = mapped_column(Time, default=time(9, 0))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    business_day_policy: Mapped[str] = mapped_column(String(20), default="none")
    completion_method_settings: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    occurrences = relationship("WorkflowOccurrence", back_populates="workflow", cascade="all, delete-orphan")
    recipients = relationship("WorkflowRecipient", back_populates="workflow", cascade="all, delete-orphan")
    reminder_rules = relationship("ReminderRule", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowOccurrence(Base, TimestampMixin):
    __tablename__ = "workflow_occurrences"
    __table_args__ = (UniqueConstraint("workflow_definition_id", "due_at", name="uq_occurrence_due"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_definition_id: Mapped[int] = mapped_column(ForeignKey("workflow_definitions.id"), index=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(20), default=OccurrenceStatus.future.value, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    completion_source: Mapped[str | None] = mapped_column(String(20))
    completion_note: Mapped[str | None] = mapped_column(Text)
    deferred_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workflow = relationship("WorkflowDefinition", back_populates="occurrences")


class Recipient(Base, TimestampMixin):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default=Role.viewer.value)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkflowRecipient(Base, TimestampMixin):
    __tablename__ = "workflow_recipients"
    __table_args__ = (
        UniqueConstraint("workflow_definition_id", "recipient_id", "recipient_type", name="uq_workflow_recipient"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_definition_id: Mapped[int] = mapped_column(ForeignKey("workflow_definitions.id"), index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("recipients.id"), index=True)
    recipient_type: Mapped[str] = mapped_column(String(20), default=RecipientType.primary.value)
    can_complete: Mapped[bool] = mapped_column(Boolean, default=True)

    workflow = relationship("WorkflowDefinition", back_populates="recipients")
    recipient = relationship("Recipient")


class ReminderRule(Base, TimestampMixin):
    __tablename__ = "reminder_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_definition_id: Mapped[int] = mapped_column(ForeignKey("workflow_definitions.id"), index=True)
    offset_type: Mapped[str] = mapped_column(String(20), default="on")
    offset_value: Mapped[int] = mapped_column(Integer, default=0)
    offset_unit: Mapped[str] = mapped_column(String(20), default="days")
    repeat_until_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    repeat_interval_value: Mapped[int | None] = mapped_column(Integer)
    repeat_interval_unit: Mapped[str | None] = mapped_column(String(20))
    escalation_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    workflow = relationship("WorkflowDefinition", back_populates="reminder_rules")


class ReminderSendLog(Base):
    __tablename__ = "reminder_send_logs"
    __table_args__ = (
        UniqueConstraint("workflow_occurrence_id", "reminder_rule_id", "recipient_email", "sent_at", name="uq_send_once"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_occurrence_id: Mapped[int] = mapped_column(ForeignKey("workflow_occurrences.id"), index=True)
    reminder_rule_id: Mapped[int] = mapped_column(ForeignKey("reminder_rules.id"), index=True)
    recipient_email: Mapped[str] = mapped_column(String(255), index=True)
    graph_message_id: Mapped[str | None] = mapped_column(String(255))
    internet_message_id: Mapped[str | None] = mapped_column(String(255))
    conversation_id: Mapped[str | None] = mapped_column(String(255), index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    delivery_status: Mapped[str] = mapped_column(String(30), default="sent")
    error_message: Mapped[str | None] = mapped_column(Text)


class InboundEmailLog(Base):
    __tablename__ = "inbound_email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    graph_message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    internet_message_id: Mapped[str | None] = mapped_column(String(255), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(255), index=True)
    sender_email: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(500))
    body_preview: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_status: Mapped[str] = mapped_column(String(30), default="pending")
    matched_occurrence_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_occurrences.id"))
    parse_result: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_id: Mapped[str] = mapped_column(String(120), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    details: Mapped[dict | None] = mapped_column(JSON)
