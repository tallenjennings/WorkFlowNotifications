from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.entities import WorkflowOccurrence


def query_occurrences(
    db: Session,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    stmt = select(WorkflowOccurrence)
    filters = []
    if status:
        filters.append(WorkflowOccurrence.status == status)
    if date_from:
        filters.append(WorkflowOccurrence.due_at >= date_from)
    if date_to:
        filters.append(WorkflowOccurrence.due_at <= date_to)
    if filters:
        stmt = stmt.where(and_(*filters))
    return db.scalars(stmt.order_by(WorkflowOccurrence.due_at.asc())).all()
