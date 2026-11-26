# SoilSync — TEDA BYTE

**Running the project?** See the [one-command startup guide](PLEASE_READ_START_GUIDE.md).

SoilSync is a React/Vite and Capacitor Android app with FastAPI, Google Gemini, Neon PostgreSQL and MongoDB Atlas. This source includes illustrated guides for Hot Composting, Cold Composting, Bokashi, Blender Slurry & Soil Factory and DIY Rice Water Inoculant.

See [ONLINE_SETUP.md](ONLINE_SETUP.md) for deployment and APK build details, and [VALIDATION.md](VALIDATION.md) for release checks.

- Online app: https://soilsync-api.vercel.app/
- API documentation: https://soilsync-api.vercel.app/docs
- Firebase trainer demo: https://soilsync-bdd70.web.app/ (separate sample-data frontend; AI disabled)

The Firebase Storage emulator remains an optional local development mode. `main` is updated only through a reviewed pull request.

```text
SoilSync-Remake/
├── frontend/                 React pages, styles, assets and camera controls
├── backend/
│   ├── app/                  API, models, validation, accounting, Gemini and photos
│   ├── alembic/              versioned migration
│   ├── sql/                  PostgreSQL DDL, mock data and dbdiagram DBML
│   ├── scripts/              setup, seed, exports and live-stack verification
│   ├── tests/                isolated API regression suite
│   └── .env.example          copy to .env locally; never commit secrets
├── scripts/                  development commands
├── firebase.json             local Storage emulator configuration
├── storage.rules             deny direct browser access to photos
└── SoilSync.code-workspace   open in VS Code
```

## Run locally

Use Node 22.12+, Python 3.12 and PostgreSQL. Java 21 is needed for Android builds and the optional Firebase Storage emulator. This computer already has its environment and database configured.

```powershell
git clone https://github.com/charlescarlson89-hub/SoilSync-Remake.git
cd SoilSync-Remake
npm run setup
```

