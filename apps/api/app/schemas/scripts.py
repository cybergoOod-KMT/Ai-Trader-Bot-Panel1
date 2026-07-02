from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScriptFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    relative_path: str
    enabled: bool
    detected_at: datetime
    created_at: datetime
    updated_at: datetime


class ScriptFileUpdateRequest(BaseModel):
    enabled: bool


class ScriptRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    script_file_id: int
    status: str
    pid: int | None
    started_at: datetime
    stopped_at: datetime | None
    exit_code: int | None
    error_message: str | None


class ScriptLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    script_run_id: int
    stream: str
    line: str
    created_at: datetime


class ScriptInputRequest(BaseModel):
    value: str = Field(min_length=1, max_length=1000)
