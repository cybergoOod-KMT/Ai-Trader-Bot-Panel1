from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models import AuditLog, User


def create_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    *,
    actor_user: User | None = None,
    before: dict | None = None,
    after: dict | None = None,
    request: Request | None = None,
) -> AuditLog:
    row = AuditLog(
        actor_user_id=actor_user.id if actor_user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before,
        after_json=after,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
