from sqlalchemy import select

from app.auth.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Recipient, ReminderRule, User, WorkflowDefinition, WorkflowRecipient
from app.services.occurrences import OccurrenceService


def run():
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.email == "admin@example.com")):
            db.add(User(name="Admin", email="admin@example.com", password_hash=hash_password("admin123"), role="admin"))

        r1 = db.scalar(select(Recipient).where(Recipient.email == "finance@example.com"))
        if not r1:
            r1 = Recipient(name="Finance Team", email="finance@example.com", role="manager")
            db.add(r1)
            db.flush()

        wf = db.scalar(select(WorkflowDefinition).where(WorkflowDefinition.title == "Submit subsidy details"))
        if not wf:
            wf = WorkflowDefinition(
                title="Submit subsidy details",
                description="Submit subsidy details on the 1st of each month",
                category="Subsidy",
                owner="Finance Manager",
                department="Finance",
                recurrence_type="monthly",
                recurrence_rule={"day_of_month": 1},
            )
            db.add(wf)
            db.flush()
            db.add(WorkflowRecipient(workflow_definition_id=wf.id, recipient_id=r1.id, recipient_type="primary", can_complete=True))
            db.add(ReminderRule(workflow_definition_id=wf.id, offset_type="on", offset_value=0, offset_unit="days"))
            OccurrenceService().generate_for_workflow(db, wf)

        db.commit()


if __name__ == "__main__":
    run()
