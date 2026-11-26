"""SoilSync API: user accounts, catalogue, scans, batches, photos and rewards."""

import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app import atlas_methods, gemini_credentials, media, recipe_formulation, waste_catalogue_v4
from app.accounting import (
    DAILY_POINTS,
    SCAN_POINTS,
    TERMS_VERSION,
    WEEKLY_POINTS,
    local_day,
    locked_user,
    post_points,
)
from app.batch_workflow import IMAGE_ONLY_POLICY, accepts_any_checkin_image, create_batch_record
from app.compost_methods import CURRENT_RECIPE_IDS
from app.config import get_settings
from app.database import get_db
from app.models import (
    AuthSession,
    Batch,
    DailyCheckin,
    FertilizerType,
    GeminiCredential,
    PointsLedger,
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
from app.schemas import (
    AdminUserList,
    BatchCreate,
    ChatInput,
    ClaimCreate,
    GeminiKeyInput,
    Login,
    ProfileUpdate,
    Registration,
    SettingsUpdate,
)
from app.security import (
    CSRF_COOKIE,
    DUMMY_HASH,
    SESSION_COOKIE,
    create_session,
    digest,
    issue_csrf,
    limiter,
    passwords,
    require_admin,
    require_user,
    verify_csrf,
)
from app.serializers import (
    catalogue,
    public_batch,
    public_claim,
    public_recipe,
    public_reward,
    public_scan,
    public_user,
    state_snapshot,
)

logger = logging.getLogger("soilsync")
config = get_settings()
app = FastAPI(
    title="SoilSync API",
    version="0.1.0",
    description="TEDA BYTE user-based PostgreSQL API. Scans use server-side Gemini; rewards are partner concepts.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
DB = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(require_user)]
CurrentAdmin = Annotated[User, Depends(require_admin)]
write = [Depends(verify_csrf)]


@app.middleware("http")
async def response_policy(request: Request, call_next):
    length = request.headers.get("content-length", "0")
    if length.isdigit() and int(length) > media.MAX_UPLOAD + 128 * 1024:
        return JSONResponse({"detail": "Upload is too large."}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    # Do not echo invalid password values or whole request bodies into responses.
    return JSONResponse(
        {
            "detail": [
                {"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]}
                for item in error.errors()
            ]
        },
        status_code=422,
    )


@app.exception_handler(OperationalError)
async def database_error(request, error):
    logger.error("PostgreSQL request unavailable (%s)", type(error).__name__)
    return JSONResponse(
        {"detail": "The database is unavailable. Start PostgreSQL and the backend, then retry."},
        status_code=503,
    )


@app.exception_handler(IntegrityError)
async def integrity_error(request, error):
    return JSONResponse(
        {
            "detail": "This record already exists or conflicts with the current state. Refresh and retry."
        },
        status_code=409,
    )


@app.get("/api/health")
def health(db: DB):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "gemini": (
            "per_account" if config.gemini_require_personal_key and config.gemini_demo_user_id is None else
            "configured" if config.gemini_api_key.get_secret_value() else "missing_key"
        ),
        "photoStorage": "firebase-emulator"
        if config.upload_storage == "firebase" and config.storage_emulator_host
        else config.upload_storage,
    }


@app.get("/api/auth/csrf")
def csrf(request: Request, response: Response):
    return {"csrfToken": issue_csrf(request, response)}


@app.post("/api/auth/register", status_code=201, dependencies=write)
def register(body: Registration, request: Request, response: Response, db: DB):
    limiter.check(("register", request.client.host), 10, 3600)
    if db.scalar(
        select(User.id).where(
            or_(
                func.lower(User.email) == body.email.lower(),
                func.lower(User.username) == body.username.lower(),
            )
        )
    ):
        raise HTTPException(409, "That email or username is already registered.")
    user = User(
        username=body.username,
        email=body.email.lower(),
        password=passwords.hash(body.password.get_secret_value()),
        location=body.location,
        terms_version=TERMS_VERSION,
    )
    db.add(user)
    db.flush()
    db.add(UserSettings(user_id=user.id))
    create_session(db, user, response)
    db.flush()
    return {"user": public_user(user)}


@app.post("/api/auth/login", dependencies=write)
def login(body: Login, request: Request, response: Response, db: DB):
    limiter.check(("login", request.client.host), 15, 300)
    user = db.scalar(
        select(User).where(
            or_(
                func.lower(User.email) == body.identifier.lower(),
                func.lower(User.username) == body.identifier.lower(),
            )
        )
    )
    try:
        valid = passwords.verify(
            body.password.get_secret_value(), user.password if user else DUMMY_HASH
        )
    except Exception:
        valid = False
    if not user or not valid:
        raise HTTPException(401, "Email/username or password is incorrect.")
    create_session(db, user, response)
    return {"user": public_user(user)}


@app.post("/api/auth/logout", dependencies=write)
def logout(request: Request, response: Response, db: DB):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == digest(token)))
    response.delete_cookie(
        SESSION_COOKIE, path="/", secure=config.cookie_secure, httponly=True, samesite="lax"
    )
    response.delete_cookie(CSRF_COOKIE, path="/", secure=config.cookie_secure, samesite="lax")
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: CurrentUser):
    return {"user": public_user(user)}


