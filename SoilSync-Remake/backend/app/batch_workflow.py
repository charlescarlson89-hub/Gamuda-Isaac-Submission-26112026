"""Batch scheduling shared by the app and project administration."""

from datetime import timedelta

from app.accounting import local_day
from app.models import Batch, WeeklyCheckinQuest, utcnow

IMAGE_ONLY_POLICY = "image_only"


def accepts_any_checkin_image(quest):
    return (quest.verification or {}).get("policy") == IMAGE_ONLY_POLICY


def create_batch_record(db, owner, recipe, body, method, *, started_at=None, image_only=False):
    started_at = started_at or utcnow()
    start_day = local_day(started_at)
    timeline_days = method.timeline_days if method else recipe.est_days_to_finish
    weeks = (timeline_days + 6) // 7 if method else 3
    row = Batch(
        user_id=owner.id,
        fertilizer_type_id=recipe.id,
        name=body.name,
        batch_number="Pending",
        client_request_id=str(body.client_request_id),
        started_at=started_at,
        est_completion_date=start_day + timedelta(days=timeline_days),
    )
    db.add(row)
    db.flush()
    row.batch_number = f"Batch #{row.id:04d}"
    for week in range(1, weeks + 1):
        db.add(
            WeeklyCheckinQuest(
                batch_id=row.id,
                week_number=week,
                status="CURRENT" if week == 1 else "UPCOMING",
                available_on=start_day + timedelta(days=min(week * 7, timeline_days)) if method else None,
                verification={"policy": IMAGE_ONLY_POLICY} if image_only else None,
            )
        )
    db.flush()
    return row
