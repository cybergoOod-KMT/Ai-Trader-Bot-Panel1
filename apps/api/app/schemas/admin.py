from datetime import datetime

from pydantic import BaseModel


class GenericSettingsPayload(BaseModel):
    value: dict


class GenericSettingsResponse(BaseModel):
    key: str
    value: dict


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    before_json: dict | None
    after_json: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class LearningMemoryResponse(BaseModel):
    id: int
    symbol: str
    strategy_name: str
    stats_json: dict
    lessons_json: dict
    updated_at: datetime


class TradeOutcomeResponse(BaseModel):
    id: int
    symbol: str
    strategy_name: str
    ai_engine: str | None
    entry_snapshot_json: dict
    decision_json: dict
    exit_reason: str
    pnl: str
    pnl_pct: str
    duration_seconds: int
    was_successful: bool
    created_at: datetime


class BackupResponse(BaseModel):
    id: str
    files: list[str]
    created_at: str


class EmergencyConfirmRequest(BaseModel):
    confirm_token: str
