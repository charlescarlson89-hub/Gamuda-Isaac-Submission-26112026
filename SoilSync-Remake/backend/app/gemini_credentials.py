"""Keep Gemini credentials encrypted at rest and scoped to one account and request."""

from contextlib import contextmanager
from contextvars import ContextVar

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from pydantic import SecretStr

from app.config import get_settings
from app.models import GeminiCredential

_active_key: ContextVar[SecretStr | None] = ContextVar("gemini_personal_key", default=None)
MISSING_KEY = "Sign in with a TedaByte account and add a Gemini API key in Profile."


def can_manage(user_id):
    settings = get_settings()
    return (
        settings.gemini_demo_user_id is None
        and user_id in settings.gemini_personal_key_user_ids
        and bool(settings.gemini_personal_key_encryption.get_secret_value())
    )


def _cipher():
    try:
        return Fernet(get_settings().gemini_personal_key_encryption.get_secret_value())
    except ValueError as error:
        raise HTTPException(503, "Personal Gemini keys are temporarily unavailable.") from error


def encrypt(user_id, value):
    return _cipher().encrypt(f"{user_id}:{value}".encode())


@contextmanager
def use_account_key(db, user_id):
    settings = get_settings()
    demo_user_id = settings.gemini_demo_user_id
    if demo_user_id is not None and user_id != demo_user_id:
        raise HTTPException(403, "Live AI is reserved for the SoilSync demo account.")
    credential = db.get(GeminiCredential, user_id) if can_manage(user_id) else None
    key = None
    if credential is not None:
        try:
            owner, value = _cipher().decrypt(credential.encrypted_key).decode().split(":", 1)
            if owner != str(user_id) or not value:
                raise ValueError("Invalid account credential")
        except (InvalidToken, ValueError) as error:
            raise HTTPException(503, "Your Gemini key could not be read. Replace it in Profile.") from error
        key = SecretStr(value)
    if key is None and settings.gemini_require_personal_key and demo_user_id is None:
        raise HTTPException(503, MISSING_KEY)
    token = _active_key.set(key)
    try:
        yield
    finally:
        _active_key.reset(token)


def active_key():
    return _active_key.get()
