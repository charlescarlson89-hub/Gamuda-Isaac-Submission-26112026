import io
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import atlas_methods, gemini_credentials, media, recipe_formulation, security
from app.accounting import local_day
from app.batch_workflow import create_batch_record
from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import (
    Base,
    FertilizerType,
    GeminiCredential,
    PointsLedger,
    User,
    WasteFertilizerMatch,
    WasteType,
    WeeklyCheckinQuest,
    utcnow,
)
from app.schemas import BatchCreate, CompostVerification, Detection, VisionResult
from app.security import limiter
from app.seed_data import populate_catalogue

ORIGIN = "http://127.0.0.1:5173"
PASSWORD = "A-long-test-password-2026"


def photo(color="green"):
    data = io.BytesIO()
    Image.new("RGB", (100, 100), color).save(data, "PNG")
    return ("scraps.png", data.getvalue(), "image/png")


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db, db.begin():
        populate_catalogue(db)

    def override_db():
        with factory() as db:
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(media, "BACKEND_ROOT", tmp_path)
    monkeypatch.setattr(
        media,
        "get_settings",
        lambda: get_settings().model_copy(update={"upload_storage": "local", "app_env": "test"}),
    )
    limiter.events.clear()
    with TestClient(app, headers={"Origin": ORIGIN}) as client:
        client.db_factory = factory
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


def csrf(api):
    token = api.get("/api/auth/csrf").json()["csrfToken"]
    api.headers["X-CSRF-Token"] = token


