from datetime import datetime
from io import StringIO
import csv

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import WorkflowDefinition, WorkflowOccurrence
from app.models.enums import CompletionSource, OccurrenceStatus
from app.services.occurrences import OccurrenceService
from app.services.reporting import query_occurrences

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    due_today = db.scalars(select(WorkflowOccurrence).where(WorkflowOccurrence.due_at <= now)).all()
    overdue = db.scalars(select(WorkflowOccurrence).where(WorkflowOccurrence.status == OccurrenceStatus.overdue.value)).all()
    recent = db.scalars(
        select(WorkflowOccurrence).where(WorkflowOccurrence.status == OccurrenceStatus.completed.value)
    ).all()[-10:]
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "due_today": due_today, "overdue": overdue, "recent": recent},
    )


@router.get("/workflows", response_class=HTMLResponse)
def list_workflows(request: Request, db: Session = Depends(get_db)):
    workflows = db.scalars(select(WorkflowDefinition).order_by(WorkflowDefinition.title)).all()
    return templates.TemplateResponse("workflows.html", {"request": request, "workflows": workflows})


@router.post("/workflows")
def create_workflow(
    title: str = Form(...),
    recurrence_type: str = Form("monthly"),
    timezone: str = Form("UTC"),
    db: Session = Depends(get_db),
):
    workflow = WorkflowDefinition(title=title, recurrence_type=recurrence_type, timezone=timezone)
    db.add(workflow)
    db.flush()
    OccurrenceService().generate_for_workflow(db, workflow)
    db.commit()
    return RedirectResponse("/workflows", status_code=303)


@router.post("/occurrences/{occ_id}/status")
def update_status(occ_id: int, status: str = Form(...), note: str = Form(""), db: Session = Depends(get_db)):
    occ = db.get(WorkflowOccurrence, occ_id)
    if not occ:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    occ.status = status
    occ.completion_source = CompletionSource.manual.value
    occ.completion_note = note
    if status == OccurrenceStatus.completed.value:
        occ.completed_at = datetime.utcnow()
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.get("/reports", response_class=HTMLResponse)
def reports(request: Request, status: str | None = None, db: Session = Depends(get_db)):
    items = query_occurrences(db, status=status)
    return templates.TemplateResponse("reports.html", {"request": request, "items": items})


@router.get("/reports.csv")
def reports_csv(status: str | None = None, db: Session = Depends(get_db)):
    items = query_occurrences(db, status=status)
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(["id", "workflow", "due_at", "status", "completed_at", "completion_note"])
    for x in items:
        writer.writerow([x.id, x.workflow_definition_id, x.due_at.isoformat(), x.status, x.completed_at, x.completion_note])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv")
