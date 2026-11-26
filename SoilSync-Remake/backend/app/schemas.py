"""Request validation. Extra fields cannot mutate server-owned balances/status."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AdminUserSummary(BaseModel):
    id: int
    username: str


class AdminUserList(BaseModel):
    users: list[AdminUserSummary]
    total: int
    offset: int
    limit: int
    has_more: bool


class Registration(Input):
    username: str = Field(min_length=3, max_length=40)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: SecretStr
    location: str = Field(min_length=1, max_length=80)
    accepted_terms: bool

    @field_validator("password")
    @classmethod
    def valid_password(cls, value):
        if not 12 <= len(value.get_secret_value()) <= 128:
            raise ValueError("Use a password between 12 and 128 characters.")
        return value

    @field_validator("accepted_terms")
    @classmethod
    def consent_required(cls, value):
        if not value:
            raise ValueError("Read and accept the terms and data-use notice before registration.")
        return value


class Login(Input):
    identifier: str = Field(min_length=1, max_length=254)
    password: SecretStr

    @field_validator("password")
    @classmethod
    def bounded_password(cls, value):
        if not 1 <= len(value.get_secret_value()) <= 128:
            raise ValueError("Enter your password.")
        return value


class ProfileUpdate(Input):
    username: str = Field(min_length=3, max_length=40)
    location: str = Field(min_length=1, max_length=80)


class SettingsUpdate(Input):
    checkin_reminder: bool | None = None
    reward_received_notify: bool | None = None
    service_notices_notify: bool | None = None
    claim_reward_reminder: bool | None = None
    quiet_hours_start: str | None = Field(
        default=None, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$"
    )
    quiet_hours_end: str | None = Field(default=None, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")


class GeminiKeyInput(Input):
    api_key: SecretStr

    @field_validator("api_key")
    @classmethod
    def valid_api_key(cls, value):
        key = value.get_secret_value().strip()
        if not 20 <= len(key) <= 256 or any(c.isspace() for c in key):
            raise ValueError("Enter a Gemini API key without spaces.")
        return SecretStr(key)


class BatchCreate(Input):
    name: str = Field(min_length=1, max_length=60)
    fertilizer_type_id: int = Field(gt=0)
    client_request_id: UUID


class ClaimCreate(Input):
    request_id: UUID


class Detection(Input):
    waste_type_id: int | None = Field(
        default=None, description="An ID from the supplied catalogue, or null if unknown."
    )
    detected_name: str = Field(min_length=1, max_length=100)
    confidence: float = Field(
        ge=0, le=1, description="Uncalibrated model estimate; not a nutrient concentration."
    )


class VisionResult(Input):
    items: list[Detection] = Field(max_length=12)
    explanation: str = Field(max_length=600)


class CompostVerification(Input):
    verdict: Literal["compost", "not_compost", "uncertain"]
    confidence: float = Field(ge=0, le=1, description="Uncalibrated visual estimate.")
    reason: str = Field(min_length=1, max_length=600)


class ChatInput(Input):
    question: str = Field(min_length=1, max_length=1000)
