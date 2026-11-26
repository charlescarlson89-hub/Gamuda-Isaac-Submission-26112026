"""Server-owned point amounts and Kuala Lumpur activity dates."""

from datetime import timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.models import PointsLedger, User, utcnow

LOCAL_TZ = timezone(timedelta(hours=8), "Asia/Kuala_Lumpur")
DAILY_POINTS = 10
SCAN_POINTS = 50
WEEKLY_POINTS = 100
TERMS_VERSION = "2026-10-21-test-v2"


def local_day(value=None):
    return (value or utcnow()).astimezone(LOCAL_TZ).date()


def locked_user(db, user_id):
    return db.scalar(select(User).where(User.id == user_id).with_for_update())


def post_points(db, user, points, event_key, reason):
    existing = db.scalar(select(PointsLedger).where(PointsLedger.event_key == event_key))
    if existing:
        return False
    if user.points_balance + points < 0:
        raise HTTPException(409, "You do not have enough EcoPoints for this reward.")
    user.points_balance += points
    user.tier = (
        "Tier 3: Community Champion"
        if user.points_balance >= 3000
        else "Tier 2: Humus Custodian"
        if user.points_balance >= 1000
        else "Tier 1: Beginner"
    )
    db.add(PointsLedger(user_id=user.id, event_key=event_key, points=points, reason=reason))
    return True