def test_leaffy_chat_uses_existing_csrf_and_does_not_award_points(api, monkeypatch):
    register(api)
    before = state(api)["balance"]
    seen = []

    def answer(question):
        seen.append(question)
        return "Controlled SoilSync guide response."

    monkeypatch.setattr(media, "project_chat", answer)
    token = api.headers.pop("X-CSRF-Token")
    assert api.post("/api/ai/chat", json={"question": "How do batches work?"}).status_code == 403
    assert not seen
    api.headers["X-CSRF-Token"] = token
    response = api.post("/api/ai/chat", json={"question": "How do batches work?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Controlled SoilSync guide response.", "source": "gemini"}
    assert seen == ["How do batches work?"]
    assert state(api)["balance"] == before


@pytest.mark.parametrize("reply", ["Use the Fertilizer guide to start a named batch.", "", None])
def test_leaffy_gemini_contract_and_empty_response(api, monkeypatch, reply):
    from types import SimpleNamespace

    from fastapi import HTTPException

    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(text=reply)

    monkeypatch.setattr(
        media,
        "gemini_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    if reply:
        assert media.project_chat("Where do I start?") == reply
    else:
        with pytest.raises(HTTPException) as error:
            media.project_chat("Where do I start?")
        assert error.value.status_code == 503
    assert calls[0]["contents"] == "Where do I start?"
    config = calls[0]["config"]
    assert config.max_output_tokens == 400
    assert "Neon PostgreSQL" in config.system_instruction
    assert "Chat earns no points" in config.system_instruction
    assert "Never invent their balance" in config.system_instruction


def register(api, name="alice"):
    csrf(api)
    response = api.post(
        "/api/auth/register",
        json={
            "username": name,
            "email": f"{name}@soilsync.test",
            "password": PASSWORD,
            "location": "Kota Kinabalu",
            "accepted_terms": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["user"]


def state(api):
    response = api.get("/api/state")
    assert response.status_code == 200, response.text
    return response.json()


def test_personal_gemini_key_is_private_and_used_only_for_its_owner(api, monkeypatch):
    path = "/api/user-settings/gemini-key"
    assert api.get(path).status_code == 401
    alice = register(api)
    bob = register(api, "bob")
    settings = get_settings().model_copy(update={
        "gemini_personal_key_user_ids": [alice["id"]],
        "gemini_personal_key_encryption": SecretStr(Fernet.generate_key().decode()),
        "gemini_require_personal_key": True,
    })
    monkeypatch.setattr(gemini_credentials, "get_settings", lambda: settings)
    key = "fixture-key-for-alice-only"
    assert api.get(path).json() == {"available": False, "configured": False}
    assert api.post(path, json={"api_key": key}).status_code == 403

    def login_as(name):
        response = api.post("/api/auth/login", json={"identifier": name, "password": PASSWORD})
        assert response.status_code == 200

    def reply(_):
        assert gemini_credentials.active_key().get_secret_value() == key
        return "Personal key selected."

    monkeypatch.setattr(media, "project_chat", reply)
    login_as("alice")
    response = api.post(path, json={"api_key": key})
    assert response.json() == {"available": True, "configured": True}
    assert key not in response.text and key not in api.get(path).text
    with api.db_factory() as db:
        credential = db.get(GeminiCredential, alice["id"])
        assert key.encode() not in credential.encrypted_key
        assert db.get(GeminiCredential, bob["id"]) is None
    chat = "/api/ai/chat"
    assert api.post(chat, json={"question": "How does composting work?"}).status_code == 200
    assert gemini_credentials.active_key() is None
    login_as("bob")
    assert api.post(chat, json={"question": "How does composting work?"}).status_code == 503
    login_as("alice")
    assert api.delete(path).json() == {"available": True, "configured": False}
    assert api.post(chat, json={"question": "How does composting work?"}).status_code == 503


def mock_vision(monkeypatch, waste_id=1, confidence=0.94):
    monkeypatch.setattr(
        media,
        "detect_waste",
        lambda data, catalogue: VisionResult(
            items=[
                Detection(
                    waste_type_id=waste_id, detected_name="visible scraps", confidence=confidence
                )
            ],
            explanation="Test provider response, not a live AI call.",
        ),
    )


def test_demo_mode_reserves_live_ai_for_one_account(api, monkeypatch):
    presenter = register(api)
    register(api, "bob")
    mock_vision(monkeypatch)
    old_scan = api.post("/api/scans", files={"photo": photo()}).json()["scan"]
    batch = create_batch(api)
    settings = get_settings().model_copy(update={
        "gemini_demo_user_id": presenter["id"],
        "gemini_personal_key_user_ids": [presenter["id"]],
        "gemini_personal_key_encryption": SecretStr(Fernet.generate_key().decode()),
        "gemini_require_personal_key": True,
    })
    monkeypatch.setattr(gemini_credentials, "get_settings", lambda: settings)
    provider_calls = []

    def chat_reply(_):
        assert gemini_credentials.active_key() is None
        provider_calls.append("chat")
        return "Demo reply"

    def unexpected_call(*_, **__):
        pytest.fail("An account outside the demo called an AI provider")

    monkeypatch.setattr(media, "project_chat", chat_reply)
    monkeypatch.setattr(media, "detect_waste", unexpected_call)
    monkeypatch.setattr(media, "verify_compost", unexpected_call)
    monkeypatch.setattr(recipe_formulation, "suggest_mix", unexpected_call)
    chat = "/api/ai/chat"
    question = {"question": "What can I compost?"}
    assert api.post(chat, json=question).status_code == 403
    assert api.post("/api/scans", files={"photo": photo("blue")}).status_code == 403
    assert api.post(f"/api/scans/{old_scan['id']}/recipe-suggestion").status_code == 403
    assert api.post(
        f"/api/batches/{batch['id']}/quests/1/complete", files={"photo": photo()}
    ).status_code == 403
    assert api.get("/api/catalog").status_code == 200
    assert api.post("/api/daily-checkins").status_code == 200
    assert api.post("/api/auth/logout").status_code == 200
    csrf(api)
    guest_reply = api.post(chat, json=question)
    assert guest_reply.status_code == 403
    assert guest_reply.json()["detail"] == "Live AI is reserved for the SoilSync demo account."
    assert api.post("/api/auth/login", json={"identifier": "alice", "password": PASSWORD}).status_code == 200
    assert api.get("/api/user-settings/gemini-key").json() == {"available": False, "configured": False}
    assert api.post(chat, json=question).json() == {"answer": "Demo reply", "source": "gemini"}
    assert provider_calls == ["chat"]


def mock_compost(monkeypatch, verdict="compost", confidence=0.94):
    calls = []

    def verify(data, recipe_name, *, rice_water=False, week=None):
        calls.append((data, recipe_name, rice_water, week))
        return CompostVerification(
            verdict=verdict, confidence=confidence, reason="Controlled test provider response."
        )

    monkeypatch.setattr(media, "verify_compost", verify)
    return calls


def test_recipe_suggestion_uses_atlas_documents_and_rejects_unsafe_mixes(api, monkeypatch):
    register(api)
    monkeypatch.setattr(
        media,
        "detect_waste",
        lambda *_: VisionResult(
            items=[
                Detection(waste_type_id=32, detected_name="Papaya peel", confidence=.95),
                Detection(waste_type_id=2, detected_name="Coffee grounds", confidence=.93),
                Detection(waste_type_id=21, detected_name="Plastic wrapper", confidence=.92),
                Detection(waste_type_id=5, detected_name="Unclear object", confidence=.40),
            ],
            explanation="Fixture",
        ),
    )
    scan = api.post("/api/scans", files={"photo": photo()}).json()["scan"]
    path = f"/api/scans/{scan['id']}/recipe-suggestion"
    original_balance = state(api)["balance"]
    assert scan["items"][0]["description"]
    assert scan["items"][0]["fertilizer_ids"] == [4, 5, 6]
    documents = recipe_formulation.approved_documents()

    def find(query):
        assert query == {"_id": {"$in": [4, 5, 6]}}
        return documents

    monkeypatch.setattr(
        recipe_formulation,
        "get_settings",
        lambda: get_settings().model_copy(update={
            "mongodb_recipe_uri": SecretStr("mongodb://fixture"),
            "mongodb_recipe_database": "soilsync",
            "gemini_model": "fixture",
        }),
    )
    monkeypatch.setattr(
        recipe_formulation, "mongo_client",
        lambda _: {"soilsync": {"recipe_templates": SimpleNamespace(find=find)}},
    )
    suggestion = {
        "recipe_id": 5,
        "ingredients": [
            {"ingredient_id": 2, "percentage": 10},
            {"ingredient_id": 32, "percentage": 20},
            {"ingredient_id": 0, "percentage": 70},
        ],
    }

    def generate(**kwargs):
        assert "Plastic packaging" not in kwargs["contents"]
        assert "Carrot peels" not in kwargs["contents"]
        assert documents[1]["steps"][0] in kwargs["contents"]
        return SimpleNamespace(text=json.dumps(suggestion))

    monkeypatch.setattr(
        recipe_formulation, "gemini_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    response = api.post(path)
    assert response.status_code == 200, response.text
    mix = response.json()
    assert mix["recipeId"] == 5 and mix["basis"] == "mix_by_volume"
    assert [item["id"] for item in mix["ingredients"]] == [2, 32, 0]
    assert sum(item["percentage"] for item in mix["ingredients"]) == 100
    assert state(api)["balance"] == original_balance
    suggestion["ingredients"][-1]["percentage"] = 65
    suggestion["ingredients"][0]["percentage"] = 15
    assert api.post(path).status_code == 502  # Totals 100 but has too few browns.
    suggestion["ingredients"][0]["ingredient_id"] = 21
    assert api.post(path).status_code == 502  # Plastic is never in the mix.
    suggestion.update(recipe_id=6, ingredients=[
        {"ingredient_id": 2, "percentage": 30},
        {"ingredient_id": 32, "percentage": 70},
    ])
    bokashi = api.post(path).json()
    assert bokashi["basis"] == "food_scraps_by_volume"
    assert "kit" in bokashi["kitGuidance"]
    suggestion["ingredients"][0]["percentage"] = 29
    assert api.post(path).status_code == 502
    documents.pop()
    assert api.post(path).status_code == 503
    assert api.post("/api/auth/logout").status_code == 200
    register(api, name="bob")
    assert api.post(path).status_code == 404


@pytest.mark.parametrize(("slug", "recipe_id", "scrap_id", "scrap", "plant", "days", "weeks",
                          "allowed_label", "recipe_label"), [
    ("blender_slurry_soil_factory", 7, 32, "Papaya peels", "Pandan", 21, 3,
     "Fruit scraps (banana peels, papaya skins, watermelon rinds)", "Mixed fruit peels (papaya, dragonfruit)"),
    ("diy_rice_water_lab", 8, 2, "Coffee grounds", "Hibiscus", 28, 4,
     "Coffee grounds & tea leaves", "Spent coffee grounds"),
    ("cold_composting", 5, 40, "Cabbage trimmings", "Sawi", 180, 26,
     "Vegetable scraps", "Vegetable trimmings"),
])
def test_atlas_method_recommendation_and_scheduled_claims(
    api, monkeypatch, slug, recipe_id, scrap_id, scrap, plant, days, weeks, allowed_label, recipe_label
):
    from app import main

    start = date(2026, 11, 16)
    action_day = start
    monkeypatch.setattr("app.batch_workflow.utcnow", lambda: datetime(2026, 11, 16, tzinfo=timezone.utc))
    monkeypatch.setattr(main, "local_day", lambda: action_day)
    monkeypatch.setattr("app.serializers.local_day", lambda: action_day)
    register(api)
    method = atlas_methods.CompostMethod.model_validate({
        "recipe_id": recipe_id,
        "method_id": slug,
        "method_name": "Method from Atlas",
        "timeline_days": days,
        "suitable_food_waste": [allowed_label],
        "not_suitable_food_waste": ["Cooking oil"],
        "suitable_plants": [plant],
        "plants_to_avoid": [],
        "steps": [f"Atlas step {number}" for number in range(1, 7 if recipe_id == 7 else 6)],
        "recipes": [
            {
                "recipe_name": "Matching mix",
                "ingredients": [
                    {"item": recipe_label, "percentage": 30},
                    {"item": "Dry leaves", "percentage": 70},
                ],
            },
        ],
    })
    methods = {recipe_id: method}
    if recipe_id == 7:
        alternate = method.model_dump()
        alternate.update(
            recipe_id=4, method_id="hot_composting", method_name="Hot Composting",
            suitable_food_waste=["Fruit scraps"],
        )
        methods[4] = atlas_methods.CompostMethod.model_validate(alternate)
    monkeypatch.setattr(atlas_methods, "load_methods", lambda: methods)
    monkeypatch.setattr(media, "detect_waste", lambda *_: VisionResult(
        items=[Detection(waste_type_id=scrap_id, detected_name=scrap, confidence=.95)],
        explanation="Fixture",
    ))
    scan = api.post("/api/scans", files={"photo": photo()}).json()["scan"]
    reply = api.get(f"/api/scans/{scan['id']}/method-match")
    assert reply.status_code == 200, reply.text
    recommendation = reply.json()["recommendation"]
    assert recommendation["recipeId"] == recipe_id
    assert [option["recipeId"] for option in recommendation["alternatives"]] == (
        [4] if recipe_id == 7 else []
    )
    assert recommendation["matchedWaste"] == [scrap]
    assert recommendation["suitablePlants"] == [plant]
    assert [part["matched"] for part in recommendation["ingredients"]] == [True, False]
    assert sum(part["percentage"] for part in recommendation["ingredients"]) == 100
    guide = next(row for row in api.get("/api/catalog").json()["fertilizers"] if row["id"] == recipe_id)
    assert guide["plants"][0]["name"] == plant
    if recipe_id in {7, 8}:
        method_key = "blender" if recipe_id == 7 else "rice-water"
        assert [stage["imageKey"] for stage in guide["stages"]] == [
            f"{method_key}-{number}" for number in range(1, 4)
        ]
        assert [step["instruction"] for stage in guide["stages"] for step in stage["steps"]] == method.steps
        assert guide["guideCredit"] == "SoilSync recipe library"

    reply = api.post("/api/batches", json={
        "name": "Atlas recipe", "fertilizer_type_id": recipe_id,
        "client_request_id": str(uuid.uuid4()),
    })
    assert reply.status_code == 201, reply.text
    batch = reply.json()
    assert len(batch["quests"]) == weeks
    assert batch["quests"][-1]["availableOn"] == (start + timedelta(days=days)).isoformat()
    assert not batch["quests"][0]["canClaim"]
    path = f"/api/batches/{batch['id']}/quests/1/complete"
    assert api.post(path, files={"photo": photo()}).status_code == 409
    action_day = start + timedelta(days=7)
    calls = mock_compost(monkeypatch)
    reply = api.post(path, files={"photo": photo()})
    assert reply.status_code == 200, reply.text
    assert reply.json()["pointsAwarded"] == 100
    assert reply.json()["batch"]["progress"] == round(100 / weeks)
    assert calls[0][2:] == (recipe_id == 8, 1)
    assert api.post(path, files={"photo": photo()}).json()["pointsAwarded"] == 0


def create_batch(api, name="Kitchen", request_id=None):
    response = api.post(
        "/api/batches",
        json={
            "name": name,
            "fertilizer_type_id": 4,
            "client_request_id": request_id or str(uuid.uuid4()),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_featured_methods_require_compatible_neon_waste_and_atlas_mix(api, monkeypatch):
    register(api)
    methods = {}
    for slug, recipe_id in atlas_methods.METHOD_IDS.items():
        document = {
            "recipe_id": recipe_id,
            "method_id": slug,
            "method_name": slug,
            "timeline_days": 28,
            "suitable_food_waste": ["Plain cooked rice", "Plain cooked noodles"],
            "not_suitable_food_waste": ["Cooking oil"],
            "suitable_plants": ["Hibiscus"],
            "plants_to_avoid": [],
            "recipes": [{"recipe_name": "Mixed scraps", "ingredients": [
                {"item": "Plain cooked rice and noodles", "percentage": 60},
                {"item": "Shredded paper", "percentage": 40},
            ]}],
        }
        methods[recipe_id] = atlas_methods.CompostMethod.model_validate(document)
    monkeypatch.setattr(atlas_methods, "load_methods", lambda: methods)

    for waste_id, expected, featured_matches in ((57, 7, [True, True]), (59, 5, [False, False]), (24, None, [False, False])):
        monkeypatch.setattr(media, "detect_waste", lambda *_, waste_id=waste_id: VisionResult(
            items=[Detection(waste_type_id=waste_id, detected_name="Fixture material", confidence=.95)],
            explanation="Fixture",
        ))
        created = api.post("/api/scans", files={"photo": photo((waste_id, 108, 72))})
        assert created.status_code == 200
        scan_id = created.json()["scan"]["id"]
        response = api.get(f"/api/scans/{scan_id}/method-match")
        assert response.status_code == 200, response.text
        result = response.json()
        assert [row["id"] for row in result["featuredMethods"]] == [7, 8]
        assert [row["matchesScan"] for row in result["featuredMethods"]] == featured_matches
        assert (result["recommendation"] or {}).get("recipeId") == expected


def test_animal_scraps_are_only_matched_to_compatible_fermentation_methods(api, monkeypatch):
    register(api)
    methods = {}
    for slug, recipe_id in atlas_methods.METHOD_IDS.items():
        methods[recipe_id] = atlas_methods.CompostMethod.model_validate({
            "recipe_id": recipe_id,
            "method_id": slug,
            "method_name": slug,
            "timeline_days": 28,
            "suitable_food_waste": ["Fruit scraps", "Small meat or fish trimmings"],
            "not_suitable_food_waste": ["Large meat chunks or bones"],
            "suitable_plants": ["Hibiscus"],
            "plants_to_avoid": [],
            "recipes": [{
                "recipe_name": "Example plant mix",
                "ingredients": [{"item": "Fruit scraps", "percentage": 100}],
            }],
        })
    monkeypatch.setattr(atlas_methods, "load_methods", lambda: methods)
    for index, (waste_ids, expected) in enumerate([
        ((68,), [8, 6]), ((69, 1), [8, 6]), ((70,), [8, 6]), ((73,), [8, 6]), ((74,), [8]),
        ((71,), []), ((72,), []), ((22,), []),
    ]):
        monkeypatch.setattr(media, "detect_waste", lambda *_, waste_ids=waste_ids: VisionResult(
            items=[Detection(waste_type_id=waste_id, detected_name="Fixture material", confidence=.95)
                   for waste_id in waste_ids],
            explanation="Fixture",
        ))
        created = api.post("/api/scans", files={"photo": photo((index, 130, 90))})
        assert created.status_code == 200
        response = api.get(f"/api/scans/{created.json()['scan']['id']}/method-match")
        assert response.status_code == 200, response.text
        result = response.json()
        mix = result["recommendation"]
        matched_ids = [row["recipeId"] for row in [mix, *mix["alternatives"]]] if mix else []
        assert matched_ids == expected
        assert [row["matchesScan"] for row in result["featuredMethods"]] == [False, 8 in expected]


def test_scan_ignores_servingware_and_rejects_a_misidentified_fish_spine(api, monkeypatch):
    register(api)
    monkeypatch.setattr(media, "detect_waste", lambda *_: VisionResult(
        items=[
            Detection(waste_type_id=70, detected_name="Fish spine", confidence=.95),
            Detection(waste_type_id=70, detected_name="Small fish pin bones on the plate", confidence=.95),
            Detection(waste_type_id=None, detected_name="Plate", confidence=.98),
            Detection(waste_type_id=26, detected_name="Stainless steel knife", confidence=.98),
        ],
        explanation="Fixture",
    ))
    response = api.post("/api/scans", files={"photo": photo()})
    assert response.status_code == 200
    items = response.json()["scan"]["items"]
    assert [(item["waste_type_id"], item["is_supported"]) for item in items] == [(71, False), (73, True)]
    assert response.json()["pointsAwarded"] == 50
    assert state(api)["balance"] == 50


@pytest.mark.parametrize(("label", "catalogue_id", "stored_id", "points"), [
    ("Small tilapia bones", 70, 73, 50),
    ("Large tuna bone", 73, 71, 0),
    ("Tuna bone", 73, 71, 0),
    ("Small tilapia spine", 73, 71, 0),
    ("Separate chicken drumstick bone", 71, 74, 50),
    ("Chicken carcass", 74, 71, 0),
    ("Chicken backbone", 74, 71, 0),
    ("Fish bones", 70, None, 0),
])
def test_bone_scan_rewards_only_accepted_material(api, monkeypatch, label, catalogue_id, stored_id, points):
    register(api)
    monkeypatch.setattr(media, "detect_waste", lambda *_: VisionResult(
        items=[Detection(waste_type_id=catalogue_id, detected_name=label, confidence=.95)],
        explanation="Fixture",
    ))
    response = api.post("/api/scans", files={"photo": photo()})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["scan"]["items"][0]["waste_type_id"] == stored_id
    assert result["scan"]["items"][0]["is_supported"] == bool(points)
    assert result["scan"]["pointsEarned"] == result["pointsAwarded"] == points
    assert state(api)["balance"] == points


def test_database_photo_storage_is_private_and_removed_with_completed_batch(api, monkeypatch):
    from app import main
    from app.models import WeeklyCheckinQuest

    monkeypatch.setattr(main, "config", main.config.model_copy(update={"upload_storage": "postgres"}))
    register(api)
    mock_compost(monkeypatch)
    batch = create_batch(api)
    for week in (1, 2, 3):
        response = api.post(
            f"/api/batches/{batch['id']}/quests/{week}/complete",
            files={"photo": photo((week * 50, 80, 40))},
        )
        assert response.status_code == 200, response.text
        assert response.json()["pointsAwarded"] == 100
        assert "photo_data" not in response.text
    proof = response.json()["batch"]["checkins"][0]["photoUrl"]
    assert api.get(proof).headers["content-type"] == "image/jpeg"
    with api.db_factory() as db:
        saved = db.scalars(select(WeeklyCheckinQuest)).all()
        assert all(quest.photo_data and not quest.storage_key for quest in saved)
    assert not list(media.BACKEND_ROOT.rglob("*.jpg"))
    assert api.post("/api/auth/logout").status_code == 200
    register(api, "otherhouse")
    assert api.get(proof).status_code == 404
    assert api.post("/api/auth/logout").status_code == 200
    csrf(api)
    api.post("/api/auth/login", json={"identifier": "alice", "password": PASSWORD})
    assert api.delete(f"/api/batches/{batch['id']}").status_code == 200
    assert api.get(proof).status_code == 404
    with api.db_factory() as db:
        assert db.scalar(select(WeeklyCheckinQuest)) is None


def test_registration_password_hash_and_real_authentication(api):
    user = register(api)
    assert state(api)["balance"] == 0
    assert "password" not in user
    with api.db_factory() as db:
        saved = db.get(User, user["id"])
        assert saved.password.startswith("$argon2")
        assert PASSWORD not in saved.password
        assert saved.terms_version
    assert api.post("/api/auth/logout").status_code == 200
    assert api.get("/api/state").status_code == 401
    csrf(api)
    assert (
        api.post("/api/auth/login", json={"identifier": "alice", "password": "wrong"}).status_code
        == 401
    )
    assert (
        api.post(
            "/api/auth/login", json={"identifier": "ALICE@SOILSYNC.TEST", "password": PASSWORD}
        ).status_code
        == 200
    )
    assert state(api)["profile"]["id"] == user["id"]


def test_registration_requires_consent_and_does_not_echo_password(api):
    csrf(api)
    body = {
        "username": "alice",
        "email": "alice@soilsync.test",
        "password": "tiny",
        "location": "KK",
        "accepted_terms": False,
    }
    response = api.post("/api/auth/register", json=body)
    assert response.status_code == 422
    assert '"input"' not in response.text
    assert "tiny" not in response.text
    assert api.get("/api/auth/me").status_code == 401


def test_csrf_and_origin_are_required_even_on_login(api):
    assert (
        api.post("/api/auth/login", json={"identifier": "alice", "password": PASSWORD}).status_code
        == 403
    )
    csrf(api)
    assert (
        api.post(
            "/api/auth/login",
            headers={"Origin": "https://untrusted.example"},
            json={"identifier": "alice", "password": PASSWORD},
        ).status_code
        == 403
    )


def test_daily_checkin_is_idempotent_and_balances_are_server_owned(api):
    register(api)
    assert api.post("/api/daily-checkins").json()["pointsAwarded"] == 10
    assert api.post("/api/daily-checkins").json()["pointsAwarded"] == 0
    assert state(api)["balance"] == 10
    assert (
        api.patch(
            "/api/profile", json={"username": "alice", "location": "KK", "points_balance": 99999}
        ).status_code
        == 422
    )
    ledger = api.get("/api/points-ledger").json()
    assert sum(row["points"] for row in ledger["entries"]) == 10


def test_catalogue_and_profile_preferences_are_database_backed(api):
    register(api)
    catalog = api.get("/api/catalog").json()
    waste = {row["id"]: row for row in catalog["wasteTypes"]}
    assert len(waste) == 74
    assert waste[73]["name"] == "Small fish bones"
    assert waste[74]["name"] == "Separate chicken bones"
    assert waste[1]["name"] == "Banana peels"
    assert waste[31]["name"] == "Whole Potato"
    assert waste[32]["name"] == "Papaya peels"
    assert "betik peel" in waste[32]["aliases"]
    assert waste[48]["ingredient_role"] == "brown"
    assert waste[50]["is_supported"] is False
    assert waste[57]["name"] == "Plain cooked rice"
    assert waste[67]["is_supported"] is False
    assert "local service" in waste[50]["guide_recommendation"]
    assert all(row["description"] for row in waste.values())
    assert len(catalog["rewards"]) == 26
    assert {row["id"]: row["cost"] for row in catalog["rewards"] if row["id"].startswith("coffee-")} == {
        "coffee-cup": 40, "coffee-beans": 75, "coffee-grounds": 30
    }
    rewards = {row["id"]: row for row in catalog["rewards"]}
    for slug, cost in {"vinda-tissue": 60, "vinda-kitchen-paper": 90, "petpet-diapers": 150}.items():
        assert rewards[slug]["cost"] == cost
        assert rewards[slug]["prototypeOnly"] is True
        assert "renewable plant fibres" in rewards[slug]["description"]
    assert len(catalog["fertilizers"]) == 3
    assert all(reward["category"] == "partner" for reward in catalog["rewards"])
    assert len(catalog["fertilizers"][0]["steps"]) == 7
    assert (
        api.patch(
            "/api/user-settings", json={"checkin_reminder": False, "quiet_hours_start": "21:30"}
        ).status_code
        == 200
    )
    assert state(api)["preferences"]["checkin"] is False
    assert state(api)["quietHours"]["start"] == "21:30"
    assert api.patch("/api/user-settings", json={"quiet_hours_start": "99:00"}).status_code == 422
    assert (
        api.patch(
            "/api/profile", json={"username": "alice_updated", "location": "Penampang"}
        ).status_code
        == 200
    )
    assert state(api)["profile"]["location"] == "Penampang"


def test_vision_resolves_only_database_ids_and_never_double_awards(api, monkeypatch):
    register(api)
    mock_vision(monkeypatch)
    result = api.post("/api/scans", files={"photo": photo()})
    assert result.status_code == 200, result.text
    assert result.json()["pointsAwarded"] == 50
    assert result.json()["scan"]["items"][0]["name"] == "Banana peels"
    assert result.json()["scan"]["fertilizer_ids"]
    scan = result.json()["scan"]
    assert scan["items"][0]["waste_type_id"] == 1
    assert scan["items"][0]["fertilizer_ids"] == scan["fertilizer_ids"]
    for recipe in scan["fertilizers"]:
        assert recipe == api.get(f"/api/fertilizers/{recipe['id']}").json()
        assert recipe["steps"] and recipe["plants"]
    again = api.post("/api/scans", files={"photo": photo()})
    assert again.json()["duplicate"] is True
    assert again.json()["pointsAwarded"] == 0
    assert state(api)["balance"] == 50
    assert len(api.get("/api/scans").json()) == 1


@pytest.mark.parametrize("waste_id, confidence", [(9999, 0.95), (1, 0.2), (None, 0.5)])
def test_unknown_or_uncertain_material_never_mints_scan_points(
    api, monkeypatch, waste_id, confidence
):
    register(api)
    mock_vision(monkeypatch, waste_id, confidence)
    result = api.post("/api/scans", files={"photo": photo()})
    assert result.status_code == 200, result.text
    assert result.json()["pointsAwarded"] == 0
    assert result.json()["scan"]["items"][0]["is_supported"] is False
    assert state(api)["balance"] == 0


def test_unsupported_waste_uses_catalogue_rejection_guidance(api, monkeypatch):
    register(api)
    mock_vision(monkeypatch, 21)
    result = api.post("/api/scans", files={"photo": photo()}).json()
    assert result["scan"]["items"][0]["name"] == "Plastic packaging"
    assert result["scan"]["items"][0]["is_supported"] is False
    assert result["scan"]["fertilizer_ids"] == []
    assert result["pointsAwarded"] == result["scan"]["pointsEarned"] == state(api)["balance"] == 0


def test_invalid_image_and_provider_failure_leave_no_scan_or_points(api, monkeypatch):
    from fastapi import HTTPException

    register(api)
    assert (
        api.post(
            "/api/scans", files={"photo": ("fake.png", b"not an image", "image/png")}
        ).status_code
        == 422
    )

    def unavailable(*args):
        raise HTTPException(503, "Provider unavailable")

    monkeypatch.setattr(media, "detect_waste", unavailable)
    assert api.post("/api/scans", files={"photo": photo()}).status_code == 503
    assert state(api)["balance"] == 0
    assert api.get("/api/scans").json() == []


def test_open_checkins_can_be_completed_out_of_order_without_resetting_a_completed_week(api, monkeypatch):
    owner_id = register(api)["id"]
    with api.db_factory() as db, db.begin():
        body = BatchCreate(name="test batch", fertilizer_type_id=8, client_request_id=uuid.uuid4())
        batch = create_batch_record(
            db, db.get(User, owner_id), db.get(FertilizerType, 8),
            body, SimpleNamespace(timeline_days=28), started_at=utcnow() - timedelta(days=28),
        )
        batch_id = batch.id
        for quest in db.scalars(select(WeeklyCheckinQuest).where(WeeklyCheckinQuest.batch_id == batch_id)):
            quest.status = "CURRENT"

    order = (4, 2, 1, 3)
    calls = mock_compost(monkeypatch)
    completed = set()
    for week in order:
        path = f"/api/batches/{batch_id}/quests/{week}/complete"
        response = api.post(path, files={"photo": photo((week * 30, 90, 40))})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["pointsAwarded"] == 100
        completed.add(week)
        assert {quest["week"] for quest in result["batch"]["quests"] if quest["status"] == "DONE"} == completed
        assert api.post(path, files={"photo": photo()}).json()["pointsAwarded"] == 0
    assert [call[2:] for call in calls] == [(True, week) for week in order]
    assert result["batch"]["status"] == "Completed"
    assert state(api)["balance"] == 400


def test_image_only_checkins_keep_schedule_and_points_without_ai(api, monkeypatch):
    registered = register(api)
    with api.db_factory() as db, db.begin():
        owner = db.get(User, registered["id"])
        recipe = db.get(FertilizerType, 8)
        body = BatchCreate(name="Rice water", fertilizer_type_id=8, client_request_id=uuid.uuid4())
        batch = create_batch_record(
            db, owner, recipe, body, SimpleNamespace(timeline_days=14),
            started_at=utcnow() - timedelta(days=6), image_only=True,
        )
        batch_id = batch.id

    path = f"/api/batches/{batch_id}/quests"
    monkeypatch.setattr(media, "verify_compost", lambda *_: pytest.fail("AI must not be called"))
    assert api.post(f"{path}/1/complete", files={"photo": photo()}).status_code == 409

    with api.db_factory() as db, db.begin():
        for quest in db.scalars(select(WeeklyCheckinQuest).where(WeeklyCheckinQuest.batch_id == batch_id)):
            quest.available_on = local_day()

    assert api.post(f"{path}/2/complete", files={"photo": photo()}).status_code == 409
    invalid = ("invalid.png", b"not an image", "image/png")
    assert api.post(f"{path}/1/complete", files={"photo": invalid}).status_code == 422
    for week in (1, 2):
        response = api.post(f"{path}/{week}/complete", files={"photo": photo()})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["pointsAwarded"] == 100
        assert result["batch"]["quests"][week - 1]["imageOnly"] is True
        assert result["batch"]["checkins"][-1]["verification"]["status"] == "recorded"
        assert api.get(result["batch"]["checkins"][-1]["photoUrl"]).status_code == 200
        assert api.post(f"{path}/{week}/complete", files={"photo": photo()}).json()["pointsAwarded"] == 0
    assert result["batch"]["status"] == "Completed"
    assert state(api)["balance"] == 200


def test_multiple_batches_photo_quests_awards_and_completed_only_deletion(api, monkeypatch):
    register(api)
    calls = mock_compost(monkeypatch)
    request_id = str(uuid.uuid4())
    first = create_batch(api, request_id=request_id)
    assert create_batch(api, request_id=request_id)["id"] == first["id"]
    second = create_batch(api, "Garden")
    assert api.delete(f"/api/batches/{first['id']}").status_code == 409
    assert (
        api.post(
            f"/api/batches/{first['id']}/quests/2/complete", files={"photo": photo()}
        ).status_code
        == 409
    )
    for week in (1, 2, 3):
        completed = api.post(
            f"/api/batches/{first['id']}/quests/{week}/complete",
            files={"photo": photo((week * 50, 80, 40))},
            data={"note": f"Observation {week}"},
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["pointsAwarded"] == 100
        proof = completed.json()["batch"]["checkins"][-1]
        assert proof["verification"]["status"] == "approved"
        assert proof["verification"]["provider"] == "gemini"
    assert (
        api.post(f"/api/batches/{first['id']}/quests/1/complete", files={"photo": photo()}).json()[
            "pointsAwarded"
        ]
        == 0
    )
    data = state(api)
    assert data["balance"] == 300
    assert data["batches"][0]["progress"] == 100
    assert data["batches"][1]["progress"] == 0
    proof = data["batches"][0]["checkins"][0]["photoUrl"]
    assert api.get(proof).headers["content-type"] == "image/jpeg"
    assert api.delete(f"/api/batches/{first['id']}").status_code == 200
    assert [row["id"] for row in state(api)["batches"]] == [second["id"]]
    assert state(api)["balance"] == 300
    assert len(calls) == 3  # Completed retries never invoke AI or award again.
    assert api.get(proof).status_code == 404


def test_users_cannot_read_or_mutate_each_others_batches_photos_or_scans(api, monkeypatch):
    register(api)
    mock_compost(monkeypatch)
    batch = create_batch(api)
    api.post(f"/api/batches/{batch['id']}/quests/1/complete", files={"photo": photo()})
    proof = state(api)["batches"][0]["checkins"][0]["photoUrl"]
    mock_vision(monkeypatch)
    scan_id = api.post("/api/scans", files={"photo": photo()}).json()["scan"]["id"]
    api.post("/api/auth/logout")
    register(api, "bob")
    assert api.get(f"/api/batches/{batch['id']}").status_code == 404
    assert api.delete(f"/api/batches/{batch['id']}").status_code == 404
    assert (
        api.post(
            f"/api/batches/{batch['id']}/quests/2/complete", files={"photo": photo()}
        ).status_code
        == 404
    )
    assert api.get(proof).status_code == 404
    assert api.get(f"/api/scans/{scan_id}").status_code == 404
    assert state(api)["balance"] == 0
    assert state(api)["batches"] == []


def test_reward_claims_are_one_time_and_retries_do_not_spend_again(api, monkeypatch):
    register(api)
    request_id = str(uuid.uuid4())
    assert (
        api.post("/api/rewards/eco-bag/claims", json={"request_id": request_id}).status_code == 409
    )
    mock_vision(monkeypatch)
    api.post("/api/scans", files={"photo": photo()})
    first = api.post("/api/rewards/eco-bag/claims", json={"request_id": request_id})
    assert first.status_code == 200, first.text
    assert first.json()["claim"]["claimCode"].startswith("SS-")
    assert state(api)["balance"] == 0
    again = api.post("/api/rewards/eco-bag/claims", json={"request_id": str(uuid.uuid4())})
    assert again.json()["alreadyClaimed"] is True
    assert again.json()["claim"]["id"] == first.json()["claim"]["id"]
    assert len(api.get("/api/reward-claims").json()) == 1
    assert state(api)["balance"] == 0
    with api.db_factory() as db:
        assert sum(db.scalars(select(PointsLedger.points))) == 0


def test_logout_revokes_copied_session_cookie(api):
    register(api)
    token = api.cookies.get("soilsync_session")
    api.post("/api/auth/logout")
    api.cookies.set("soilsync_session", token)
    assert api.get("/api/auth/me").status_code == 401


def test_scan_uses_current_database_ids_and_links_not_hardcoded_banana_id(api, monkeypatch):
    register(api)
    with api.db_factory() as db, db.begin():
        db.add(
            WasteType(
                id=101, name="Locally catalogued peel", category="Fruit Scrap", is_supported=True
            )
        )
        db.flush()
        db.add(WasteFertilizerMatch(waste_type_id=101, fertilizer_type_id=5))
    mock_vision(monkeypatch, 101)
    result = api.post("/api/scans", files={"photo": photo()}).json()["scan"]
    assert result["items"][0]["waste_type_id"] == 101
    assert result["items"][0]["name"] == "Locally catalogued peel"
    assert result["fertilizer_ids"] == [5]
    assert [recipe["id"] for recipe in result["fertilizers"]] == [5]
    assert result["fertilizers"][0]["steps"] and result["fertilizers"][0]["plants"]


@pytest.mark.parametrize(
    "verdict,confidence", [("not_compost", 0.99), ("uncertain", 0.99), ("compost", 0.79)]
)
def test_unapproved_weekly_photo_cannot_change_progress_wallet_or_storage(
    api, monkeypatch, verdict, confidence
):
    register(api)
    batch = create_batch(api)
    mock_compost(monkeypatch, verdict, confidence)
    response = api.post(f"/api/batches/{batch['id']}/quests/1/complete", files={"photo": photo()})
    assert response.status_code == 422
    snapshot = state(api)
    assert snapshot["balance"] == 0
    assert snapshot["batches"][0]["progress"] == 0
    assert snapshot["batches"][0]["checkins"] == []
    assert snapshot["batches"][0]["quests"][0]["status"] == "CURRENT"
    assert not list(media.BACKEND_ROOT.rglob("*.jpg"))


def test_reusing_approved_photo_in_later_week_or_other_batch_is_blocked(api, monkeypatch):
    register(api)
    first, second = create_batch(api), create_batch(api, "Garden")
    calls = mock_compost(monkeypatch)
    path = f"/api/batches/{first['id']}/quests"
    assert api.post(path + "/1/complete", files={"photo": photo()}).status_code == 200
    assert api.post(path + "/2/complete", files={"photo": photo()}).status_code == 409
    assert (
        api.post(
            f"/api/batches/{second['id']}/quests/1/complete", files={"photo": photo()}
        ).status_code
        == 409
    )
    assert len(calls) == 1
    assert state(api)["balance"] == 100
    assert [b["progress"] for b in state(api)["batches"]] == [33, 0]


def test_weekly_provider_failure_and_storage_failure_leave_quest_pending(api, monkeypatch):
    from fastapi import HTTPException

    register(api)
    batch = create_batch(api)
    path = f"/api/batches/{batch['id']}/quests/1/complete"

    def unavailable(*args, **kwargs):
        raise HTTPException(503, "Service unavailable")

    monkeypatch.setattr(media, "verify_compost", unavailable)
    assert api.post(path, files={"photo": photo()}).status_code == 503
    mock_compost(monkeypatch)
    monkeypatch.setattr(media, "save_photo", unavailable)
    assert api.post(path, files={"photo": photo()}).status_code == 503
    assert state(api)["balance"] == 0
    assert state(api)["batches"][0]["checkins"] == []


def test_weekly_bad_image_never_calls_ai_and_threshold_boundary_can_approve(api, monkeypatch):
    register(api)
    batch = create_batch(api)
    calls = mock_compost(monkeypatch, confidence=0.8)
    path = f"/api/batches/{batch['id']}/quests/1/complete"
    assert (
        api.post(path, files={"photo": ("fake.png", b"not an image", "image/png")}).status_code
        == 422
    )
    assert not calls
    assert api.post(path, files={"photo": photo()}).status_code == 200
    assert state(api)["balance"] == 100


@pytest.mark.parametrize(
    "payload,status",
    [
        ('{"verdict":"compost","confidence":0.9,"reason":"Visible decomposing mixture"}', 200),
        ('{"verdict":"compost","confidence":2,"reason":"Invalid"}', 502),
        ('{"verdict":"yes","confidence":0.9,"reason":"Invalid"}', 502),
        ("not-json", 502),
    ],
)
def test_gemini_compost_adapter_validates_structured_response(api, monkeypatch, payload, status):
    from types import SimpleNamespace

    from fastapi import HTTPException

    settings = get_settings().model_copy(update={"gemini_model": "configured-test-model"})
    monkeypatch.setattr(media, "get_settings", lambda: settings)
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(text=payload)

    monkeypatch.setattr(
        media,
        "gemini_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    if status == 200:
        assert media.verify_compost(b"synthetic test bytes", "Home compost").verdict == "compost"
    else:
        with pytest.raises(HTTPException) as error:
            media.verify_compost(b"synthetic test bytes", "Home compost")
        assert error.value.status_code == status
    assert calls[0]["config"].response_schema is None
    assert calls[0]["config"].response_json_schema == CompostVerification.model_json_schema()


@pytest.mark.parametrize(("kind", "week"), [
    ("waste", None), ("compost", 1), ("rice_water", 1),
    ("rice_water", 2), ("rice_water", 3), ("rice_water", 4),
])
def test_gemini_image_requests_send_json_schema_on_the_actual_sdk_wire(api, monkeypatch, kind, week):
    import json
    from types import SimpleNamespace

    import httpx
    from google import genai
    from google.genai import types

    schema = VisionResult if kind == "waste" else CompostVerification
    payload = (
        {"items": [], "explanation": "Controlled test image."}
        if kind == "waste"
        else {
            "verdict": "compost" if kind.startswith("rice_water") else "not_compost",
            "confidence": 0.99,
            "reason": "Controlled test image.",
        }
    )
    requests = []

    def handle(request):
        requests.append(request)
        body = json.loads(request.content)
        config = body["generationConfig"]
        assert "responseSchema" not in config
        assert config["responseJsonSchema"] == schema.model_json_schema()
        assert config["responseJsonSchema"]["additionalProperties"] is False
        image = body["contents"][0]["parts"][1]["inlineData"]
        assert image.get("mimeType", image.get("mime_type")) == "image/jpeg"
        if kind != "waste":
            prompt = body["contents"][0]["parts"][0]["text"]
            starter_guidance = kind == "rice_water" and week == 1
            scraps_guidance = kind == "rice_water" and week in {2, 3, 4}
            assert ("pale cloudy or milky liquid" in prompt) == starter_guidance
            assert ("Visible solid scraps are not required" in prompt) == starter_guidance
            assert ("pale yellow liquid layer" in prompt) == starter_guidance
            assert ("closed transparent jar is acceptable" in prompt) == starter_guidance
            assert ("clearly visible collection of discarded food scraps" in prompt) == scraps_guidance
            if starter_guidance:
                assert "plain clear water" in prompt
            if scraps_guidance:
                assert "Starter liquid alone" in prompt
                assert "does not qualify for this check-in" in prompt
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": json.dumps(payload)}], "role": "model"},
                        "finishReason": "STOP",
                    }
                ]
            },
        )

    # MockTransport intercepts the real SDK request: no network or real API key.
    client = genai.Client(
        api_key="fixture-key",
        http_options=types.HttpOptions(client_args={"transport": httpx.MockTransport(handle)}),
    )
    monkeypatch.setattr(media, "gemini_client", lambda: client)
    monkeypatch.setattr(
        media,
        "get_settings",
        lambda: get_settings().model_copy(update={"gemini_model": "fixture-model"}),
    )
    try:
        if kind == "waste":
            result = media.detect_waste(
                b"fixture-image",
                [SimpleNamespace(id=1, name="Banana peels", category="Fruit Scrap")],
            )
            assert result.items == []
        elif kind == "compost":
            assert media.verify_compost(b"fixture-image", "Home compost").verdict == "not_compost"
        else:
            result = media.verify_compost(b"fixture-image", "DIY Rice Water", rice_water=True, week=week)
            assert result.verdict == "compost"
    finally:
        client.close()
    assert len(requests) == 1


def allow_admins(monkeypatch, ids):
    settings = get_settings().model_copy(update={"admin_user_ids": ids})
    monkeypatch.setattr(security, "get_settings", lambda: settings)


def test_admin_directory_requires_login_and_explicit_admin_access(api, monkeypatch):
    allow_admins(monkeypatch, [])
    assert api.get("/api/admin/users").status_code == 401
    user = register(api)
    response = api.get("/api/admin/users")
    assert response.status_code == 403
    assert "users" not in response.json()
    # A caller cannot grant themselves access using a parameter or header.
    assert (
        api.get(
            f"/api/admin/users?admin_user_id={user['id']}", headers={"X-Admin": "true"}
        ).status_code
        == 403
    )


def test_admin_directory_returns_only_ids_and_usernames(api, monkeypatch):
    alice = register(api)
    bob = register(api, "bob")
    allow_admins(monkeypatch, [alice["id"]])
    assert api.get("/api/admin/users").status_code == 403  # Bob is signed in.
    assert (
        api.post("/api/auth/login", json={"identifier": "alice", "password": PASSWORD}).status_code
        == 200
    )
    response = api.get("/api/admin/users")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "users": [
            {"id": alice["id"], "username": "alice"},
            {"id": bob["id"], "username": "bob"},
        ],
        "total": 2,
        "offset": 0,
        "limit": 50,
        "has_more": False,
    }
    assert PASSWORD not in response.text
    assert "@soilsync.test" not in response.text
    assert "$argon2" not in response.text


def test_admin_directory_pagination_is_ordered_and_bounded(api, monkeypatch):
    users = [register(api, name) for name in ("alice", "bob", "carol")]
    allow_admins(monkeypatch, [users[-1]["id"]])
    for offset, user in enumerate(users):
        page = api.get(f"/api/admin/users?limit=1&offset={offset}").json()
        assert page["users"] == [{"id": user["id"], "username": user["username"]}]
        assert page["total"] == 3
        assert page["offset"] == offset
        assert page["limit"] == 1
        assert page["has_more"] == (offset < 2)
    page = api.get("/api/admin/users?limit=1&offset=3").json()
    assert page["users"] == []
    assert page["has_more"] is False
    for query in ("limit=0", "limit=101", "offset=-1"):
        assert api.get(f"/api/admin/users?{query}").status_code == 422


def test_admin_directory_access_is_revoked_with_allowlist_or_session(api, monkeypatch):
    user = register(api)
    allow_admins(monkeypatch, [user["id"]])
    assert api.get("/api/admin/users").status_code == 200
    allow_admins(monkeypatch, [])
    assert api.get("/api/admin/users").status_code == 403
    allow_admins(monkeypatch, [user["id"]])
    assert api.post("/api/auth/logout").status_code == 200
    assert api.get("/api/admin/users").status_code == 401


def test_admin_directory_is_documented_with_an_explicit_response_schema(api):
    schema = api.get("/openapi.json").json()
    operation = schema["paths"]["/api/admin/users"]["get"]
    assert operation["tags"] == ["Admin"]
    assert {"200", "401", "403", "422"} <= set(operation["responses"])
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AdminUserList"
    }
    assert set(schema["components"]["schemas"]["AdminUserSummary"]["properties"]) == {
        "id",
        "username",
    }


def test_operator_password_recovery_revokes_only_target_sessions_and_keeps_progress(api):
    from pydantic import SecretStr

    from app.models import AuthSession
    from scripts.reset_password import reset_account_password

    alice = register(api)
    assert api.post("/api/daily-checkins").status_code == 200
    batch = create_batch(api)
    bob = register(api, "bob")
    new_password = "A-new-private-test-password-2026"
    with api.db_factory() as db, db.begin():
        assert reset_account_password(db, alice["id"], SecretStr(new_password)) == "alice"
    with api.db_factory() as db:
        saved = db.get(User, alice["id"])
        assert saved.password.startswith("$argon2")
        assert security.passwords.verify(new_password, saved.password)
        assert new_password not in saved.password
        assert saved.points_balance == 10
        assert not list(db.scalars(select(AuthSession).where(AuthSession.user_id == alice["id"])))
        assert (
            len(list(db.scalars(select(AuthSession).where(AuthSession.user_id == bob["id"])))) == 1
        )
        assert security.passwords.verify(PASSWORD, db.get(User, bob["id"]).password)
    assert api.get("/api/auth/me").json()["user"]["id"] == bob["id"]
    assert (
        api.post("/api/auth/login", json={"identifier": "alice", "password": PASSWORD}).status_code
        == 401
    )
    assert (
        api.post(
            "/api/auth/login", json={"identifier": "alice", "password": new_password}
        ).status_code
        == 200
    )
    assert state(api)["balance"] == 10
    assert state(api)["batches"][0]["id"] == batch["id"]


def test_operator_password_recovery_rejects_invalid_input_without_changing_account(api):
    from pydantic import SecretStr

    from scripts.reset_password import reset_account_password

    user = register(api)
    with api.db_factory() as db:
        original_hash = db.get(User, user["id"]).password
    for user_id, password in ((user["id"], "too-short"), (9999, "A-valid-test-password-2026")):
        with pytest.raises(ValueError), api.db_factory() as db, db.begin():
            reset_account_password(db, user_id, SecretStr(password))
    with api.db_factory() as db:
        assert db.get(User, user["id"]).password == original_hash
    assert api.get("/api/auth/me").status_code == 200


def test_operator_password_recovery_password_and_session_changes_rollback_together(api):
    from pydantic import SecretStr

    from scripts.reset_password import reset_account_password

    user = register(api)
    with api.db_factory() as db:
        original_hash = db.get(User, user["id"]).password
    with pytest.raises(RuntimeError), api.db_factory() as db, db.begin():
        reset_account_password(db, user["id"], SecretStr("A-valid-test-password-2026"))
        raise RuntimeError("Simulated transaction failure")
    with api.db_factory() as db:
        assert db.get(User, user["id"]).password == original_hash
    assert api.get("/api/auth/me").status_code == 200


def test_operator_password_recovery_refuses_non_interactive_input(monkeypatch, capsys):
    import io

    from scripts import reset_password

    monkeypatch.setattr("sys.argv", ["reset_password.py", "--user-id", "26"])
    monkeypatch.setattr("sys.stdin", io.StringIO("must-not-be-used-as-a-password"))
    monkeypatch.setattr(
        reset_password, "session_factory", lambda: pytest.fail("Database must not be opened")
    )
    assert reset_password.main() == 1
    output = capsys.readouterr().out
    assert "interactive terminal" in output
    assert "must-not-be-used-as-a-password" not in output


def test_only_approved_methods_have_three_complete_illustrated_stages(api):
    recipes = api.get("/api/catalog").json()["fertilizers"]
    assert [(r["id"], r["name"]) for r in recipes] == [(4, "Hot Composting"), (5, "Cold Composting"), (6, "Bokashi Composting")]
    for recipe in recipes:
        assert len(recipe["stages"]) == 3
        assert [step for stage in recipe["stages"] for step in stage["steps"]] == recipe["steps"]
        assert all(stage["imageKey"].startswith(recipe["method"]) for stage in recipe["stages"])
        assert all(stage["steps"] for stage in recipe["stages"])
        assert recipe["active"] and recipe["sources"] and recipe["timeline"]
    bokashi = recipes[2]
    assert "pre-compost" in bokashi["steps"][5]["instruction"]
    assert "roots" in bokashi["steps"][6]["instruction"]
    assert "sealed" in bokashi["maintenance"]["cadence"]


@pytest.mark.parametrize("waste_id,expected", [(1, [4, 5, 6]), (16, [4, 5]), (21, [])])
def test_scans_match_only_current_methods_and_respect_bokashi_materials(api, monkeypatch, waste_id, expected):
    register(api)
    mock_vision(monkeypatch, waste_id=waste_id)
    result = api.post("/api/scans", files={"photo": photo()}).json()["scan"]
    assert result["fertilizer_ids"] == expected
    assert result["items"][0]["fertilizer_ids"] == expected


def test_legacy_batch_and_scan_history_keep_their_identity(api):
    from app.models import Batch, FertilizerType, ScanLog
    user = register(api)
    with api.db_factory() as db, db.begin():
        old = db.get(FertilizerType, 2)
        assert old.name == "Worm compost"
        db.add(Batch(user_id=user["id"], fertilizer_type_id=2, batch_number="Legacy batch", name="Original worm bin", client_request_id="legacy-batch"))
        db.add(ScanLog(user_id=user["id"], waste_type_id=1, image_sha256="a"*64, points_earned=0, model_name="old-fixture", result={"items": [{"waste_type_id": 1, "is_supported": True}], "fertilizer_ids": [1, 2]}))
    current = state(api)
    assert current["batches"][0]["fertilizerTypeId"] == 2
    assert current["batches"][0]["fertilizerName"] == "Worm compost"
    assert current["scan"]["fertilizer_ids"] == [4, 5, 6]
    assert current["balance"] == 0
    with api.db_factory() as db:
        assert db.scalar(select(ScanLog)).result["fertilizer_ids"] == [1, 2]
    assert api.post("/api/batches", json={"name": "Not a new method", "fertilizer_type_id": 2, "client_request_id": str(uuid.uuid4())}).status_code == 404


def test_reseeding_keeps_existing_recipe_edits_and_batch_references(api):
    from app.models import FertilizerRecipeStep, FertilizerType
    with api.db_factory() as db, db.begin():
        legacy = db.get(FertilizerType, 1)
        legacy.description = "Preserved historical instructions"
        before = len(list(db.scalars(select(FertilizerRecipeStep))))
        populate_catalogue(db)
        populate_catalogue(db)
        assert db.get(FertilizerType, 1).description == "Preserved historical instructions"
        assert len(list(db.scalars(select(FertilizerRecipeStep)))) == before


def test_seed_refuses_to_reassign_a_reserved_recipe_id(api):
    from app.models import FertilizerType
    with api.db_factory() as db, db.begin():
        db.get(FertilizerType, 4).name = "Teammate's different recipe"
        db.flush()
        with pytest.raises(RuntimeError, match="already belongs"):
            populate_catalogue(db)
        assert db.get(FertilizerType, 4).name == "Teammate's different recipe"
