from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    severity: str
    title: str
    message: str
    is_read: bool
    metadata_json: dict | None
    created_at: datetime