@app.get(
    "/api/admin/users",
    tags=["Admin"],
    summary="List registered user IDs and usernames",
    response_model=AdminUserList,
    responses={
        401: {"description": "Log in to SoilSync in this browser first."},
        403: {"description": "The logged-in account is not in the server admin allowlist."},
    },
)
def list_admin_users(
    _admin: CurrentAdmin,
    db: DB,
    limit: Annotated[int, Query(ge=1, le=100, description="Accounts per page, up to 100.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of accounts to skip.")] = 0,
):
    """Read-only account directory, including demo accounts, ordered by user ID.

    Log in through the SoilSync frontend using an authorised admin account, then
    use **Try it out â†’ Execute** here in the same browser. Use the same hostname
    for both pages (for example, 127.0.0.1) so the session cookie is shared.
    Admin access is controlled by the server's ADMIN_USER_IDS configuration.
    Increase offset by limit to fetch the next page while has_more is true.
    Only IDs and usernames are returned; no password, session or contact fields.
    """
    total = db.scalar(select(func.count(User.id)))
    rows = db.execute(select(User.id, User.username).order_by(User.id).offset(offset).limit(limit))
    users = [{"id": row.id, "username": row.username} for row in rows]
    return {
        "users": users,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(users) < total,
    }


@app.get("/api/state")
def state(user: CurrentUser, db: DB):
    return state_snapshot(db, user)


@app.patch("/api/profile", dependencies=write)
def update_profile(body: ProfileUpdate, user: CurrentUser, db: DB):
    other = db.scalar(
        select(User.id).where(
            func.lower(User.username) == body.username.lower(), User.id != user.id
        )
    )
    if other:
        raise HTTPException(409, "That username is already in use.")
    user.username, user.location = body.username, body.location
    db.flush()
    return {"user": public_user(user)}


@app.get("/api/user-settings")
def read_preferences(user: CurrentUser, db: DB):
    row = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    return {
        column.name: getattr(row, column.name)
        for column in UserSettings.__table__.columns
        if column.name not in {"id", "user_id"}
    }


@app.patch("/api/user-settings", dependencies=write)
def update_preferences(body: SettingsUpdate, user: CurrentUser, db: DB):
    row = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    for key, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(row, key, value)
    db.flush()
    return {"ok": True}


@app.get("/api/user-settings/gemini-key")
def gemini_key_status(user: CurrentUser, db: DB):
    available = gemini_credentials.can_manage(user.id)
    return {"available": available, "configured": available and db.get(GeminiCredential, user.id) is not None}


@app.post("/api/user-settings/gemini-key", dependencies=write)
def save_gemini_key(body: GeminiKeyInput, user: CurrentUser, db: DB):
    if not gemini_credentials.can_manage(user.id):
        raise HTTPException(403, "Personal Gemini keys are unavailable for this account.")
    encrypted_key = gemini_credentials.encrypt(user.id, body.api_key.get_secret_value())
    locked_user(db, user.id)
    credential = db.get(GeminiCredential, user.id)
    if credential is None:
        db.add(GeminiCredential(user_id=user.id, encrypted_key=encrypted_key))
    else:
        credential.encrypted_key = encrypted_key
    return {"available": True, "configured": True}


