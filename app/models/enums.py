from enum import Enum


class Role(str, Enum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class RecurrenceType(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"
    custom = "custom"


class OccurrenceStatus(str, Enum):
    pending = "pending"
    due = "due"
    overdue = "overdue"
    completed = "completed"
    skipped = "skipped"
    deferred = "deferred"
    future = "future"


class CompletionSource(str, Enum):
    manual = "manual"
    email_reply = "email_reply"
    system = "system"


class RecipientType(str, Enum):
    primary = "primary"
    escalation = "escalation"
    cc = "cc"
