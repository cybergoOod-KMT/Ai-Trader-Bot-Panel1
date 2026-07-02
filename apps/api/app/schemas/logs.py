from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SystemLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: str
    source: str
    message: str
    metadata_json: dict | None
    created_at: datetime
