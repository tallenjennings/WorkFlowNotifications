from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import ReminderRule, ReminderSendLog, WorkflowOccurrence, WorkflowRecipient
from app.models.enums import OccurrenceStatus
from app.services.audit import write_audit
from app.services.graph import GraphClient


class ReminderService:
    def __init__(self):
        self.graph = GraphClient()

    async def send_due_reminders(self, db: Session):
        now = datetime.utcnow()
        occurrences = db.scalars(
            select(WorkflowOccurrence).where(
                WorkflowOccurrence.status.in_([
                    OccurrenceStatus.pending.value,
                    OccurrenceStatus.due.value,
                    OccurrenceStatus.overdue.value,
                ])
            )
        ).all()

        for occ in occurrences:
            rules = db.scalars(select(ReminderRule).where(ReminderRule.workflow_definition_id == occ.workflow_definition_id)).all()
            recips = db.scalars(
                select(WorkflowRecipient).where(WorkflowRecipient.workflow_definition_id == occ.workflow_definition_id)
            ).all()
            for rule in rules:
                send_time = occ.due_at
                if rule.offset_type == "before":
                    send_time = occ.due_at - timedelta(**{rule.offset_unit: rule.offset_value})
                if rule.offset_type == "after":
                    send_time = occ.due_at + timedelta(**{rule.offset_unit: rule.offset_value})
                if send_time > now:
                    continue
                for wr in recips:
                    if wr.recipient_type not in {"primary", "escalation"}:
                        continue
                    email = wr.recipient.email
                    duplicate = db.scalar(
                        select(ReminderSendLog).where(
                            ReminderSendLog.workflow_occurrence_id == occ.id,
                            ReminderSendLog.reminder_rule_id == rule.id,
                            ReminderSendLog.recipient_email == email,
                        )
                    )
                    if duplicate:
                        continue
                    payload = await self.graph.send_mail(
                        email,
                        f"Reminder: {occ.workflow.title} due {occ.due_at.isoformat()}",
                        f"<p>Task: {occ.workflow.title}</p><p>Reply DONE/DEFER/SKIP.</p>",
                    )
                    db.add(
                        ReminderSendLog(
                            workflow_occurrence_id=occ.id,
                            reminder_rule_id=rule.id,
                            recipient_email=email,
                            delivery_status=payload["delivery_status"],
                        )
                    )
                    write_audit(db, "system", "reminder_sent", "workflow_occurrence", str(occ.id), {"recipient": email})