Setup installs the pinned Node/Python dependencies, creates `backend/.venv` and copies `.env.example` only when `.env` does not exist. Install Java 21 from [Eclipse Adoptium](https://adoptium.net/temurin/releases/?version=21), or use `npm run setup:storage:windows` for a checksum-verified portable runtime in ignored `backend/.runtime/java`. This does not change the system PATH.

Configure your own database connection and Gemini key in `%LOCALAPPDATA%/SoilSyncRemake/.env` on Windows, as described below. Keep non-secret defaults in `backend/.env`. PostgreSQL on this computer uses **port 8888**; a teammate may use 5432. GitHub does not include credentials or copy the running database and photos to another computer. Keep database passwords and Gemini keys out of chat, Git and `VITE_*` variables.

In pgAdmin, connect Query Tool to `postgres` as administrator, enable Auto-commit and run `backend/sql/000_create_database.sql`. This creates only `soilsync_remake_test`, owned by the existing `soilsync_app` role. A teammate without that role should create a local login role/password first and adjust the owner/connection. Alternatively set `ADMIN_DATABASE_URL` locally and run `backend/.venv/Scripts/python.exe backend/scripts/create_database.py`.

```powershell
npm run db:migrate
npm run db:seed -- --mock
npm run dev
```

| Service | Address |
| --- | --- |
| Frontend | http://127.0.0.1:5173/ |
| API documentation | http://127.0.0.1:8001/docs |
| API health through Vite | http://127.0.0.1:5173/api/health |
| Firebase emulator UI | http://127.0.0.1:4000/storage |
| Storage emulator | http://127.0.0.1:9199 |

`npm run dev` starts Vite and FastAPI, plus Storage when the project defaults explicitly select the Firebase emulator. New setups default to PostgreSQL photo storage. It reports occupied ports without killing unrelated programs. Stop an existing SoilSync task with **Ctrl+C** before restarting. Separate commands: `dev:frontend`, `dev:backend`, `dev:storage`. Use `127.0.0.1` consistently for cookie sessions.

On Windows, run `npm.cmd run dev:setup` from the project root to install the locked Node and Python dependencies and start the local app in one step. FastAPI uses your saved settings to connect to Neon PostgreSQL and MongoDB Atlas. The command keeps your existing configuration and leaves the cloud database schemas untouched.

The full dev launcher waits for FastAPI health and catalogue checks before starting React. For this launcher, saved database settings take priority over values inherited from the terminal. Restart the launcher after editing the saved settings.

In VS Code, open `SoilSync.code-workspace`, select **SoilSync: Start full app** in Run and Debug, then press **F5**. **SoilSync: Start backend (FastAPI)** launches only the API.

If Uvicorn says `Could not import module "main"`, stop that terminal command with **Ctrl+C**. This project's entry point is `app.main:app` inside `backend/app/main.py`, and the frontend expects port **8001**. Run `npm run dev` from the project root, or use this exact standalone command from the `backend` folder:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Using the project's Python environment avoids launching Uvicorn from another project's environment. `uvicorn main:app --reload` looks for the wrong module and also defaults to port 8000.

The first Firebase run downloads its official runtime. Photos export every minute and on normal Ctrl+C to `backend/.runtime/firebase-data`, then import on restart. Keep that ignored folder and PostgreSQL backups together. Forced system/process shutdown can lose photos since the last export. Seeded photos are clearly labelled local fixtures; `db:seed -- --mock` recreates missing fixtures after SQL import.

## Add the Gemini key

Like Kazu AI Lab, SoilSync supports a private secrets file outside the repository and OneDrive. On this Windows account, open this file in VS Code:

```text
C:\Users\Charl\AppData\Local\SoilSyncRemake\.env
```

Store actual `GEMINI_API_KEY`, `DATABASE_URL` and optional `ADMIN_DATABASE_URL` there. Private values override `backend/.env`; process environment variables override both for deployment. Other computers use their own `%LOCALAPPDATA%/SoilSyncRemake/.env` (fallback `~/.config/SoilSyncRemake/.env`). Existing project-only settings remain supported. This is a plaintext local file, not an encrypted vault or on-screen mask. Keep it closed when screen-sharing.

Enter the key in the **private file** and keep the model in **backend/.env**:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Save and restart the backend after editing the private file; it is outside the watched project directory. Choose another vision-capable model if your Gemini project lacks access to the configured model. Scan Waste → capture/upload a real waste photo → **Identify waste**. The backend validates JPEG/PNG/WebP, limits size, strips EXIF, resizes and sends the image server-side to Gemini. Only recognized catalogue IDs above the confidence threshold are accepted; support, disposal and recipe guidance come from PostgreSQL. Unknown objects receive no points.

Missing keys/provider errors display honest errors and award no points. Leaffy appears beside the Home daily tip board and on the landing page, uses server-side Gemini and labels her bundled project-guide fallback when live AI is unavailable. Chat earns no points and stays in screen memory until leaving or clearing it. The owner confirmed online phone login, a waste scan and a Leaffy reply; this does not establish general AI accuracy. Provider regression tests use controlled responses. Scan images are not stored; the identified result and image hash are saved.

### Waste matching and weekly photo approval

Scans resolve only current PostgreSQL `waste_types.id` values (the seed's Banana peels is ID 1; IDs are never hardcoded in the classifier). Each result item includes its `fertilizer_ids` from `waste_fertilizer_matches`. The scan also includes matched `fertilizers`, with ordered database recipe steps, maintenance guidance and suitable/avoid plant links. Unknown, low-confidence or unsupported items cannot acquire recipe links from AI-generated text.

### Scan-based compost mixes

Apply PostgreSQL migrations through `0011` when preparing a separate database. Revision `0007` adds date-based claims and reserves method IDs 7 and 8. Revision `0008` adds waste types 54–67 and links catalogue entries to their Atlas method IDs. Revisions `0009` and `0010` add distinct animal scrap and fish pin bone types. Revision `0011` adds the household rewards. Existing batches keep their recorded check-ins.

The Atlas database uses `recipe_templates` with matching numeric `_id` and `recipe_id` values. Hot is 4, Cold is 5, Bokashi is 6, Blender Slurry is 7 and DIY Rice-Water is 8. Edit the numeric records. During migration the app can read the older ObjectId records when a numeric record is absent.

Set `MONGODB_RECIPE_URI` in the backend's private configuration using an Atlas account that can read the recipe collection. Set `MONGODB_RECIPE_DATABASE` if it differs from `soilsync`.

Gemini identifies materials against the PostgreSQL waste catalogue. SoilSync matches the identified food scraps to Atlas suitability lists and recipe ingredients. When Blender Slurry or DIY Rice-Water match, the scan options and fertilizer picker show the matching preferred methods. Otherwise, they show all compost guides. Ingredient percentages come from the matched mix and suitable plants come from the selected Atlas method.

For small plain meat and fish trimmings, the matcher uses mixes adapted from the SoilSync Composting Guide for sealed Bokashi or DIY Rice-Water. Clearly small, thin fish pin bones can match either method. Other small bones can match Bokashi if the kit accepts them. The classification keeps spines, thick bones, whole pieces and unspecified animal waste out of the supported mixes. Serving dishes and cutlery are ignored.

New batches started from an Atlas method open their first claim after seven days. Additional claims open weekly, with a final claim on the method's last planned day if it falls partway through a week.

New weekly check-ins must pass Gemini's visible-compost check before the photo is stored, the quest advances or 100 points are awarded. Only a `compost` verdict at confidence >= 0.80 is accepted. This is an uncalibrated model estimate, not measured accuracy. Early-stage compost mixtures and decomposing leaf material are allowed; isolated fresh peels, closed bins without visible contents, unrelated objects and unclear images are not proof. Missing keys, provider errors and rejected photos leave points and progress unchanged. Exact normalized-image reuse across a user's check-ins is blocked; this is not perceptual duplicate detection or proof of when/where a photo was taken. Approval details (provider/model, verdict, confidence and time) are stored in `weekly_checkin_quests.verification`. Existing/mock records remain null, not retroactively approved.

Run `npm run db:migrate` for your own local database after pulling this update. Revision `0002` adds verification fields and `0003` adds optional private PostgreSQL photo bytes. Existing data is preserved; do not replace or reseed the shared Neon database. The camera explains that weekly photos go to Google Gemini. The Firebase trainer demo uses sample stages and does not perform real verification.

`npm run test:backend` verifies approvals/rejections with controlled AI responses. `npm run test:live` checks the actual local stack and missing-key safeguards; it explicitly skips real approval/photo-storage assertions without real photos. To opt into live Gemini verification, supply **three distinct real compost photos** (these will be sent to Google Gemini):

```powershell
npm run test:live -- --compost-photos "C:\photos\week1.jpg" "C:\photos\week2.jpg" "C:\photos\week3.jpg"
```

No live AI accuracy or photo approval is claimed until this is tested with the owner's key and representative compost/non-compost photos.

## Data and behaviour

The 15 supplied tables are implemented, plus `auth_sessions` for revocable sessions and `points_ledger` for balance auditing. Database constraints cover ownership, uniqueness and valid values. Registration stores the versioned consent timestamp. `users.password` contains Argon2 hashes, never plaintext. Sessions use HttpOnly cookies, allowed origins and CSRF protection; the browser cannot set its wallet balance.

The synthetic seed contains 20 households/settings, 30 waste types, 20 plants, 23 reward concepts (including three coffee concepts), 40 batches, 40 daily check-ins, 40 scan logs, 120 weekly quests, 20 claims and ledger records. There are intentionally **three recipes and three maintenance guides**, matching the schema, plus 21 recipe steps and 60 suitability links. Seed sessions are expired. Photos/scans/codes are labelled mock data.

Test login: **demo01** or **demo01@soilsync.example**, password **SoilSyncDemo!2026**. Accounts demo02–demo20 also exist. These are disposable mock credentials; do not seed them into a public database. Real registrations start at zero.

The server awards **10** points per Kuala Lumpur date, **50** for a newly identified photo and **100** for each verified weekly batch photo. Identical photo, quest and reward retries do not duplicate points or charges. PostgreSQL row locks protect concurrent requests. Batch progress tracks completed check-ins. Completed batches can be deleted with their photos, preserving other batches and ledger history.

Eco-bag and other practical eco rewards have database claim codes and one claim per user/reward. **Partner fulfilment, voucher validation and shipping are not connected.** Notification preferences persist; scheduled notifications, password reset and email verification are not yet configured. The registration notice is a test-project draft requiring organisation/contact details and review before public launch.

## pgAdmin and dbdiagram

Import `backend/sql/soilsync.dbml` into [dbdiagram](https://dbdiagram.io/d). It represents the same models, relationships and unique indexes as the SQL schema.

For SQL-only setup, run `000_create_database.sql` on `postgres`, then connect to `soilsync_remake_test` and run `001_schema.sql` followed by `002_mock_data.sql`. Choose **either SQL DDL import or Alembic migration** for a fresh database, not both. After SQL import, run this from the project root, followed by `npm run db:seed -- --mock` to recreate synthetic photos:

```powershell
backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini stamp 0001
npm run db:migrate
```

The checked-in SQL seed contains only synthetic data and password hashes. `export_schema.py` generates SQL/DBML; future schema changes need a new migration. The initial SQL becomes the immutable migration baseline after this branch is committed. Automatic destructive downgrade is disabled.

## Checks

```powershell
npm test
npm run lint
npm run build
npm run test:backend
npm run lint:backend
npm run test:live
```

`test:live` needs the local stack and test database. It creates/removes two synthetic QA accounts and checks real PostgreSQL concurrency, private Firebase photos, batches, rewards and logout. It does not send synthetic images to a configured Gemini provider. See `VALIDATION.md` for results and limits.

## Hosting and teamwork

### Get this update on a teammate's computer

In GitHub Desktop, select **SoilSync-Remake**, click **Fetch origin**, switch **Current branch** to **codex/soilsync-final-mobile**, then click **Pull origin** if offered. Keep any local work committed or stashed before switching or pulling. `main` does not receive this update automatically.

For an existing local setup, stop SoilSync with **Ctrl+C**, then run from the project root:

```powershell
npm run setup
npm run db:migrate
npm run dev
```

Migrations through `0003` retain existing records and support private PostgreSQL photos. Existing databases do not need reseeding. For a first-time setup, follow **Run locally** above using a separate local database and mock data. Each developer supplies private credentials; the included mock login works only after that developer seeds a local database. The shared Neon database is already migrated: do not run mock seeding or destructive setup against it. pgAdmin is a database client; it does not synchronize separate local databases.

### Public demo

The public site at https://soilsync-bdd70.web.app/ serves a clearly labelled **trainer frontend demo**. `npm run build:hosting-demo` exports the latest committed frontend into an isolated release folder and substitutes a browser-only sample-data adapter. The local API-connected frontend sources stay intact. The demo includes the cinematic landing/Leaffy, sample login/registration screens, multiple batches and demo weekly stages, the current eco rewards catalogue, sample waste classification, recipes/plants, profile and logout. Use the supplied sample login fields; no real password is needed, verified or retained. Notes, profile edits, sample points and demo claims stay in that browser. Photos are temporary local previews and are never uploaded or stored. AI is off; Leaffy uses the built-in project guide.

The Firebase demo makes no backend or Gemini requests. Its catalogue is generated from an in-memory synthetic seed, never exported from the real user database. See `HOSTING_RELEASE.md` for that demo's version and update instructions. The full online app is the separate Vercel/Neon service described in `ONLINE_SETUP.md`; its approved photos use PostgreSQL. The checked-in Cloud Run/Firebase rewrite example is an optional alternative, not the current deployment.

Keep production credentials server-side, secure cookies and allowed origins configured, and review backups and hosting/provider quotas. A Firebase Storage bucket is not required by the current PostgreSQL photo mode. Never deploy an emulator owner token or emulator host. No browser receives administrative credentials or a public photo URL.

In GitHub Desktop select **codex/soilsync-final-mobile**, fetch/pull, commit and push. Review a pull request before merging. Secrets, dependencies, generated APKs, uploads and emulator data are ignored. Nothing merges to `main` automatically.
