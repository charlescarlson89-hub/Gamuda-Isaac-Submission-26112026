"""Explicit API serializers: password hashes, session tokens and object keys stay private."""

from sqlalchemy import select

from app import atlas_methods
from app.accounting import local_day
from app.batch_workflow import accepts_any_checkin_image
from app.compost_methods import CURRENT_RECIPE_IDS, RECIPE_DETAILS
from app.models import (
    Batch,
    DailyCheckin,
    FertilizerMaintenanceGuide,
    FertilizerRecipeStep,
    FertilizerSuitablePlant,
    FertilizerType,
    Plant,
    Reward,
    RewardClaim,
    ScanLog,
    UserSettings,
    WasteFertilizerMatch,
    WasteType,
    WeeklyCheckinQuest,
)
from app.waste_catalogue_v4 import SMALL_ANIMAL_BONE_GUIDANCE, SMALL_ANIMAL_BONE_ID, is_servingware


def iso(value):
    return value.isoformat() if value is not None else None


def public_user(user):
    return {
        "id": user.id,
        "name": user.username,
        "username": user.username,
        "email": user.email,
        "location": user.location,
        "tier": user.tier,
        "streakDays": user.streak_days,
        "createdAt": iso(user.created_at),
    }


def public_waste(row):
    return {
        "id": row.id,
        "name": row.name,
        "category": row.category,
        "is_supported": row.is_supported,
        "rejection_reason": row.rejection_reason,
        "guide_recommendation": row.guide_recommendation,
        "description": row.description,
        "aliases": row.aliases or [],
        "ingredient_role": row.ingredient_role,
        "reference_url": row.reference_url,
    }


def public_reward(row):
    return {
        "id": row.slug,
        "databaseId": row.id,
        "name": row.title,
        "cost": row.points_cost,
        "kind": row.kind,
        "category": "partner",
        "displayCategory": row.category,
        "description": row.description,
        "active": row.is_active,
        "prototypeOnly": row.prototype_only,
    }


def public_claim(row, reward):
    return {
        "id": str(row.id),
        "rewardId": reward.slug,
        "at": iso(row.claimed_at),
        "expiresAt": None,
        "claimCode": row.claim_code,
        "cost": row.points_spent,
        "isRedeemed": row.is_redeemed,
    }


def public_batch(db, batch):
    quests = list(
        db.scalars(
            select(WeeklyCheckinQuest)
            .where(WeeklyCheckinQuest.batch_id == batch.id)
            .order_by(WeeklyCheckinQuest.week_number)
        )
    )
    return {
        "id": str(batch.id),
        "name": batch.name,
        "number": batch.batch_number,
        "fertilizerTypeId": batch.fertilizer_type_id,
        "fertilizerName": db.get(FertilizerType, batch.fertilizer_type_id).name,
        "status": batch.status,
        "progress": batch.percentage_completed,
        "startedAt": iso(batch.started_at),
        "estimatedCompletionDate": iso(batch.est_completion_date),
        "quests": [
            {
                "id": row.id,
                "week": row.week_number,
                "status": row.status,
                "points": row.points_reward,
                "availableOn": iso(row.available_on),
                "imageOnly": accepts_any_checkin_image(row),
                "canClaim": row.status == "CURRENT"
                and (row.available_on is None or row.available_on <= local_day()),
            }
            for row in quests
        ],
        "checkins": [
            {
                "id": str(row.id),
                "week": row.week_number,
                "at": iso(row.completed_at),
                "note": row.note,
                "photoUrl": row.image_proof_url,
                "verification": row.verification,
            }
            for row in quests
            if row.status == "DONE"
        ],
    }


def public_scan(row, db=None):
    # Re-resolve recommendations without altering historical detections or awarding points.
    result = dict(row.result)
    if db is not None:
        items = [dict(item) for item in result.get("items", []) if not is_servingware(item.get("name"))]
        ids = [item["waste_type_id"] for item in items if item.get("is_supported")]
        matches = (
            db.execute(
                select(
                    WasteFertilizerMatch.waste_type_id, WasteFertilizerMatch.fertilizer_type_id
                ).where(
                    WasteFertilizerMatch.waste_type_id.in_(ids),
                    WasteFertilizerMatch.fertilizer_type_id.in_(CURRENT_RECIPE_IDS),
                )
            ).all()
            if ids
            else []
        )
        for item in items:
            if item.get("is_supported") and item.get("waste_type_id") == SMALL_ANIMAL_BONE_ID:
                item["guide_recommendation"] = SMALL_ANIMAL_BONE_GUIDANCE
            item["fertilizer_ids"] = sorted(
                {r for w, r in matches if w == item.get("waste_type_id")}
            )
        recipe_ids = sorted({r for _, r in matches})
        result.update(
            items=items,
            fertilizer_ids=recipe_ids,
            fertilizers=[
                public_recipe(db, recipe)
                for recipe in db.scalars(
                    select(FertilizerType)
                    .where(FertilizerType.id.in_(recipe_ids))
                    .order_by(FertilizerType.id)
                )
            ],
        )
    return {
        **result,
        "id": row.id,
        "at": iso(row.scanned_at),
        "pointsEarned": row.points_earned,
        "provider": row.provider,
        "model": row.model_name,
    }


