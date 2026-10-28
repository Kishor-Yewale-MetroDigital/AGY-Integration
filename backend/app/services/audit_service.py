from datetime import date, datetime
from decimal import Decimal
from typing import Any
from sqlalchemy.orm import Session

from app.models.entities import AuditEvent, Notification, User


def _json_safe(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if data is None:
        return None
    cleaned: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, Decimal):
            cleaned[k] = str(v)
        elif isinstance(v, (date, datetime)):
            cleaned[k] = v.isoformat()
        else:
            cleaned[k] = v
    return cleaned


def record_audit_event(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    actor: User,
    action: str,
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor.id,
        actor_role=actor.role,
        action=action,
        previous_state=_json_safe(previous_state),
        new_state=_json_safe(new_state),
    )
    db.add(event)
    return event


def emit_notification(
    db: Session,
    *,
    recipient_role: str,
    hiring_request_id: str,
    event_type: str,
    message: str,
    recipient_user_id: str | None = None,
) -> Notification:
    notif = Notification(
        recipient_user_id=recipient_user_id,
        recipient_role=recipient_role,
        hiring_request_id=hiring_request_id,
        event_type=event_type,
        message=message,
    )
    db.add(notif)
    return notif
