"""Opt-in live local test: creates then removes two synthetic QA accounts.

Run only against soilsync_remake_test with the local app and Storage emulator running.
Live approvals require --compost-photos with three distinct real photos.
Without them no live AI call is made when a key is configured.
"""

import argparse
import io
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from PIL import Image
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url

from app import media
from app.config import get_settings
from app.database import session_factory
from app.models import Batch, User, WeeklyCheckinQuest

parser = argparse.ArgumentParser()
parser.add_argument("--compost-photos", nargs=3, type=Path, metavar="PHOTO")
args = parser.parse_args()
proof_uploads = []
for path in args.compost_photos or []:
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(path.suffix.lower())
    if not mime or not path.is_file():
        parser.error("Supply three distinct real JPEG, PNG or WebP compost photos.")
    proof_uploads.append((path.name, path.read_bytes(), mime))
settings = get_settings()
if (
    settings.app_env == "production"
    or make_url(settings.database_url.get_secret_value()).database != "soilsync_remake_test"
):
    raise SystemExit("Live smoke test is restricted to soilsync_remake_test outside production.")

base = "http://127.0.0.1:5173"
users = []
clients = []


def check(condition, message):
    assert condition, message
    print("PASS", message)


def new_account():
    name = "qa_" + uuid.uuid4().hex[:14]
    client = httpx.Client(base_url=base, headers={"Origin": base}, timeout=90)
    clients.append(client)
    client.headers["X-CSRF-Token"] = client.get("/api/auth/csrf").json()["csrfToken"]
    response = client.post(
        "/api/auth/register",
        json={
            "username": name,
            "email": name + "@soilsync.example",
            "password": "SoilSync-QA!2026",
            "location": "Synthetic QA household",
            "accepted_terms": True,
        },
    )
    check(response.status_code == 201, "Register synthetic account with consent")
    users.append((response.json()["user"]["id"], name + "@soilsync.example"))
    return client


