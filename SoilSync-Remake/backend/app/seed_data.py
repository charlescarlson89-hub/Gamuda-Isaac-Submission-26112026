"""Idempotent catalogue setup and optional synthetic test accounts."""

import hashlib
import secrets
from datetime import timedelta

from PIL import Image, ImageDraw
from sqlalchemy import select

from app.accounting import TERMS_VERSION, local_day, post_points
from app.atlas_methods import ADDITIONAL_METHODS
from app.catalog_data import FERTILIZERS, LEGACY_FERTILIZERS, PLANTS, REWARDS, WASTE
from app.compost_methods import CURRENT_RECIPE_IDS, WASTE_MATCHES
from app.config import BACKEND_ROOT
from app.household_rewards import household_reward_rows
from app.models import (
    AuthSession,
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
    User,
    UserSettings,
    WasteFertilizerMatch,
    WasteType,
    WeeklyCheckinQuest,
    utcnow,
)
from app.security import passwords
from app.waste_catalogue_v1 import EXISTING_EXTRA_WASTE, EXTRA_WASTE, details_for, recipes_for
from app.waste_catalogue_v2 import NEW_WASTE, WASTE_LINKS, waste_values
from app.waste_catalogue_v3 import ANIMAL_LINKS, ANIMAL_WASTE, BOKASHI_SOURCE, UNSPECIFIED_GUIDE
from app.waste_catalogue_v4 import (
    BONE_DETAILS,
    CHICKEN_BONE,
    REJECTED_BONE_ALIASES,
    REJECTED_BONE_GUIDANCE,
    REJECTED_BONE_ID,
    SMALL_ANIMAL_BONE_GUIDANCE,
    SMALL_ANIMAL_BONE_ID,
    SMALL_ANIMAL_BONE_RICE_WATER_LINK,
    SMALL_FISH_BONE,
)

MOCK_PASSWORD = "SoilSyncDemo!2026"


def ensure_mock_photos(db):
    """Recreate clearly labelled synthetic fixtures after importing the SQL seed."""
    from app.media import safe_local_path

    for quest in db.scalars(
        select(WeeklyCheckinQuest).where(WeeklyCheckinQuest.storage_key.like("local/mock/%"))
    ):
        photo = safe_local_path(quest.storage_key.removeprefix("local/"))
        if not photo.is_file():
            photo.parent.mkdir(parents=True, exist_ok=True)
            image = Image.new("RGB", (640, 480), (100, 120, 65))
            ImageDraw.Draw(image).text((30, 30), "SOILSYNC MOCK PHOTO - NOT EVIDENCE", fill="white")
            image.save(photo, "JPEG")


