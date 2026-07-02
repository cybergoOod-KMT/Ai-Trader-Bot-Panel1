from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    force_password_change: bool
    created_at: datetime
    updated_at: datetime


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: UserResponse | None = None
