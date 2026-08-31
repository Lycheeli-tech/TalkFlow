from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuthenticatedUser(BaseModel):
    id: UUID
    email: str | None = None


class UserState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interface_language: Literal["en", "zh-CN"] = "en"
    support_language: Literal["en", "zh-CN"] = "en"
    default_session_length: Literal[10, 20, 30, 60] = 20
    coaching_style: Literal["supportive", "professional", "strict"] = "supportive"
    timezone: str = "UTC"


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["fluentloop-api"] = "fluentloop-api"
    version: str
