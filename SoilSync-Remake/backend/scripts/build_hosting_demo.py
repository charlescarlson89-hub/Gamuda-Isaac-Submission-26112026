"""Export committed frontend screens into a static sample-data trainer build.

All substitutions affect an ignored release copy. Never use real accounts,
PostgreSQL data, Gemini credentials or the normal app's API transport here.
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
BACKEND = PROJECT / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import atlas_methods  # noqa: E402
from app.models import Base, WasteFertilizerMatch, WasteType  # noqa: E402
from app.seed_data import populate_catalogue  # noqa: E402
from app.serializers import catalogue  # noqa: E402

source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT, text=True).strip()
release = BACKEND / ".runtime" / f"firebase-release-{source_commit[:7]}-{uuid.uuid4().hex[:8]}"
release.mkdir(parents=True)
archive = subprocess.check_output(["git", "archive", source_commit, "frontend"], cwd=PROJECT)
with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
    bundle.extractall(release, filter="data")
frontend = release / "frontend"


def adapt(relative, substitutions):
    path = frontend / relative
    source = path.read_text(encoding="utf-8")
    for old, new in substitutions:
        if old not in source:
            raise RuntimeError(f"Review trainer-demo adaptation: {relative}: {old[:60]}")
        source = source.replace(old, new)
    path.write_text(source, encoding="utf-8")


adapt("src/main.jsx", [("<App />", '<div className="hosting-demo-notice" role="note">Trainer frontend demo · Sample data · AI off · No online accounts</div><App />')])
with (frontend / "src/styles.css").open("a", encoding="utf-8") as css:
    css.write(
        "\n.hosting-demo-notice { padding: 10px 16px; color: #23432a; background: #e8edda; text-align: center; font-size: 13px; line-height: 1.5; border-bottom: 1px solid #d3ddbd; }\n"
        ".confidence-score { display: none; }\n"
        ".capture-stage .camera-demo-sample { min-height: 44px; padding: 8px 16px; border: 1px solid #d0dbc0; border-radius: 8px; background: #293526; color: #f4f7ee; font-size: 14px; }\n"
    )
adapt("src/pages/Welcome.jsx", [
    ('const [identifier, setIdentifier] = useState("")', 'const [identifier, setIdentifier] = useState("trainer")'),
    ('const [email, setEmail] = useState("")', 'const [email, setEmail] = useState("trainer@soilsync.example")'),
    ('const [password, setPassword] = useState("")', 'const [password, setPassword] = useState("frontend-demo")'),
    ('setPassword("");', 'setPassword("frontend-demo");'),
    ('autoComplete={registering ? "new-password" : "current-password"}', 'autoComplete="off"'),
    ('autoComplete="username"', 'autoComplete="off"'),
    ('autoComplete="email"', 'autoComplete="off"'),
    ('<h1>SoilSync</h1>', '<h1>SoilSync</h1>\n        <span className="powered-by">Frontend demo · sample access</span>'),
    ('<h2>{registering ? "Create account" : "Log In"}</h2>', '<h2>{registering ? "Registration preview" : "Demo Log In"}</h2>'),
    ('Your profile and progress belong to your account. Passwords are\n          securely hashed.', 'Sample access only. Do not enter a real password. No online account is created.'),
    ('I have read and accept the terms and data-use notice.', 'I have read this sample notice for the frontend preview.'),
    ('SoilSync test project · 20 October 2026', 'Trainer demo · Sample notice · No online accounts'),
    ('Registration stores your username, email, location,\n            a password hash and your acceptance of this notice.', 'This form previews registration only. No online account, email record or password hash is created.'),
    ('Your account records include check-ins, points, scans, batches and\n            reward claims. Scan and weekly proof photos are sent to Google\n            Gemini to identify waste or check for visible compost. Approved\n            weekly proof photos are stored privately.', 'This demo uses sample points, recipes, batches and reward claims. AI is off. Photos preview locally and are not uploaded or saved.'),
    ('Contact the TEDA BYTE project administrator to recover your account.\n            Email password recovery is not connected yet.', 'No real account or password exists in this trainer demo. Use the supplied sample fields to explore.'),
])

# A sample classification is never presented as analysis of a captured photo.
adapt("src/pages/Scan.jsx", [
    ('import CameraStage from "../components/CameraStage";', 'import CameraStage from "../components/CameraStage";\nimport demoPhoto from "../assets/food-scraps.jpg";'),
    ('const { state, scanPhoto, busy } = useSoilSync();', 'const { state, busy } = useSoilSync();'),
    ('const [result, setResult] = useState(null);', 'const [result, setResult] = useState(state.scan);'),
    ('    setResult(null);\n    scanPhoto(camera.file)\n      .then((next) => {\n        if (next) setResult(next);\n      })\n      .catch((err) => setError(err.message));\n  }, [camera.file, scanPhoto]);', '    setResult(state.scan);\n  }, [camera.file, state.scan]);'),
    ('const next = await scanPhoto(camera.file);', 'const next = await Promise.resolve(state.scan);'),
    ('setResult(null);', 'setResult(state.scan);'),
    ('<CameraStage camera={camera} onClose={() => navigate("/home")} />', '<CameraStage camera={camera} onClose={() => navigate("/home")} onDemo={() => camera.setPhoto(demoPhoto)} />'),
    ('"AI Waste"', '"Sample Waste"'),
    ('result.pointsEarned\n                ? `+${result.pointsEarned} PTS Earned`\n                : "No points earned"', '"SAMPLE · AI OFF"'),
    ('Scanned materials matched to the SoilSync waste catalogue.', 'Illustrative catalogue example, not based on your photo.'),
    ('Identification confidence, not nutrient composition.', 'Sample data · No AI analysis or photo points.'),
    ('"Materials identified"', '"Illustrative sample · AI off"'),
    ('Try analysis again', 'Show sample again'),
    ('Identify waste\n', 'View sample\n'),
])
adapt("src/components/CameraStage.jsx", [
    ('  onCapture,', '  onCapture,\n  onDemo,'),
    ('"Capture photo and analyse with Google AI"', '"Capture photo for local demo preview"'),
    ('<small>{analysePhoto ? "Photos are analysed by Google AI." : "Your photo is saved privately."}</small>', '<small>Local previews only · AI off · No uploads</small>\n        {onDemo && <button type="button" className="camera-demo-sample" onClick={onDemo}>Use sample photo · demo only</button>}'),
])
adapt("src/pages/CheckinCamera.jsx", [
    ('import CameraStage from "../components/CameraStage";', 'import CameraStage from "../components/CameraStage";\nimport demoPhoto from "../assets/food-scraps.jpg";'),
    ('          camera={camera}', '          camera={camera}\n          onDemo={() => camera.setPhoto(demoPhoto)}'),
    ('Show the compost contents clearly. Approval earns 100 EcoPoints.', 'Sample weekly stage · no AI approval. Save for 100 sample points.'),
    ('Show the cloudy starter and its container clearly, or show the composting scraps. Approval earns 100 EcoPoints.', 'Sample weekly stage · no AI approval. Save for 100 sample points.'),
    ('Photograph the layered starter through the side of the jar, or show the cloudy liquid in its tub. Approval earns 100 EcoPoints.', 'Sample weekly stage · no AI approval. Save for 100 sample points.'),
    ('Show a collection of food scraps, such as fruit peels, rinds, or vegetable trimmings. A photo of the starter alone does not count. Approval earns 100 EcoPoints.', 'Sample weekly stage · no AI approval. Save for 100 sample points.'),
    ('"Checking compost…" : "Verify weekly check-in"', '"Saving demo…" : "Save demo weekly stage"'),
    ('alt="Your weekly compost proof"', 'alt="Weekly compost check-in preview"'),
    ('Verification sends this photo to Google AI. Approved proof is\n              saved privately. A visual check does not certify compost maturity.', 'Demo only: photos stay in memory and are not uploaded or retained. Sample stages do not verify compost or its maturity.'),
    ('+100 EcoPoints!', '+100 sample points!'),
])
adapt("src/state.jsx", [
    ('if (!batch || !action.photo)', 'if (!batch)'),
    ('form.append("photo", action.photo, "weekly-checkin.jpg");', 'if (action.photo) form.append("photo", action.photo, "weekly-checkin.jpg");'),
])
adapt("src/pages/Garden.jsx", [
    ('Check-in photos, dates and notes are saved to your account. Completing a\n        quest does not prove compost maturity.', 'Demo dates and notes stay in this browser. No photos are stored or AI verification performed.'),
    ('This photo is private to your account. It records an observation,\n            not verified compost maturity.', 'This is a demo observation with no stored photo or AI verification.'),
])
adapt("src/pages/Settings.jsx", [
    ('Preferences are saved to your account. Device notification delivery is', 'Demo preferences stay in this browser. Device notification delivery is'),
    ('Your username, email, location, password hash, activities and\n                reward claims are stored with your account. Logging out ends\n                this session without deleting your progress.', 'This frontend demo stores sample progress and profile edits in this browser. No online account or password is saved.'),
    ('Scan and weekly check-in photos are sent to Google Gemini for\n                waste identification or a visible-compost check. Approved\n                check-in photos are saved privately. Only the signed-in owner\n                can view account photos.', 'AI is off. Photo previews stay in screen memory and are not sent, saved or analysed. Demo stages do not verify compost.'),
])
adapt("src/pages/Rewards.jsx", [
    ('`Redeemed: ${confirm.name} (−${result.cost ?? confirm.cost} pts)`', '`Demo claim: ${confirm.name} (−${result.cost ?? confirm.cost} sample pts)`'),
    ('a project reward concept.', 'a demo concept; no real voucher or item is issued.'),
])
adapt("src/pages/LandingPage.jsx", [
    ('SoilSync uses Gemini to identify photographed materials against our waste catalogue. If AI is unavailable, the scan shows a clear status instead of guessing. Leaffy can also help with project questions.', 'Live AI is off in this trainer demo. Browse sample classifications and recipes. Leaffy uses the bundled project guide, without Gemini requests.'),
    ('Your profile and activity are saved to your SoilSync account. Weekly check-in photos are private. Scan photos are sent to Google Gemini for identification. Leaffy conversations remain in this page and clear when you leave.', 'Demo progress stays in this browser. No online account is created. Photos preview locally and are not uploaded or saved. Leaffy uses the bundled project guide.'),
    ('Your claims and point balance are saved to your account.', 'Demo claims and sample points stay in this browser.'),
])
adapt("src/components/LeaffyMascot.jsx", [
    ('Live AI unavailable · showing the project guide', 'Trainer demo · project guide · AI off'),
    ('Your question is sent to Google Gemini. Chat stays in this screen until you leave or clear it.', 'Trainer demo · AI off. Questions use the project guide and stay in this screen until you leave or clear it.'),
    ('SoilSync guide · ask about your greener routine', 'Trainer demo · project guide · AI off'),
])

templates = BACKEND / "hosting_demo"
shutil.copyfile(frontend / "src/services/leaffyKnowledge.js", frontend / "src/services/leaffyKnowledge-app.js")
shutil.copyfile(templates / "leaffy-guide.js", frontend / "src/services/leaffyKnowledge.js")
shutil.copyfile(templates / "demo-runtime.js", frontend / "src/services/demo-runtime.js")
shutil.copyfile(templates / "demo.test.js", frontend / "tests/hosting-demo.test.js")
(frontend / "src/services/api.js").write_text(
    'import catalog, { sampleScan, sampleMatch } from "./demo-catalogue.js";\n'
    'import { createDemoApi } from "./demo-runtime.js";\n'
    'export { ApiError, privatePhoto } from "./demo-runtime.js";\n'
    'let storage;\ntry { storage = window.localStorage; } catch { /* Optional. */ }\n'
    'export const api = createDemoApi({ catalog, sampleScan, sampleMatch, storage });\n'
    'export function clearCsrf() {}\n', encoding="utf-8",
)
# Publish the same guide fields available in the app, using synthetic scan rows
# and recipe links from the in-memory catalogue. Do not read user records.
methods = atlas_methods.load_methods()
if set(methods) != set(atlas_methods.METHOD_IDS.values()):
    raise RuntimeError("The five public recipe guides are required for the trainer demo.")
engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
with Session(engine) as db:
    populate_catalogue(db)
    db.flush()
    sample_catalogue = catalogue(db, methods=methods)
    sample_items = [row for row in sample_catalogue["wasteTypes"] if row["id"] in (1, 21)]
    sample_food_id = 1  # Banana peels.
    links = db.scalars(
        select(WasteFertilizerMatch.fertilizer_type_id)
        .where(WasteFertilizerMatch.waste_type_id == sample_food_id)
        .order_by(WasteFertilizerMatch.fertilizer_type_id)
    ).all()
    recommendation = atlas_methods.recommend(
        methods, [db.get(WasteType, sample_food_id)], {recipe_id: {sample_food_id} for recipe_id in links}
    )
    if recommendation is None:
        raise RuntimeError("The sample scan requires a compost recommendation for banana peels.")
    sample_scan = {
        "id": "demo-example", "source": "seed", "pointsEarned": 0,
        "fertilizer_ids": [recommendation["recipeId"], *(mix["recipeId"] for mix in recommendation["alternatives"])],
        "items": [
            {**row, "waste_type_id": row["id"], "confidence": 0, "fertilizer_ids": links if row["is_supported"] else []}
            for row in sample_items
        ],
    }
engine.dispose()
(frontend / "src/services/demo-catalogue.js").write_text(
    "export default " + json.dumps(sample_catalogue, indent=2) + ";\n"
    "export const sampleScan = " + json.dumps(sample_scan) + ";\n"
    "export const sampleMatch = " + json.dumps({"recommendation": recommendation, "featuredMethods": []}) + ";\n",
    encoding="utf-8",
)
hosting = {"hosting": {
    "site": "soilsync-bdd70", "public": "frontend/dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{"source": "**", "destination": "/index.html"}],
    "headers": [
        {"source": "**", "headers": [
            {"key": "X-Content-Type-Options", "value": "nosniff"},
            {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
            {"key": "Cache-Control", "value": "no-cache"},
        ]},
        {"source": "/assets/**", "headers": [{"key": "Cache-Control", "value": "public,max-age=31536000,immutable"}]},
    ],
}}
(release / "firebase.json").write_text(json.dumps(hosting, indent=2) + "\n", encoding="utf-8")
android_build = (frontend / "android/app/build.gradle").read_text(encoding="utf-8")
version = re.search(r'^\s*versionName\s+"([^"]+)"', android_build, re.MULTILINE)
if version is None:
    raise RuntimeError("Could not read the SoilSync version from the committed Android build configuration.")
manifest = {"sourceCommit": source_commit, "appVersion": version.group(1), "mode": "static-trainer-demo", "liveBackend": False, "realAccounts": False, "liveAI": False, "photoUploads": False}
(release / "release.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(frontend / "public/release.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
environment = {key: value for key, value in os.environ.items() if not key.startswith("VITE_")}
for command in ["npm ci", "npm test", "npm run lint", "npm run build"]:
    args = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", command] if os.name == "nt" else command.split()
    subprocess.run(args, cwd=frontend, check=True, env=environment)
print("Built latest static trainer demo only; nothing deployed.")
print("Source commit:", source_commit)
print("Firebase config:", (release / "firebase.json").relative_to(PROJECT).as_posix())