def populate_catalogue(db):
    additional_waste = EXISTING_EXTRA_WASTE | EXTRA_WASTE
    waste_rows = list(enumerate(WASTE, 1)) + list(additional_waste.items())
    for index, (name, category, supported) in waste_rows:
        existing = db.get(WasteType, index)
        details = details_for(index)
        if index == 22 and name == "Meat and fish":
            details["description"] = UNSPECIFIED_GUIDE
        if index in EXTRA_WASTE and existing and existing.name != name:
            raise RuntimeError(f"Waste ID {index} already belongs to another item.")
        if existing and existing.name == name:
            for key, value in details.items():
                if getattr(existing, key) is None:
                    setattr(existing, key, value)
        if not existing:
            guide = (
                "Remove packaging, chop if useful, and combine with dry browns in a suitable compost system. Use only mature compost in the garden."
                if supported
                else "Keep this material out of a beginner home compost bin. Separate packaging and use an appropriate local collection or disposal route."
            )
            if index in EXTRA_WASTE or index == 22:
                guide = details["description"]
            db.add(
                WasteType(
                    id=index,
                    name=name,
                    category=category,
                    is_supported=supported,
                    rejection_reason=None if supported else category,
                    guide_recommendation=guide,
                    **details,
                )
            )
    for row in (*NEW_WASTE, *ANIMAL_WASTE, SMALL_FISH_BONE, CHICKEN_BONE):
        values = waste_values(row)
        if row in ANIMAL_WASTE:
            values["reference_url"] = BOKASHI_SOURCE
        if values["id"] in BONE_DETAILS:
            aliases, guidance = BONE_DETAILS[values["id"]]
            if values["id"] == SMALL_ANIMAL_BONE_ID:
                guidance = SMALL_ANIMAL_BONE_GUIDANCE
            elif values["id"] == REJECTED_BONE_ID:
                aliases, guidance = REJECTED_BONE_ALIASES, REJECTED_BONE_GUIDANCE
            values.update(aliases=aliases, description=guidance, guide_recommendation=guidance)
        existing = db.get(WasteType, values["id"])
        if existing and existing.name != values["name"]:
            raise RuntimeError(f"Waste ID {values['id']} already belongs to another item.")
        if not existing:
            db.add(WasteType(**values))
    recipes = list(enumerate(LEGACY_FERTILIZERS, 1)) + [(r["id"], r) for r in FERTILIZERS]
    for index, recipe in recipes:
        existing = db.get(FertilizerType, index)
        if index in CURRENT_RECIPE_IDS and existing and existing.name != recipe["name"]:
            raise RuntimeError(f"Recipe ID {index} already belongs to another method; review the migration.")
        if not existing:
            db.add(
                FertilizerType(
                    id=index,
                    name=recipe["name"],
                    description=recipe["description"],
                    est_days_to_finish=recipe["est_days_to_finish"],
                )
            )
            db.flush()
            for step, instruction in enumerate(recipe["steps"], 1):
                db.add(
                    FertilizerRecipeStep(
                        fertilizer_type_id=index, step_number=step, instruction=instruction
                    )
                )
            db.add(
                FertilizerMaintenanceGuide(
                    fertilizer_type_id=index,
                    check_cadence=recipe["check_cadence"],
                    optimal_temp=recipe["optimal_temp"],
                    moisture_range=recipe["moisture_range"],
                )
            )
    for recipe_id, (name, description, days) in ADDITIONAL_METHODS.items():
        existing = db.get(FertilizerType, recipe_id)
        if existing and existing.name != name:
            raise RuntimeError(f"Recipe ID {recipe_id} already belongs to another method.")
        if not existing:
            db.add(FertilizerType(id=recipe_id, name=name, description=description, est_days_to_finish=days))
    for index, (name, kind) in enumerate(PLANTS, 1):
        if not db.get(Plant, index):
            db.add(Plant(id=index, name=name, plant_type=kind, growth_stage="Established"))
    for index, (slug, title, cost, category, kind, description) in enumerate(REWARDS, 1):
        if not db.get(Reward, index):
            db.add(
                Reward(
                    id=index,
                    slug=slug,
                    title=title,
                    description=description + " Partner concept; no real item or voucher issued.",
                    points_cost=cost,
                    category=category,
                    kind=kind,
                )
            )
    for values in household_reward_rows():
        if not db.scalar(select(Reward.id).where(Reward.slug == values["slug"])):
            db.add(Reward(**values))
    db.flush()
    recipe_matches = {recipe_id: list(ids) for recipe_id, ids in WASTE_MATCHES.items()}
    for waste_id, (name, _, supported) in additional_waste.items():
        row = db.get(WasteType, waste_id)
        if row.name == name and row.is_supported and supported:
            for recipe_id in recipes_for(waste_id):
                recipe_matches.setdefault(recipe_id, []).append(waste_id)
    supported = dict(db.execute(select(WasteType.name, WasteType.id).where(WasteType.is_supported)).all())
    for name, recipe_id in WASTE_LINKS:
        if name in supported:
            recipe_matches.setdefault(recipe_id, []).append(supported[name])
    bone_links = [
        SMALL_ANIMAL_BONE_RICE_WATER_LINK,
        *((row[0], recipe) for row in (SMALL_FISH_BONE, CHICKEN_BONE) for recipe in row[-1]),
    ]
    for waste_id, recipe_id in (*ANIMAL_LINKS, *bone_links):
        recipe_matches.setdefault(recipe_id, []).append(waste_id)
    for fertilizer_id, waste_ids in recipe_matches.items():
        for waste_id in waste_ids:
            if not db.scalar(
                select(WasteFertilizerMatch).where(
                    WasteFertilizerMatch.waste_type_id == waste_id,
                    WasteFertilizerMatch.fertilizer_type_id == fertilizer_id,
                )
            ):
                db.add(
                    WasteFertilizerMatch(waste_type_id=waste_id, fertilizer_type_id=fertilizer_id)
                )
    for waste_id in range(1, 21):
        for fertilizer_id in [1, 2] if waste_id not in (12, 18) else [1]:
            if not db.scalar(
                select(WasteFertilizerMatch).where(
                    WasteFertilizerMatch.waste_type_id == waste_id,
                    WasteFertilizerMatch.fertilizer_type_id == fertilizer_id,
                )
            ):
                db.add(
                    WasteFertilizerMatch(waste_type_id=waste_id, fertilizer_type_id=fertilizer_id)
                )
    if not db.scalar(
        select(WasteFertilizerMatch).where(
            WasteFertilizerMatch.waste_type_id == 16, WasteFertilizerMatch.fertilizer_type_id == 3
        )
    ):
        db.add(WasteFertilizerMatch(waste_type_id=16, fertilizer_type_id=3))
    for fertilizer_id in range(1, 7):
        for plant_id in range(1, 21):
            if not db.scalar(
                select(FertilizerSuitablePlant).where(
                    FertilizerSuitablePlant.fertilizer_type_id == fertilizer_id,
                    FertilizerSuitablePlant.plant_id == plant_id,
                )
            ):
                recommended = plant_id <= 18
                db.add(
                    FertilizerSuitablePlant(
                        fertilizer_type_id=fertilizer_id,
                        plant_id=plant_id,
                        is_recommended=recommended,
                        notes="General garden inspiration. Check plant, soil and drainage needs before applying mature compost."
                        if recommended
                        else "Use specialist growing-medium guidance; do not apply this generic recipe directly.",
                    )
                )
    db.flush()


