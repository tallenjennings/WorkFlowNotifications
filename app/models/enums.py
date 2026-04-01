from enum import StrEnum


class Role(StrEnum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class RecurrenceType(StrEnum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"
    custom = "custom"


class OccurrenceStatus(StrEnum):
    pending = "pending"
    due = "due"
    overdue = "overdue"
    completed = "completed"
    skipped = "skipped"
    deferred = "deferred"
    future = "future"


class CompletionSource(StrEnum):
    manual = "manual"
    email_reply = "email_reply"
    system = "system"


class RecipientType(StrEnum):
    primary = "primary"
    escalation = "escalation"
    cc = "cc"