def parallel_post(client, path, payload=None):
    def send(_):
        return httpx.post(
            base + path,
            headers=dict(client.headers),
            cookies=client.cookies,
            json=payload,
            timeout=90,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        return list(executor.map(send, range(8)))


buffer = io.BytesIO()
Image.new("RGB", (240, 180), "green").save(buffer, "PNG")
upload = ("synthetic-qa.png", buffer.getvalue(), "image/png")

try:
    health = httpx.get(base + "/api/health").json()
    check(
        health["database"] == "connected" and health["photoStorage"] == "firebase-emulator",
        "Vite proxy reaches PostgreSQL API with emulator configuration",
    )
    owner, stranger = new_account(), new_account()
    check(
        owner.get("/api/state").json()["balance"] == 0, "Real registrations start with zero points"
    )
    daily = parallel_post(owner, "/api/daily-checkins")
    check(
        all(row.status_code == 200 for row in daily)
        and owner.get("/api/state").json()["balance"] == 10,
        "Eight concurrent daily requests award exactly ten points",
    )
    batch_ids = []
    for i in range(2):
        response = owner.post(
            "/api/batches",
            json={
                "name": f"Synthetic QA batch {i + 1}",
                "fertilizer_type_id": 1,
                "client_request_id": str(uuid.uuid4()),
            },
        )
        check(response.status_code == 201, "Create independent batch")
        batch_ids.append(response.json()["id"])
    batch = batch_ids[0]
    check(
        stranger.get(f"/api/batches/{batch}").status_code == 404,
        "Other account cannot access a batch",
    )
    check(
        owner.delete(f"/api/batches/{batch}").status_code == 409,
        "Unfinished batch cannot be deleted",
    )
    if proof_uploads:
        first_photo = None
        for week, proof_upload in enumerate(proof_uploads, start=1):
            response = owner.post(
                f"/api/batches/{batch}/quests/{week}/complete",
                files={"photo": proof_upload},
                data={"note": "Real compost photo supplied for opt-in live verification."},
            )
            check(
                response.status_code == 200,
                f"Week {week} uploads to Firebase emulator and commits PostgreSQL progress",
            )
            saved = response.json()["batch"]
            first_photo = first_photo or saved["checkins"][0]["photoUrl"]
            check(
                owner.get(saved["checkins"][-1]["photoUrl"]).status_code == 200,
                "Owner can retrieve persisted private photo",
            )
        check(
            saved["progress"] == 100 and saved["status"] == "Completed",
            "Three check-ins complete the tracker",
        )
        check(
            stranger.get(first_photo).status_code == 404,
            "Another account cannot retrieve the private photo",
        )
        with session_factory()() as db:
            key = db.scalar(
                select(WeeklyCheckinQuest.storage_key)
                .join(Batch)
                .where(Batch.id == int(batch), WeeklyCheckinQuest.week_number == 1)
            )
        public = httpx.get(
            f"http://127.0.0.1:9199/v0/b/{settings.firebase_storage_bucket}/o/{quote(key.removeprefix('firebase/'), safe='')}?alt=media"
        )
        check(
            public.status_code in (401, 403),
            "Firebase rules deny unauthenticated direct photo access",
        )
        repeats = owner.post(f"/api/batches/{batch}/quests/1/complete", files={"photo": upload})
        check(
            repeats.status_code == 200 and repeats.json()["pointsAwarded"] == 0,
            "Completed quest retry awards no extra points",
        )
        claims = parallel_post(
            owner, "/api/rewards/eco-bag/claims", {"request_id": str(uuid.uuid4())}
        )
        check(
            all(row.status_code == 200 for row in claims),
            "Concurrent reward retries return one claim",
        )
        snapshot = owner.get("/api/state").json()
        check(
            snapshot["balance"] == 260 and len(snapshot["redemptions"]) == 1,
            "Database wallet has exactly 10 + 300 - 50 points",
        )
    else:
        print(
            "SKIP live compost approvals/photo persistence: supply --compost-photos with three distinct real photos."
        )
        check(
            owner.post(
                "/api/rewards/eco-bag/claims", json={"request_id": str(uuid.uuid4())}
            ).status_code
            == 409,
            "Unapproved check-ins cannot fund a reward claim",
        )
    expected_balance = 260 if proof_uploads else 10
    if health["gemini"] == "missing_key":
        scan = owner.post("/api/scans", files={"photo": upload})
        check(
            scan.status_code == 503
            and owner.get("/api/state").json()["balance"] == expected_balance,
            "Missing Gemini key produces honest error and no scan points",
        )
    if not proof_uploads and health["gemini"] == "missing_key":
        proof = owner.post(f"/api/batches/{batch}/quests/1/complete", files={"photo": upload})
        snapshot = owner.get("/api/state").json()
        check(
            proof.status_code == 503
            and snapshot["balance"] == 10
            and snapshot["batches"][0]["progress"] == 0
            and snapshot["batches"][0]["checkins"] == [],
            "Missing Gemini cannot approve a weekly photo or award points",
        )
    if proof_uploads:
        check(
            owner.delete(f"/api/batches/{batch}").status_code == 200,
            "Completed batch deletion removes its private photos",
        )
        check(
            owner.get(first_photo).status_code == 404
            and len(owner.get("/api/state").json()["batches"]) == 1,
            "Deletion preserves the other batch and removes old photo access",
        )
    check(
        owner.post("/api/auth/logout").status_code == 200
        and owner.get("/api/state").status_code == 401,
        "Logout revokes the server session",
    )
finally:
    for client in clients:
        client.close()
    with session_factory()() as db, db.begin():
        for user_id, email in users:
            if db.scalar(select(User.id).where(User.id == user_id, User.email == email)):
                keys = list(
                    db.scalars(
                        select(WeeklyCheckinQuest.storage_key)
                        .join(Batch)
                        .where(Batch.user_id == user_id)
                    )
                )
                for key in keys:
                    if key:
                        media.delete_photo(key)
                db.execute(delete(User).where(User.id == user_id, User.email == email))
    print("Synthetic QA accounts removed; seeded households preserved.")
