from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import InboundEmailLog, ReminderSendLog, WorkflowOccurrence, WorkflowRecipient
from app.models.enums import CompletionSource, OccurrenceStatus
from app.services.audit import write_audit
from app.services.graph import GraphClient
from app.services.reply_parser import ReplyParser


class ReplyProcessingService:
    def __init__(self):
        self.graph = GraphClient()
        self.parser = ReplyParser()

    async def poll_and_process(self, db: Session):
        messages = await self.graph.fetch_inbound()
        for m in messages:
            graph_id = m["id"]
            existing = db.scalar(select(InboundEmailLog).where(InboundEmailLog.graph_message_id == graph_id))
            if existing:
                continue

            sender = (m.get("from") or {}).get("emailAddress", {}).get("address", "").lower()
            subject = m.get("subject", "")
            body_preview = m.get("bodyPreview", "")
            log = InboundEmailLog(
                graph_message_id=graph_id,
                internet_message_id=m.get("internetMessageId"),
                conversation_id=m.get("conversationId"),
                sender_email=sender,
                subject=subject,
                body_preview=body_preview,
                received_at=datetime.fromisoformat(m["receivedDateTime"].replace("Z", "+00:00"))
                if m.get("receivedDateTime")
                else datetime.utcnow(),
            )
            db.add(log)

            parse = self.parser.parse(subject, body_preview)
            log.parse_result = {"command": parse.command, "note": parse.note, "ambiguous": parse.ambiguous}
            if parse.ignored:
                log.processing_status = "ignored"
                continue

            send_log = db.scalar(
                select(ReminderSendLog).where(ReminderSendLog.conversation_id == m.get("conversationId"))
            )
            if not send_log:
                log.processing_status = "unmatched"
                continue

            occ = db.get(WorkflowOccurrence, send_log.workflow_occurrence_id)
            authorized = db.scalar(
                select(WorkflowRecipient).where(
                    WorkflowRecipient.workflow_definition_id == occ.workflow_definition_id,
                    WorkflowRecipient.can_complete == True,
                    WorkflowRecipient.recipient.has(email=sender),
                )
            )
            if not authorized:
                log.processing_status = "unauthorized"
                continue

            log.matched_occurrence_id = occ.id
            if parse.command == "complete":
                occ.status = OccurrenceStatus.completed.value
                occ.completed_at = datetime.utcnow()
                occ.completion_source = CompletionSource.email_reply.value
                occ.completion_note = parse.note
                log.processing_status = "completed"
            elif parse.command == "skip":
                occ.status = OccurrenceStatus.skipped.value
                occ.completion_source = CompletionSource.email_reply.value
                occ.completion_note = parse.note
                log.processing_status = "skipped"
            elif parse.command == "defer":
                occ.status = OccurrenceStatus.deferred.value
                occ.completion_source = CompletionSource.email_reply.value
                occ.completion_note = parse.note
                log.processing_status = "deferred"
            else:
                log.processing_status = "ambiguous"

            log.processed_at = datetime.utcnow()
            write_audit(db, "email:" + sender, "reply_processed", "workflow_occurrence", str(occ.id), log.parse_result)
