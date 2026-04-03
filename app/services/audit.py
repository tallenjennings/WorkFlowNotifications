from sqlalchemy.orm import Session

from app.models.entities import AuditLog


def write_audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str, details: dict | None = None):
    db.add(
        AuditLog(actor=actor, action=action, entity_type=entity_type, entity_id=str(entity_id), details=details or {})
    )
