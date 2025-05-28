import enum
from typing import Optional

import pydantic

__all__ = [
    "TracingHeaders",
    "Role",
    "AuthorizationContext",
]


class TracingHeaders(pydantic.BaseModel):
    session_id: Optional[str] | None = None
    device_id: Optional[str] | None = None
    token: Optional[str] | None = None


class Role(enum.StrEnum):
    USER = enum.auto()
    ADMIN = enum.auto()


class AuthorizationContext(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        extra="allow",
    )

    user_id: str
    role: Role = Role.USER
    device_id: str | None = None