@app.delete("/api/user-settings/gemini-key", dependencies=write)
def delete_gemini_key(user: CurrentUser, db: DB):
    locked_user(db, user.id)
    db.execute(delete(GeminiCredential).where(GeminiCredential.user_id == user.id))
    return {"available": gemini_credentials.can_manage(user.id), "configured": False}


@app.get("/api/catalog")
def read_catalogue(db: DB):
    return catalogue(db)


@app.get("/api/waste-types")
def waste_types(db: DB):
    return catalogue(db)["wasteTypes"]


@app.get("/api/fertilizers/{fertilizer_id}")
def fertilizer_recipe(fertilizer_id: int, db: DB):
    row = db.get(FertilizerType, fertilizer_id)
    if not row:
        raise HTTPException(404, "Recipe not found.")
    return public_recipe(db, row)


@app.post("/api/daily-checkins", dependencies=write)
def daily_checkin(user: CurrentUser, db: DB):
    owner = locked_user(db, user.id)
    today = local_day()
    if db.scalar(
        select(DailyCheckin.id).where(
            DailyCheckin.user_id == owner.id, DailyCheckin.checkin_date == today
        )
    ):
        return {"pointsAwarded": 0, "alreadyCheckedIn": True}
    previous = db.scalar(
        select(func.max(DailyCheckin.checkin_date)).where(DailyCheckin.user_id == owner.id)
    )
    owner.streak_days = owner.streak_days + 1 if previous == today - timedelta(days=1) else 1
    db.add(DailyCheckin(user_id=owner.id, checkin_date=today))
    post_points(db, owner, DAILY_POINTS, f"daily:{owner.id}:{today}", "Daily check-in")
    db.flush()
    return {"pointsAwarded": DAILY_POINTS, "streakDays": owner.streak_days}


@app.get("/api/points-ledger")
def points_ledger(user: CurrentUser, db: DB):
    entries = db.scalars(
        select(PointsLedger)
        .where(PointsLedger.user_id == user.id)
        .order_by(PointsLedger.id.desc())
        .limit(100)
    )
    return {
        "balance": user.points_balance,
        "entries": [
            {
                "id": row.id,
                "points": row.points,
                "reason": row.reason,
                "at": row.created_at.isoformat(),
            }
            for row in entries
        ],
    }


