from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiAccountBase(BaseModel):
    name: str
    openai_model: str
    is_active: bool = False
    read_only: bool = True
    real_trading_allowed: bool = False


class ApiAccountCreate(ApiAccountBase):
    tabdeal_api_key: str | None = None
    tabdeal_api_secret: str | None = None
    openai_api_key: str | None = None


class ApiAccountUpdate(BaseModel):
    name: str | None = None
    tabdeal_api_key: str | None = None
    tabdeal_api_secret: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    is_active: bool | None = None
    read_only: bool | None = None
    real_trading_allowed: bool | None = None


class ApiAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    openai_model: str
    is_active: bool
    read_only: bool
    real_trading_allowed: bool
    has_tabdeal_api_key: bool
    tabdeal_api_key_masked: str | None
    has_tabdeal_api_secret: bool
    tabdeal_api_secret_masked: str | None
    has_openai_api_key: bool
    openai_api_key_masked: str | None
    created_at: datetime
    updated_at: datetime


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    details: dict | None = None
