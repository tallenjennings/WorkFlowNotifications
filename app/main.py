from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sqlalchemy import select

from app.api.routes import router
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import WorkflowDefinition
from app.services.occurrences import OccurrenceService
from app.services.reminders import ReminderService
from app.services.reply_processing import ReplyProcessingService

scheduler = AsyncIOScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(generate_occurrences_job, "interval", hours=6, id="generate_occurrences", replace_existing=True)
    scheduler.add_job(send_reminders_job, "interval", minutes=15, id="send_reminders", replace_existing=True)
    scheduler.add_job(
        poll_replies_job,
        "interval",
        seconds=settings.poll_interval_seconds,
        id="poll_replies",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router)


def generate_occurrences_job():
    with SessionLocal() as db:
        svc = OccurrenceService()
        workflows = db.scalars(select(WorkflowDefinition).where(WorkflowDefinition.active == True)).all()
        for workflow in workflows:
            svc.generate_for_workflow(db, workflow, settings.occurrence_horizon_days)
        db.commit()


async def send_reminders_job():
    with SessionLocal() as db:
        await ReminderService().send_due_reminders(db)
        db.commit()


async def poll_replies_job():
    with SessionLocal() as db:
        await ReplyProcessingService().poll_and_process(db)
        db.commit()