@app.post("/api/scans", dependencies=write)
def scan_waste(user: CurrentUser, db: DB, photo: Annotated[UploadFile, File()]):
    limiter.check(("scan", user.id), 10, 3600)
    user_id = user.id
    data, image_hash = media.image_bytes(photo)
    existing = db.scalar(
        select(ScanLog).where(ScanLog.user_id == user_id, ScanLog.image_sha256 == image_hash)
    )
    if existing and not waste_catalogue_v4.has_legacy_bone_detection(existing.result):
        return {"scan": public_scan(existing, db), "pointsAwarded": 0, "duplicate": True}
    types = list(db.scalars(select(WasteType).order_by(WasteType.id)))
    # Release the read connection while the external vision request is running.
    with gemini_credentials.use_account_key(db, user_id):
        db.close()
        prediction = media.detect_waste(data, types)
    owner = locked_user(db, user_id)
    existing = db.scalar(
        select(ScanLog).where(ScanLog.user_id == user_id, ScanLog.image_sha256 == image_hash)
    )
    if existing and not waste_catalogue_v4.has_legacy_bone_detection(existing.result):
        return {"scan": public_scan(existing, db), "pointsAwarded": 0, "duplicate": True}
    allowed = {row.id: row for row in types}
    items, seen = [], set()
    for item in prediction.items:
        if waste_catalogue_v4.is_servingware(item.detected_name):
            continue
        waste_id = waste_catalogue_v4.resolve_bone_detection(item.waste_type_id, item.detected_name)
        matched = allowed.get(waste_id) if item.confidence >= 0.65 else None
        identity = matched.id if matched else item.detected_name.casefold()
        if identity in seen:
            continue
        seen.add(identity)
        items.append(
            {
                "waste_type_id": matched.id if matched else None,
                "name": matched.name if matched else item.detected_name,
                "category": matched.category if matched else "Unknown material",
                "description": matched.description if matched else None,
                "is_supported": matched.is_supported if matched else False,
                "confidence": item.confidence,
                "rejection_reason": matched.rejection_reason
                if matched
                else "Uncertain or outside the catalogue",
                "guide_recommendation": matched.guide_recommendation
                if matched
                else "Use a clearer photo or consult the waste guide. Do not add unidentified materials to compost.",
            }
        )
    supported_ids = [item["waste_type_id"] for item in items if item["is_supported"]]
    matches = (
        db.execute(
            select(
                WasteFertilizerMatch.waste_type_id, WasteFertilizerMatch.fertilizer_type_id
            ).where(
                WasteFertilizerMatch.waste_type_id.in_(supported_ids),
                WasteFertilizerMatch.fertilizer_type_id.in_(CURRENT_RECIPE_IDS),
            )
        ).all()
        if supported_ids
        else []
    )
    for item in items:
        item["fertilizer_ids"] = sorted(
            {recipe_id for waste_id, recipe_id in matches if waste_id == item["waste_type_id"]}
        )
    recipe_ids = sorted({recipe_id for _, recipe_id in matches})
    recipes = [
        public_recipe(db, recipe)
        for recipe in db.scalars(
            select(FertilizerType)
            .where(FertilizerType.id.in_(recipe_ids))
            .order_by(FertilizerType.id)
        )
    ]
    recognized = next(
        (item["waste_type_id"] for item in items if item["waste_type_id"] is not None), None
    )
    # Award scan points only when at least one catalogue match is compostable.
    # Identified but rejected items (for example, plastic packaging) earn none.
    has_compostable_waste = any(item["is_supported"] for item in items)
    points = SCAN_POINTS if has_compostable_waste else 0
    result = {
        "items": items,
        "explanation": prediction.explanation,
        "source": "gemini",
        "bone_rules": waste_catalogue_v4.BONE_RULES_VERSION,
        "fertilizer_ids": recipe_ids,
        "fertilizers": recipes,
    }
    if existing:
        existing.result = result
        existing.waste_type_id = recognized
        return {"scan": public_scan(existing, db), "pointsAwarded": 0, "duplicate": True}
    row = ScanLog(
        user_id=user_id,
        waste_type_id=recognized,
        image_sha256=image_hash,
        points_earned=points,
        model_name=config.gemini_model,
        result=result,
    )
    db.add(row)
    db.flush()
    if points:
        post_points(db, owner, points, f"scan:{row.id}", "Compostable waste scan")
    return {"scan": public_scan(row, db), "pointsAwarded": points, "duplicate": False}


@app.get("/api/scans")
def scan_history(user: CurrentUser, db: DB):
    return [
        public_scan(row, db)
        for row in db.scalars(
            select(ScanLog).where(ScanLog.user_id == user.id).order_by(ScanLog.id.desc()).limit(50)
        )
    ]


def scan_waste_rows(scan_id, user_id, db):
    scan = db.scalar(select(ScanLog).where(ScanLog.id == scan_id, ScanLog.user_id == user_id))
    if scan is None:
        raise HTTPException(404, "Scan not found.")
    waste_ids = {
        item["waste_type_id"]
        for item in scan.result.get("items", [])
        if item.get("is_supported") and item.get("waste_type_id") is not None
        and not waste_catalogue_v4.is_servingware(item.get("name"))
    }
    return list(db.scalars(select(WasteType).where(WasteType.id.in_(waste_ids)).order_by(WasteType.id)))


def scan_recipe_links(db, waste_rows, recipe_ids):
    matches = {}
    if waste_rows:
        for waste_id, recipe_id in db.execute(
            select(WasteFertilizerMatch.waste_type_id, WasteFertilizerMatch.fertilizer_type_id)
            .where(WasteFertilizerMatch.waste_type_id.in_([row.id for row in waste_rows]),
                   WasteFertilizerMatch.fertilizer_type_id.in_(recipe_ids))
        ):
            matches.setdefault(recipe_id, set()).add(waste_id)
    return matches


