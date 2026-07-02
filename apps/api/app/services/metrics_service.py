from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AuditLog, ManualOrder, Position, SystemLog


class MetricsService:
    def render_prometheus(self, db: Session) -> str:
        settings = get_settings()
        since = datetime.now(tz=UTC) - timedelta(minutes=settings.metrics_window_minutes)
        total_orders = len(db.scalars(select(ManualOrder).where(ManualOrder.created_at >= since)).all())
        open_positions = len(db.scalars(select(Position).where(Position.status == "OPEN")).all())
        error_logs = len(db.scalars(select(SystemLog).where(SystemLog.level == "ERROR", SystemLog.created_at >= since)).all())
        audit_rows = len(db.scalars(select(AuditLog).where(AuditLog.created_at >= since)).all())
        lines = [
            "# HELP panel_orders_total Orders created in the active metrics window",
            "# TYPE panel_orders_total gauge",
            f"panel_orders_total {total_orders}",
            "# HELP panel_open_positions Current open positions",
            "# TYPE panel_open_positions gauge",
            f"panel_open_positions {open_positions}",
            "# HELP panel_error_logs_total Error logs in the active metrics window",
            "# TYPE panel_error_logs_total gauge",
            f"panel_error_logs_total {error_logs}",
            "# HELP panel_audit_events_total Audit events in the active metrics window",
            "# TYPE panel_audit_events_total gauge",
            f"panel_audit_events_total {audit_rows}",
        ]
        return "\n".join(lines) + "\n"


metrics_service = MetricsService()