def public_recipe(db, row):
    guide = RECIPE_DETAILS.get(row.id)
    steps = list(
        db.scalars(
            select(FertilizerRecipeStep)
            .where(FertilizerRecipeStep.fertilizer_type_id == row.id)
            .order_by(FertilizerRecipeStep.step_number)
        )
    )
    maintenance = db.scalar(
        select(FertilizerMaintenanceGuide).where(
            FertilizerMaintenanceGuide.fertilizer_type_id == row.id
        )
    )
    plants = db.execute(
        select(FertilizerSuitablePlant, Plant)
        .join(Plant)
        .where(FertilizerSuitablePlant.fertilizer_type_id == row.id)
        .order_by(Plant.id)
    ).all()
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "estimatedDays": row.est_days_to_finish,
        "method": guide["method"] if guide else None,
        "active": row.id in CURRENT_RECIPE_IDS,
        "timeline": guide["timeline"] if guide else None,
        "sources": guide["sources"] if guide else [],
        "stages": [
            {
                "title": title,
                "imageKey": f"{guide['method']}-{index + 1}",
                "steps": [
                    {"number": s.step_number, "instruction": s.instruction}
                    for s in steps[start:end]
                ],
            }
            for index, (title, start, end) in enumerate(
                zip(guide["stages"], (0, 2, 5), (2, 5, 7), strict=True)
            )
        ]
        if guide
        else [],
        "steps": [{"number": step.step_number, "instruction": step.instruction} for step in steps],
        "plants": [
            {
                "id": plant.id,
                "name": plant.name,
                "type": plant.plant_type,
                "growthStage": plant.growth_stage,
                "recommended": suitability.is_recommended,
                "notes": suitability.notes,
            }
            for suitability, plant in plants
        ],
        "maintenance": {
            "cadence": maintenance.check_cadence,
            "temperature": maintenance.optimal_temp,
            "moisture": maintenance.moisture_range,
        }
        if maintenance
        else None,
    }


def catalogue(db, *, methods=None):
    if methods is None:
        methods = atlas_methods.load_methods()
    recipes = []
    for row in db.scalars(
        select(FertilizerType)
        .where(FertilizerType.id.in_((*CURRENT_RECIPE_IDS, *methods)))
        .order_by(FertilizerType.id)
    ):
        recipe = public_recipe(db, row)
        if row.id in methods:
            recipe.update(atlas_methods.guide_fields(methods[row.id]))
        recipes.append(recipe)
    return {
        "wasteTypes": [
            public_waste(row) for row in db.scalars(select(WasteType).order_by(WasteType.id))
        ],
        "rewards": [public_reward(row) for row in db.scalars(select(Reward).order_by(Reward.id))],
        "fertilizers": recipes,
        "pointRules": {"daily": 10, "scan": 50, "weekly": 100},
    }


def state_snapshot(db, user):
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    claims = db.execute(
        select(RewardClaim, Reward)
        .join(Reward)
        .where(RewardClaim.user_id == user.id)
        .order_by(RewardClaim.claimed_at)
    ).all()
    scan = db.scalar(
        select(ScanLog)
        .where(ScanLog.user_id == user.id)
        .order_by(ScanLog.scanned_at.desc(), ScanLog.id.desc())
        .limit(1)
    )
    return {
        "version": 3,
        "profile": public_user(user),
        "balance": user.points_balance,
        "checkins": [
            iso(day)
            for day in db.scalars(
                select(DailyCheckin.checkin_date)
                .where(DailyCheckin.user_id == user.id)
                .order_by(DailyCheckin.checkin_date)
            )
        ],
        "redemptions": [public_claim(claim, reward) for claim, reward in claims],
        "preferences": {
            "checkin": settings.checkin_reminder,
            "rewards": settings.reward_received_notify,
            "service": settings.service_notices_notify,
            "claim": settings.claim_reward_reminder,
        },
        "quietHours": {"start": settings.quiet_hours_start, "end": settings.quiet_hours_end},
        "batches": [
            public_batch(db, batch)
            for batch in db.scalars(
                select(Batch).where(Batch.user_id == user.id).order_by(Batch.started_at, Batch.id)
            )
        ],
        "scan": public_scan(scan, db) if scan else None,
        "catalog": catalogue(db),
    }