@app.get("/api/scans/{scan_id}/method-match")
def method_match(scan_id: int, user: CurrentUser, db: DB):
    waste_rows = scan_waste_rows(scan_id, user.id, db)
    links = scan_recipe_links(db, waste_rows, atlas_methods.LINKED_METHOD_IDS)
    db.close()
    methods = atlas_methods.load_methods()
    if not methods:
        raise HTTPException(503, "The compost recipe library is temporarily unavailable.")
    recommendation = atlas_methods.recommend(methods, waste_rows, links)
    compatible = (
        {recipe["recipeId"] for recipe in [recommendation, *recommendation["alternatives"]]}
        if recommendation else set()
    )
    return {
        "recommendation": recommendation,
        "featuredMethods": [
            {"id": method_id, "name": methods[method_id].method_name, "matchesScan": method_id in compatible}
            for method_id in atlas_methods.FEATURED_METHOD_IDS
            if method_id in methods
        ],
    }


@app.post("/api/scans/{scan_id}/recipe-suggestion", dependencies=write)
def recipe_suggestion(scan_id: int, user: CurrentUser, db: DB):
    waste_rows = scan_waste_rows(scan_id, user.id, db)
    limiter.check(("recipe-suggestion", user.id), 10, 3600)
    methods = atlas_methods.load_methods()
    if methods:
        links = scan_recipe_links(db, waste_rows, atlas_methods.LINKED_METHOD_IDS)
        recommendation = atlas_methods.recommend(methods, waste_rows, links)
        if recommendation is None:
            raise HTTPException(422, "No recipe matches all the identified food scraps.")
        return recommendation
    matches = scan_recipe_links(db, waste_rows, CURRENT_RECIPE_IDS)
    with gemini_credentials.use_account_key(db, user.id):
        db.close()
        return recipe_formulation.suggest_mix(waste_rows, matches)


@app.get("/api/scans/{scan_id}")
def read_scan(scan_id: int, user: CurrentUser, db: DB):
    row = db.scalar(select(ScanLog).where(ScanLog.id == scan_id, ScanLog.user_id == user.id))
    if not row:
        raise HTTPException(404, "Scan not found.")
    return public_scan(row, db)


@app.get("/api/batches")
def batches(user: CurrentUser, db: DB):
    return [
        public_batch(db, row)
        for row in db.scalars(select(Batch).where(Batch.user_id == user.id).order_by(Batch.id))
    ]


@app.post("/api/batches", status_code=201, dependencies=write)
def create_batch(body: BatchCreate, user: CurrentUser, db: DB):
    method = atlas_methods.load_methods().get(body.fertilizer_type_id)
    owner = locked_user(db, user.id)
    existing = db.scalar(
        select(Batch).where(
            Batch.user_id == owner.id, Batch.client_request_id == str(body.client_request_id)
        )
    )
    if existing:
        return public_batch(db, existing)
    recipe = db.get(FertilizerType, body.fertilizer_type_id)
    if not recipe or (recipe.id not in CURRENT_RECIPE_IDS and not method):
        raise HTTPException(404, "Recipe not found.")
    row = create_batch_record(db, owner, recipe, body, method)
    return public_batch(db, row)


def owned_batch(db, batch_id, user_id):
    row = db.scalar(
        select(Batch).where(Batch.id == batch_id, Batch.user_id == user_id).with_for_update()
    )
    if not row:
        raise HTTPException(404, "Batch not found.")
    return row


@app.get("/api/batches/{batch_id}")
def read_batch(batch_id: int, user: CurrentUser, db: DB):
    row = db.scalar(select(Batch).where(Batch.id == batch_id, Batch.user_id == user.id))
    if not row:
        raise HTTPException(404, "Batch not found.")
    return public_batch(db, row)