def populate_mock_accounts(db):
    password_hash = passwords.hash(MOCK_PASSWORD)
    for index in range(1, 21):
        email = f"demo{index:02d}@soilsync.example"
        if db.scalar(select(User).where(User.email == email)):
            continue
        user = User(
            username=f"demo{index:02d}",
            email=email,
            password=password_hash,
            location=["Kota Kinabalu", "Penampang", "Tuaran", "Putatan"][index % 4],
            terms_version=TERMS_VERSION,
        )
        db.add(user)
        db.flush()
        db.add(UserSettings(user_id=user.id))
        post_points(
            db, user, 2000, f"seed:{user.id}", "Synthetic mock starting balance; test data only"
        )
        for day_offset in (2, 1):
            day = local_day() - timedelta(days=day_offset)
            db.add(DailyCheckin(user_id=user.id, checkin_date=day))
            post_points(db, user, 10, f"daily:{user.id}:{day}", "Mock daily check-in")
        for scan_index in range(2):
            waste_id = ((index + scan_index) % 20) + 1
            waste = db.get(WasteType, waste_id)
            result = {
                "items": [
                    {
                        "waste_type_id": waste.id,
                        "name": waste.name,
                        "category": waste.category,
                        "is_supported": waste.is_supported,
                        "confidence": 0.9,
                        "guide_recommendation": waste.guide_recommendation,
                        "rejection_reason": waste.rejection_reason,
                    }
                ],
                "explanation": "Synthetic demonstration record, not a live AI result.",
                "source": "seed",
                "fertilizer_ids": [1],
            }
            scan = ScanLog(
                user_id=user.id,
                waste_type_id=waste_id,
                image_sha256=hashlib.sha256(f"seed-{user.id}-{scan_index}".encode()).hexdigest(),
                points_earned=50,
                provider="seed",
                model_name="mock-data-not-ai",
                result=result,
            )
            db.add(scan)
            db.flush()
            post_points(db, user, 50, f"scan:{scan.id}", "Mock scan")
        for batch_index in range(2):
            count = index % 4 if batch_index == 0 else 0
            batch = Batch(
                user_id=user.id,
                fertilizer_type_id=CURRENT_RECIPE_IDS[index % 3],
                batch_number=f"MOCK-{index:02d}-{batch_index + 1}",
                name=f"{'Kitchen' if batch_index == 0 else 'Garden'} batch {index:02d}",
                client_request_id=f"seed-{index}-{batch_index}",
                percentage_completed=round(count / 3 * 100),
                status="Completed" if count == 3 else "Fermenting" if count else "Active",
                est_completion_date=local_day() + timedelta(days=120),
            )
            db.add(batch)
            db.flush()
            for week in range(1, 4):
                done = week <= count
                quest = WeeklyCheckinQuest(
                    batch_id=batch.id,
                    week_number=week,
                    status="DONE" if done else "CURRENT" if week == count + 1 else "UPCOMING",
                    completed_at=utcnow() - timedelta(days=3 - week) if done else None,
                    image_proof_url="/api/photos/pending" if done else None,
                    note=f"Synthetic week {week} observation" if done else "",
                )
                db.add(quest)
                db.flush()
                if done:
                    key = f"mock/user-{user.id}/quest-{quest.id}.jpg"
                    photo = BACKEND_ROOT / "uploads" / key
                    photo.parent.mkdir(parents=True, exist_ok=True)
                    image = Image.new("RGB", (640, 480), (100, 120, 65))
                    ImageDraw.Draw(image).text(
                        (30, 30), "SOILSYNC MOCK PHOTO - NOT EVIDENCE", fill="white"
                    )
                    image.save(photo, "JPEG")
                    quest.storage_key = "local/" + key
                    quest.image_proof_url = f"/api/photos/{quest.id}"
                    post_points(db, user, 100, f"weekly:{quest.id}", "Mock weekly check-in")
        reward = db.get(Reward, index)
        claim = RewardClaim(
            user_id=user.id,
            reward_id=reward.id,
            request_id=f"seed-claim-{index}",
            claim_code=f"MOCK-SS-{index:04d}",
            points_spent=reward.points_cost,
        )
        db.add(claim)
        db.flush()
        post_points(db, user, -reward.points_cost, f"claim:{claim.id}", "Mock eco reward claim")
        db.add(
            AuthSession(
                user_id=user.id,
                token_hash=hashlib.sha256(secrets.token_bytes(48)).hexdigest(),
                expires_at=utcnow() - timedelta(days=1),
            )
        )
    db.flush()
