from datetime import datetime, time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.entities import Recipient, ReminderRule, WorkflowDefinition, WorkflowOccurrence, WorkflowRecipient
from app.services.reminders import ReminderService


class FakeGraph:
    async def send_mail(self, to_email: str, subject: str, html_body: str):
        return {"delivery_status": "sent"}


def test_manual_trigger_sends_log():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        wf = WorkflowDefinition(
            title="Smoke Task",
            recurrence_type="monthly",
            recurrence_rule={"day_of_month": 1},
            due_time=time(9, 0),
            timezone="UTC",
        )
        db.add(wf)
        db.flush()

        recipient = Recipient(name="R", email="r@example.com", role="manager")
        db.add(recipient)
        db.flush()

        db.add(
            WorkflowRecipient(
                workflow_definition_id=wf.id,
                recipient_id=recipient.id,
                recipient_type="primary",
                can_complete=True,
            )
        )
        db.add(
            ReminderRule(
                workflow_definition_id=wf.id,
                offset_type="on",
                offset_value=0,
                offset_unit="days",
            )
        )
        occ = WorkflowOccurrence(workflow_definition_id=wf.id, due_at=datetime.utcnow(), status="due")
        db.add(occ)
        db.commit()

        svc = ReminderService()
        svc.graph = FakeGraph()

        sent = __import__("asyncio").run(svc.trigger_occurrence(db, occ))
        db.commit()

        assert sent == 1