@app.post("/api/batches/{batch_id}/quests/{week}/complete", dependencies=write)
def complete_quest(
    batch_id: int,
    week: int,
    user: CurrentUser,
    db: DB,
    photo: Annotated[UploadFile, File()],
    note: Annotated[str, Form(max_length=250)] = "",
):
    user_id = user.id

    def current_quest():
        batch = owned_batch(db, batch_id, user_id)
        quest = db.scalar(
            select(WeeklyCheckinQuest).where(
                WeeklyCheckinQuest.batch_id == batch.id, WeeklyCheckinQuest.week_number == week
            )
        )
        if not quest:
            raise HTTPException(404, "Weekly quest not found.")
        if quest.status not in {"CURRENT", "DONE"}:
            raise HTTPException(409, "Complete the current week before starting another stage.")
        if quest.status == "CURRENT" and quest.available_on and quest.available_on > local_day():
            raise HTTPException(409, f"This check-in opens on {quest.available_on.isoformat()}.")
        return batch, quest

    batch, quest = current_quest()
    if quest.status == "DONE":
        return {"batch": public_batch(db, batch), "pointsAwarded": 0}
    limiter.check(("compost-proof", user_id), 10, 3600)
    data, _ = media.image_bytes(photo)
    image_only = accepts_any_checkin_image(quest)
    image_hash = None if image_only else hashlib.sha256(data).hexdigest()

    def reject_reused_image():
        reused = db.scalar(
            select(WeeklyCheckinQuest.id)
            .join(Batch)
            .where(Batch.user_id == user_id, WeeklyCheckinQuest.image_sha256 == image_hash)
            .limit(1)
        )
        if reused:
            raise HTTPException(
                409,
                "This photo already supports a check-in. Take a fresh compost photo for this week.",
            )

    if image_only:
        db.close()
        verification_details = {"policy": IMAGE_ONLY_POLICY, "status": "recorded", "provider": "upload"}
    else:
        reject_reused_image()
        rice_water = batch.fertilizer_type_id == atlas_methods.METHOD_IDS["diy_rice_water_lab"]
        recipe_name = db.get(FertilizerType, batch.fertilizer_type_id).name
        # No database connection or wallet/batch lock is held during the external AI call.
        with gemini_credentials.use_account_key(db, user_id):
            db.close()
            verification = media.verify_compost(data, recipe_name, rice_water=rice_water, week=week)
        if (
            verification.verdict != "compost"
            or verification.confidence < media.COMPOST_CONFIDENCE_THRESHOLD
        ):
            if rice_water and week in media.RICE_WATER_SCRAP_WEEKS:
                retry_hint = "Show a clear photo of the collected food scraps, such as peels, rinds, or vegetable trimmings."
            elif rice_water:
                retry_hint = "Show the cloudy or separated starter and its container clearly, or show the composting scraps when your guide calls for it."
            else:
                retry_hint = "Show the compost contents in good light and retake the photo."
            raise HTTPException(
                422, f"Check-in could not be confirmed. {retry_hint} No check-in or points were saved."
            )
        verification_details = {
            **verification.model_dump(),
            "status": "approved",
            "provider": "gemini",
            "model": config.gemini_model,
            "threshold": media.COMPOST_CONFIDENCE_THRESHOLD,
        }
    owner = locked_user(db, user_id)
    # Another simultaneous upload may have completed this quest while AI was running.
    batch, quest = current_quest()
    if quest.status == "DONE":
        return {"batch": public_batch(db, batch), "pointsAwarded": 0}
    if not image_only:
        reject_reused_image()
    database_photos = config.upload_storage == "postgres"
    key = None if database_photos else media.save_photo(data, owner.id)
    try:
        quest.status, quest.note = "DONE", note.strip()
        quest.storage_key, quest.image_proof_url = key, f"/api/photos/{quest.id}"
        quest.photo_data = data if database_photos else None
        quest.completed_at = utcnow()
        quest.image_sha256 = image_hash
        if not image_only:
            verification_details["verifiedAt"] = quest.completed_at.isoformat()
        quest.verification = verification_details
        next_quest = db.scalar(
            select(WeeklyCheckinQuest).where(
                WeeklyCheckinQuest.batch_id == batch.id,
                WeeklyCheckinQuest.week_number == week + 1,
                WeeklyCheckinQuest.status == "UPCOMING",
            )
        )
        if next_quest:
            next_quest.status = "CURRENT"
        count, total = db.execute(
            select(func.count().filter(WeeklyCheckinQuest.status == "DONE"), func.count())
            .select_from(WeeklyCheckinQuest)
            .where(WeeklyCheckinQuest.batch_id == batch.id)
        ).one()
        batch.percentage_completed = min(99, round(count / total * 100)) if count < total else 100
        batch.status = "Completed" if count == total else "Fermenting"
        post_points(db, owner, WEEKLY_POINTS, f"weekly:{quest.id}", "Weekly batch check-in")
        db.commit()
    except Exception:
        db.rollback()
        media.delete_photo(key)
        raise
    return {"batch": public_batch(db, batch), "pointsAwarded": WEEKLY_POINTS}


