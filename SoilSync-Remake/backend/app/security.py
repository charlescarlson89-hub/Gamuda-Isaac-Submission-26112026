"""Opaque revocable sessions, CSRF protection, password hashing and rate limits."""

import hashlib
import secrets
from collections import defaultdict, deque
from datetime import timedelta
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AuthSession, User, utcnow

SESSION_COOKIE = "soilsync_session"
CSRF_COOKIE = "soilsync_csrf"
passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def as_utc(value):
    return value.replace(tzinfo=utcnow().tzinfo) if value.tzinfo is None else value


def issue_csrf(request: Request, response: Response):
    value = request.cookies.get(CSRF_COOKIE) or secrets.token_urlsafe(32)
    response.set_cookie(
        CSRF_COOKIE,
        value,
        httponly=False,
        secure=get_settings().cookie_secure,
        samesite="lax",
        max_age=86400,
        path="/",
    )
    return value


def verify_csrf(request: Request):
    origin = request.headers.get("origin", "")
    allowed = get_settings().frontend_origins
    # A browser POST always has an Origin; API clients must supply an allowed Origin too.
    if origin not in allowed:
        raise HTTPException(403, "Request origin is not allowed.")
    cookie = request.cookies.get(CSRF_COOKIE, "")
    header = request.headers.get("x-csrf-token", "")
    if not cookie or not header or not secrets.compare_digest(cookie, header):
        raise HTTPException(403, "Refresh the page and try again.")


def create_session(db, user, response: Response):
    config = get_settings()
    token = secrets.token_urlsafe(48)
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=digest(token),
            expires_at=utcnow() + timedelta(hours=config.session_hours),
        )
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=config.cookie_secure,
        samesite="lax",
        max_age=config.session_hours * 3600,
        path="/",
    )


def require_user(request: Request, db: Annotated[Session, Depends(get_db)]):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(401, "Please log in.")
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == digest(token)))
    if not session or as_utc(session.expires_at) <= utcnow():
        raise HTTPException(401, "Your session has expired. Please log in again.")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Please log in.")
    return user


def require_admin(user: Annotated[User, Depends(require_user)]):
    # Immutable account IDs are configured by the server operator, never by a
    # registration/profile field or a caller-supplied request parameter.
    if user.id not in get_settings().admin_user_ids:
        raise HTTPException(403, "Administrator access is required.")
    return user


class RateLimiter:
    def __init__(self):
        self.events = defaultdict(deque)
        self.lock = Lock()

    def check(self, key, count, seconds=60):
        now = monotonic()
        with self.lock:
            history = self.events[key]
            while history and history[0] <= now - seconds:
                history.popleft()
            if len(history) >= count:
                raise HTTPException(
                    429,
                    "Too many requests. Please try again shortly.",
                    headers={"Retry-After": str(seconds)},
                )
            history.append(now)
            if len(self.events) > 5000:
                self.events = defaultdict(
                    deque, {k: v for k, v in self.events.items() if v and v[-1] > now - 3600}
                )


limiter = RateLimiter()
