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
                WorkflowOccurrence.status.in_(
                    [
                        OccurrenceStatus.pending.value,
                        OccurrenceStatus.due.value,
                        OccurrenceStatus.overdue.value,
                    ]
                )
            )
        ).all()

        for occ in occurrences:
            rules = db.scalars(
                select(ReminderRule).where(ReminderRule.workflow_definition_id == occ.workflow_definition_id)
            ).all()
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
                await self._send_for_rule(db, occ, rule, recips, prevent_duplicates=True)

    async def trigger_occurrence(self, db: Session, occ: WorkflowOccurrence) -> int:
        """Manually trigger reminder emails for an occurrence (for smoke/validation tests)."""
        rules = db.scalars(select(ReminderRule).where(ReminderRule.workflow_definition_id == occ.workflow_definition_id)).all()
        recips = db.scalars(
            select(WorkflowRecipient).where(WorkflowRecipient.workflow_definition_id == occ.workflow_definition_id)
        ).all()

        if not rules:
            pseudo_rule = ReminderRule(
                workflow_definition_id=occ.workflow_definition_id,
                offset_type="on",
                offset_value=0,
                offset_unit="days",
            )
            db.add(pseudo_rule)
            db.flush()
            rules = [pseudo_rule]

        sent_count = 0
        for rule in rules:
            sent_count += await self._send_for_rule(db, occ, rule, recips, prevent_duplicates=False)
        return sent_count

    async def _send_for_rule(
        self,
        db: Session,
        occ: WorkflowOccurrence,
        rule: ReminderRule,
        recips: list[WorkflowRecipient],
        prevent_duplicates: bool,
    ) -> int:
        sent_count = 0
        for wr in recips:
            if wr.recipient_type not in {"primary", "escalation"}:
                continue
            email = wr.recipient.email
            if prevent_duplicates:
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
                f"<p>Task: {occ.workflow.title}</p>"
                f"<p>Due: {occ.due_at.isoformat()}</p>"
                f"<p>Reply DONE/DEFER/SKIP to complete this task.</p>",
            )
            db.add(
                ReminderSendLog(
                    workflow_occurrence_id=occ.id,
                    reminder_rule_id=rule.id,
                    recipient_email=email,
                    delivery_status=payload["delivery_status"],
                    sent_at=datetime.utcnow(),
                )
            )
            write_audit(db, "system", "reminder_sent", "workflow_occurrence", str(occ.id), {"recipient": email})
            sent_count += 1
        return sent_count