@app.delete("/api/batches/{batch_id}", dependencies=write)
def delete_batch(batch_id: int, user: CurrentUser, db: DB):
    owner = locked_user(db, user.id)
    batch = owned_batch(db, batch_id, owner.id)
    if batch.percentage_completed != 100 or batch.status != "Completed":
        raise HTTPException(409, "Complete all three check-ins before deleting this batch.")
    quests = list(
        db.scalars(select(WeeklyCheckinQuest).where(WeeklyCheckinQuest.batch_id == batch.id))
    )
    for quest in quests:
        media.delete_photo(quest.storage_key)
    db.execute(delete(WeeklyCheckinQuest).where(WeeklyCheckinQuest.batch_id == batch.id))
    db.delete(batch)
    return {"deletedId": str(batch_id)}


@app.get("/api/photos/{quest_id}")
def photo_proof(quest_id: int, user: CurrentUser, db: DB):
    quest = db.scalar(
        select(WeeklyCheckinQuest)
        .join(Batch)
        .where(WeeklyCheckinQuest.id == quest_id, Batch.user_id == user.id)
    )
    if not quest or (not quest.storage_key and not quest.photo_data):
        raise HTTPException(404, "Photo not found.")
    return Response(
        quest.photo_data if quest.photo_data else media.read_photo(quest.storage_key),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store", "Content-Disposition": "inline"},
    )


@app.get("/api/rewards")
def reward_catalogue(db: DB):
    return [
        public_reward(row)
        for row in db.scalars(select(Reward).where(Reward.is_active.is_(True)).order_by(Reward.id))
    ]


@app.post("/api/rewards/{slug}/claims", dependencies=write)
def claim_reward(slug: str, body: ClaimCreate, user: CurrentUser, db: DB):
    owner = locked_user(db, user.id)
    reward = db.scalar(select(Reward).where(Reward.slug == slug))
    if not reward or not reward.is_active:
        raise HTTPException(404, "This reward is unavailable.")
    retry = db.scalar(
        select(RewardClaim).where(
            RewardClaim.user_id == owner.id, RewardClaim.request_id == str(body.request_id)
        )
    )
    if retry:
        if retry.reward_id != reward.id:
            raise HTTPException(409, "This request was already used for a different reward.")
        return {"claim": public_claim(retry, reward), "alreadyClaimed": True}
    existing = db.scalar(
        select(RewardClaim).where(
            RewardClaim.user_id == owner.id, RewardClaim.reward_id == reward.id
        )
    )
    if existing:
        return {"claim": public_claim(existing, reward), "alreadyClaimed": True}
    if owner.points_balance < reward.points_cost:
        raise HTTPException(
            409, f"You need {reward.points_cost - owner.points_balance} more EcoPoints."
        )
    row = RewardClaim(
        user_id=owner.id,
        reward_id=reward.id,
        request_id=str(body.request_id),
        claim_code="SS-" + secrets.token_hex(8).upper(),
        points_spent=reward.points_cost,
    )
    db.add(row)
    db.flush()
    post_points(db, owner, -reward.points_cost, f"claim:{row.id}", f"Reward claim: {reward.title}")
    return {"claim": public_claim(row, reward), "alreadyClaimed": False}


@app.get("/api/reward-claims")
def reward_claims(user: CurrentUser, db: DB):
    return [
        public_claim(claim, reward)
        for claim, reward in db.execute(
            select(RewardClaim, Reward)
            .join(Reward)
            .where(RewardClaim.user_id == user.id)
            .order_by(RewardClaim.claimed_at.desc())
        ).all()
    ]


@app.post("/api/ai/chat", dependencies=write)
def chat(body: ChatInput, request: Request, db: DB):
    limiter.check(("chat", request.client.host), 8, 60)
    user_id = None
    if request.cookies.get(SESSION_COOKIE):
        try:
            user_id = require_user(request, db).id
        except HTTPException as error:
            if error.status_code != 401:
                raise
    with gemini_credentials.use_account_key(db, user_id):
        db.close()
        return {"answer": media.project_chat(body.question), "source": "gemini"}
