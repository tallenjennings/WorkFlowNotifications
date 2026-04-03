from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import WorkflowDefinition, WorkflowOccurrence
from app.models.enums import OccurrenceStatus
from app.services.audit import write_audit
from app.services.recurrence import RecurrenceEngine


class OccurrenceService:
    def __init__(self):
        self.engine = RecurrenceEngine()

    def generate_for_workflow(self, db: Session, workflow: WorkflowDefinition, horizon_days: int = 90) -> int:
        now_utc = datetime.utcnow()
        due_list = self.engine.generate_due_datetimes(
            workflow.recurrence_type,
            workflow.recurrence_rule,
            workflow.due_time,
            workflow.timezone,
            now_utc.date(),
            horizon_days,
        )
        created = 0
        for due in due_list:
            exists = db.scalar(
                select(WorkflowOccurrence).where(
                    WorkflowOccurrence.workflow_definition_id == workflow.id,
                    WorkflowOccurrence.due_at == due,
                )
            )
            if exists:
                continue
            status = OccurrenceStatus.future.value if due > now_utc else OccurrenceStatus.due.value
            db.add(
                WorkflowOccurrence(
                    workflow_definition_id=workflow.id,
                    due_at=due,
                    status=status,
                )
            )
            created += 1
        write_audit(db, "system", "occurrences_generated", "workflow_definition", str(workflow.id), {"count": created})
        return created
