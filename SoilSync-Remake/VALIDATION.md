# Validation — backend test branch

Branch: `codex/soilsync-backend-test`. The first sections record the 20 October 2026 baseline; dated updates below supersede those results and limits. Local and remote `main` must remain at `6d5ad17f143d4133c255de65b7f6aeb056f2e56a`.

| Check | Result |
| --- | --- |
| Frontend Node tests | 9 passed |
| ESLint, React hooks and JSX accessibility rules | Passed, zero warnings |
| Vite production build | Passed; upstream React Router `use client` directives are ignored by Vite |
| FastAPI regression suite | 15 passed; isolated SQLite, controlled Gemini responses |
| Ruff | Passed |
| Live PostgreSQL/Firebase smoke test through Vite | 25 assertions passed |
| Browser account/batch/reward flows | 12 checks passed in Edge |
| Landing chat, simulated camera and cinematic video | 3 checks passed |
| Browser JavaScript exceptions | None |
| Axe WCAG A/AA checks | Zero violations on landing, consent dialog, registration, home, batch, rewards, scan, fertilizer and profile |
| Responsive overflow | None at 320, 390, 768 and 1440px in checked home/rewards screens; mobile screenshots reviewed |
| PostgreSQL migration | `0001 (head)` |
| DBML | 17 application tables, validated with current `dbmlv2` compiler and rendered in dbdiagram |
| Emulator photo persistence | Same photo bytes retrieved after full app/API/emulator restart |
| Seed wallet reconciliation | All 20 user balances equal their points-ledger totals |

## Live checks

Real HTTP requests at `http://127.0.0.1:5173` reached FastAPI/Uvicorn on 8001, PostgreSQL 18 on 8888, and Firebase Storage emulator on 9199. No cloud Storage bucket or paid service was created.

The live smoke test verified registration/consent, zero initial balance, eight concurrent daily requests awarding ten points total, independent batches, owner isolation, unfinished-batch deletion rejection, three persisted weekly photos and +100 points per quest, zero duplicate quest awards, direct Firebase access denied without administrative credentials, eight reward retries producing one claim/debit, exact final balance, completed-batch photo deletion, preservation of another batch and logout/session revocation. Disposable API/browser QA accounts and their photos were removed after testing. Original seeded households remain.

Browser checks exercised actual forms and API responses: rejected incorrect password, required registration consent, reload persistence, creation by database recipe/ID, all three photo upload stages, private stored-image retrieval, eco-bag claim and disabled repeat claim after reload, honest missing-Gemini-key error without points, database fertilizer catalogue, completed-batch deletion, logout and later login restoring the wallet. Separate tests exercised a simulated webcam frame capture/File and track cleanup, Leaffy's labelled project-guide fallback, and the real muted looping cinematic video, pause control and reduced-motion poster.

## Dataset

Application tables contain: 20 users, 20 settings, 40 daily check-ins, 30 waste types, 40 scan logs, 3 fertilizer types, 39 waste/recipe matches, 20 plants, 60 suitability links, 21 recipe steps, 3 maintenance guides, 40 batches, 120 weekly quests, 20 rewards, 20 claims and 150 ledger entries. Twenty synthetic expired sessions are seeded; normal test logins can add sessions. Three recipes and three maintenance guides intentionally follow the supplied three-type specification rather than duplicating them to twenty.

SQL schema/seed exports, Alembic migration and DBML are checked into the branch. Seed SQL contains synthetic account hashes and labelled mock records only. Local credentials, Python environment, Node dependencies, uploads, emulator snapshots/temporary exports and logs are excluded.

## Remaining limits

- **Live Gemini recognition/chat:** awaiting the owner's API key in `backend/.env`, an available model and a real-waste-photo check. Automated tests validate provider handling, DB-ID matching, rejection/unknown results, duplicate scans, error handling and points; they do not establish real-world model accuracy. Physical phone-camera hardware was not tested; browser capture used a simulated device.
- **Firebase cloud:** the labelled static frontend demo was subsequently deployed on 20 October 2026; see `HOSTING_RELEASE.md`. FastAPI, PostgreSQL and photo storage remain local. No billing changes or paid services were enabled. A future cloud backend and hosted database must exist before enabling the Hosting API rewrite. Emulator administrative access is restricted to loopback outside production.
- **dbdiagram:** source file is saved in Git; a new rendered draft is open in the browser. The editor is not signed in, so the draft is not saved to a dbdiagram account or share URL.
- **Product integrations:** no partner fulfilment, voucher validation, push/email delivery, password-reset or email-verification service. Preferences and claims are persisted database records. Prototype batch quests are ordered but do not enforce seven-day spacing or certify compost maturity.
- **Public launch:** requires completed organisation/privacy contact details, review of the draft terms, production credentials/cookies/origins, operational monitoring/backups and production security review. The in-memory rate limiter is appropriate for this single-process test setup, not a shared distributed limiter.
- **Dependency notices:** the pinned Firebase CLI development dependency reports 7 transitive npm audit findings (3 high, 4 moderate) in its upstream dependency tree. Compatible patched versions are not currently available through npm for all of them; a forced major downgrade/override was not applied. Frontend dependencies report zero audit findings. FastAPI's test client emits an upstream httpx deprecation warning; all tests pass.

Supporting screenshots and detailed browser reports are in the workspace parent `tmp/soilsync-remake/`, outside the source repository. Re-run the commands documented in README after changing provider keys or application code.


## 21 October 2026: catalogue matching and weekly compost approval

Implemented on `codex/soilsync-backend-test`; no Firebase deployment. These results supersede the earlier unrestricted weekly-photo behaviour above.

- Migration `0002` applied only to `soilsync_remake_test`: 120 existing quest rows preserved. New nullable `image_sha256` and JSONB `verification` fields; unique batch/image constraint. Legacy/mock proofs are not labelled approved.
- 26 isolated API/provider tests passed: database IDs and recipe/step/plant chains, unrelated/uncertain/low-confidence rejection, provider/storage failure, malformed model output, exact normalized-image reuse prevention, approved progress and duplicate retries.
- 13 live local API assertions passed, including missing-key protection: no weekly completion or points without Gemini. Live real-photo approval assertions explicitly skipped without photos/key.
- 11 additional controlled-provider checks against actual PostgreSQL and Firebase Storage emulator passed: four concurrent approvals award exactly 100 total; approval audit persists; private photo round trip; rejection/reuse leave progress unchanged; approved weeks complete and owned-photo deletion works. The controlled provider was scoped to a separate QA process; no bypass exists in the running application. Disposable QA accounts/photos removed.
- Frontend: 9 tests, ESLint and Vite build passed. Browser login, updated weekly-camera instructions, disabled submit without a photo, and logout verified at http://127.0.0.1:5173/.
- Backend Ruff passed. Test runner reports an upstream Starlette/httpx deprecation warning; tests pass.

Actual Gemini vision accuracy remains unverified: `GEMINI_API_KEY` was still absent. The 0.80 compost cutoff is an uncalibrated model estimate, not a measured accuracy guarantee. Photo approval cannot certify maturity, nutrients, time/location or batch ownership. Identical normalized images are blocked; altered/cropped or previously unseen old photos are not reliably detected.

Implementation references: [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output), [image understanding](https://ai.google.dev/gemini-api/docs/image-understanding). Existing Python Google GenAI SDK retained.


## 22 October 2026: live Gemini image request compatibility

The live image request reproduced Google HTTP 400: `additional_properties` was rejected in `generation_config.response_schema`. Text generation and model metadata worked; key validity alone did not exercise the image request schema.

Both waste detection and compost verification now use `response_json_schema=Model.model_json_schema()` with the installed Google GenAI SDK, retaining Pydantic output validation. Two regression cases inspect the actual SDK HTTP payload through a mock transport and require the JSON Schema field rather than the incompatible legacy schema conversion.

- Backend: 31 tests passed; Ruff and diff whitespace checks passed.
- Actual Gemini: both image helpers accepted a tiny synthetic solid-colour JPEG. Waste result contained no identified materials; compost verdict was `not_compost`.
- Restarted local app: `/api/scans` returned HTTP 200 and zero points for the same synthetic image. Weekly proof returned HTTP 422; wallet and progress stayed zero. Temporary QA account/records removed. No user photo was uploaded by these checks.
- Representative real waste recognition and positive real-compost approval still need image testing; these checks do not establish general recognition accuracy.

No Firebase deployment or production configuration change was made.

### GitHub team handoff checks — 22 October 2026

- Fresh frontend checks: 9 tests passed, ESLint passed with zero warnings, Vite production build passed. The existing React Router directive notices remain informational.
- Fresh backend checks: 31 tests passed and Ruff passed. The existing Starlette/httpx deprecation warning remains; no test failed. The restricted-sandbox test process stalled; the rerun with normal local permissions completed successfully.
- Checked 264 publishable source/assets files against the actual local credentials and common Google/private-key patterns without printing secret values: no matches. Private `.env` files, dependencies, uploads and emulator snapshots remain excluded.
- README now includes GitHub Desktop branch/pull instructions, private configuration requirements and migration `0002` for existing teammates. GitHub shares source, migrations and synthetic seed data; it does not share the local database, photos or credentials.
- No new live-provider accuracy test or Firebase deployment was performed for this source update.

## 23 October 2026: latest frontend trainer demo on Firebase

Published Hosting version `bb1d6bf8a774c0b4` at 00:06:55 MYT. Frontend source `b0197b5`; the generated release replaces only the API transport and demo-specific copy in an isolated folder. Local API-connected screens, database and Gemini configuration were not changed. See `HOSTING_RELEASE.md` for release and rebuild instructions.

- 12 frontend/demo tests passed, ESLint zero warnings, Vite production build passed and script Ruff passed.
- New demo tests cover no-network operation, ignoring credentials and photo content, persisted sample state, sign-in/out, independent batches, ordered stages, single awards and single reward debits. No real account is created and no AI approval is simulated as genuine.
- Firebase preview browser checks passed: landing, sample login, dashboard, new batch, weekly demo progress, eco-bag claim/non-redeemable receipt, repeat claim disabled, scan sample/AI disabled, recipe and suitable plants, reload persistence, profile and logout. No browser warnings/errors observed.
- The public live landing and Leaffy's project-guide response were verified after promotion. Live HTML, release metadata and entry JS/CSS match the final build and preview byte-for-byte.
- 133 final output files checked against local secrets/key patterns: no matches. No real database export was used; the catalogue came from a temporary in-memory seed.
- Billing read-only check returned `billingEnabled: false`. Only static Hosting deployed. No backend, cloud database, bucket, Auth settings or billing changes.
- Production dependency audit reported zero findings. A new full audit reports one high finding in the existing Vite 7.3.6 development tooling (patch 7.3.7 available); it is not included in static output. No local dependency change made for this demo release.
- Firebase CLI's preview Auth-domain sync warning is irrelevant to the browser-only demo access; Firebase Auth is not used and was not changed.

Screenshot: workspace parent `tmp/soilsync-trainer-live-2026-10-23.png` (outside the repository). The trainer demo intentionally makes no backend/Gemini requests; it does not test online registration, real scanning or compost verification.

## Final mobile design and online service — 30 October 2026 handoff

Branch: `codex/soilsync-final-mobile`. The supplied final screenshots were used to
rebuild the app screens, camera/analysis transition, recipe and batch tracking,
settings, rewards and history. Existing landing content remains available.

- Frontend verification before the APK build: 10 tests passed, ESLint passed,
  production build passed. Backend: 43 tests passed and Ruff passed.
- Local browser checks covered login, real banana recognition and recipe matches,
  batch tracking, proof display, waste guidance, profile and rewards. These local
  results do not establish general image recognition accuracy.
- Vercel serves the frontend and FastAPI at `https://soilsync-api.vercel.app/`.
  Its existing Neon database was migrated additively to revision 0003; team data
  was preserved. Private approved proof photos can persist in PostgreSQL.
- Fresh read-only checks: frontend HTTP 200; OpenAPI HTTP 200 with 25 paths;
  health HTTP 200 with database connected, Gemini configured and photo storage
  `postgres`. No Firebase deployment or paid plan change was made for this build.
- Android build succeeded. APK 0.2.0 / version code 20261029 installed successfully
  on OPPO CPH2607 and launched. It bundles the frontend, targets the public HTTPS
  API, contains no development server URL and no Google API key pattern. No USB
  reverse forwarding was configured during installation.
- The owner chose read-only production checks and will test AI on the phone.
  No production test records or new Gemini requests were created during this
  handoff. The owner subsequently confirmed that login and an AI scan work with
  USB disconnected. This owner-reported check verifies the tested phone flow;
  other production write workflows and general recognition accuracy are untested
  by this handoff.

APK SHA-256: `baf8ab092bca49b95c05e21d3b4668093c976fd3e261921fba101922d852b4be`.
Build output and browser screenshots are in the workspace parent's
`output/soilsync-final-mobile/` folder. This is a debug-signed device test APK,
not a Play Store release. Partner fulfilment and password recovery delivery
remain outside this build; cloud hosting and Gemini quotas still apply.

## 30 October 2026 — typography, switches and dark mode (0.2.1)

- App headings and labels now use the bundled DM Sans family to follow the
  supplied soft sans-serif reference. Most small text increased by 1px and
  regular text by 2px. Suitable Plants names explicitly use 12px instead of
  inheriting the older 16px bold rule; their buttons retain a 44px touch height.
- Fixed notification switches' conflicting inherited minimum width. Browser
  measurements verified a 48px track, 22px thumb and a 3px edge gap: off at the
  left edge and on at the right edge. Tested on the local demo account and
  restored its original preference afterwards.
- Added Profile/Settings → Appearance with Device, Light and Dark radio choices.
  The choice persists on the device, follows system changes in Device mode,
  synchronizes between browser tabs, and handles unavailable device storage.
  Dark colors cover app/login surfaces, forms, dialogs, navigation and content
  cards; camera images and landing branding retain their own presentation.
- Frontend: 13 tests passed, ESLint passed, Vite build and Android build passed.
  Browser checked theme persistence after reload, both themes, switches, plant
  details, rewards and history. No horizontal overflow at tested 320px/390px
  widths and no captured browser warnings/errors during these checks.
- Installed and launched version 0.2.1 (20261030) on OPPO CPH2607. APK retains
  the hosted HTTPS API and contains the new appearance setting, no development
  server URL and no Google API key pattern. No production data writes, Gemini
  calls or cloud deployment were made for this frontend-only update.

APK and screenshots: workspace parent `output/soilsync-0.2.1/`.

### 0.2.2 — expanded maintenance-card contrast

The expanded Care & maintenance rows retained an older cream background while
inheriting dark-mode light text. `frontend/src/appearance.css` now assigns the
rows, paragraph text and icons explicit theme tokens. Expanded browser checks
measured text contrast of 11.30:1 in dark mode and 12.77:1 in light mode for all
three rows. Screenshots saved in `output/soilsync-0.2.2/` in the workspace parent.
ESLint, Vite build, Android build and diff checks passed. Version 0.2.2 (build
20261031) installed and launched successfully on OPPO CPH2607. No server or
database changes were required.

### 0.2.3 — Leaffy beside the daily information board

- Preserved the daily information board on Home. Added 16 editorial tips with
  source links to the EPA and Cornell guides, deterministic daily rotation on
  Kuala Lumpur time and an Another tip control. Browsing tips makes no AI call.
- Reused the existing Leaffy sprite sheets, blink/wave/sleep routines, reduced
  motion support and pause control in a board placement. Night tapping visibly
  wakes her before opening an accessible modal chat sheet. The landing page
  placement remains available.
- Updated the bundled fallback guide and server-side Gemini instructions to
  describe the current online app. Chat cannot access account records or award
  points. The UI labels project-guide fallbacks and explains sending questions
  to Gemini; messages remain in screen memory until leaving or clearing chat.
- 17 frontend tests and ESLint passed. 47 isolated backend tests and Ruff passed,
  including chat CSRF, no point awards, provider configuration and empty replies.
  Provider responses were mocked: no live Gemini request was made by the agent.
- Local browser checked the board in light/dark modes, tip cycling, nighttime
  waking, chat opening/closing with focus restoration, composer enablement and
  pause/resume. A 390×420 viewport check confirmed the composer remained inside
  the dialog; compact mode hides suggestions to leave keyboard space. A final
  CSS adjustment fits the sheet to available width and prevents background
  scrolling. The extra final browser recheck was blocked by automatic approval
  review after a usage-limit failure; no alternate browser path was used.
- Vite and Android builds passed. Installed and launched 0.2.3 (20261032) on
  OPPO CPH2607. APK targets the hosted HTTPS API, includes the board, has no
  development server URL and no Google API key pattern.
- Promoted production deployment `dpl_E89Vmqk8k7oRNu6or6PR1ScogSVg` at
  `https://soilsync-api.vercel.app/`. Staged and public read-only checks passed:
  health reports database connected/Gemini configured/PostgreSQL photo storage;
  OpenAPI includes the existing chat route. No production test records,
  migrations, billing settings or Firebase deployments were created for this
  change. The owner subsequently confirmed that Leaffy replies on the phone.
  This owner-reported check confirms the chat interaction; the reply's provider
  label and USB/network conditions were not independently observed by the agent.

Artifact folder: workspace parent `output/soilsync-0.2.3/`.
APK SHA-256: `38ac22e94dfc0a9f7fe2f635759972b2478281267369f2d082ba09acfe0f0ecc`.

Main implementation files: `frontend/src/components/DailyTipBoard.jsx`,
`frontend/src/components/LeaffyBoard.css`, `frontend/src/components/LeaffyMascot.jsx`,
`frontend/src/data/compostTips.js`, `frontend/src/data/leaffy-guide.json`,
`frontend/src/services/leaffyKnowledge.js`, `frontend/src/pages/Home.jsx` and
`backend/app/media.py`. Supporting tests are in the frontend tests folder and
`backend/tests/test_api.py`.

### GitHub team handoff — 30 October 2026

- Latest source and teammate setup instructions identify `codex/soilsync-final-mobile`
  and SoilSync 0.2.3. The online service, optional Firebase demo/emulator and
  local-only mock data are distinguished in the README.
- Fresh frontend run: 17 tests passed and ESLint passed. Fresh backend run:
  47 isolated tests passed and Ruff passed. No real Gemini request or production
  data write was used by these checks. The previously recorded web/Android build
  and installed APK remain the application build for this handoff.
- Before staging, 348 source files and 86 unpublished historical blobs were
  checked against configured private credentials and key/token/credential-URL
  patterns. No matches were found; no credential values were printed. Private
  configuration, runtime data, generated APKs and signing keys are excluded.
- The remote team's startup-guide rename/update is preserved when incorporating
  the current `origin/main` into the mobile branch. This handoff does not merge
  the mobile implementation into `main`.

### Firebase trainer demo refresh — 30 October 2026

- Refreshed only the isolated demo builder/templates for the 0.2.3 frontend.
  Full app source/API, database and installed APK remain unchanged.
- Generated build from frontend commit `5fd988e71cc5ee1d9fc820844aa4379de0c4ba91`.
  20 frontend/demo tests, ESLint, Vite build and builder Ruff passed.
  Production dependency audit has zero findings; 133 built files passed a
  credential-pattern scan.
- Preview browser verified demo login, Home daily board/Leaffy guide answer,
  dark theme, notification switch travel, sample scan and weekly camera flows,
  ordered sample stage/point award and the latest reward catalogue.
- Preview version `26093f9a8d565518` was cloned to live Hosting. Live HTML,
  release metadata and entry JS/CSS matched the tested build byte-for-byte;
  live login and Home were visibly verified. See `HOSTING_RELEASE.md`.
- Demo has no live backend, real accounts, AI requests or photo uploads.
  Leaffy uses the bundled project guide. Billing remains disabled, verified
  read-only; no Auth, Storage, database, billing or Vercel settings changed.

### 0.2.4 — approved composting methods and illustrated dropdowns (review)

Implemented Hot, Cold and Bokashi Composting with three illustrated native
step dropdowns per method. Current recipe IDs are 4–6; 1–3 remain historical.
Scan recommendations and new batches accept only the approved methods; saved
batch identities and stored scan detections are preserved. Alembic 0004 is an
additive data migration, with a frozen SQL snapshot and pgAdmin equivalent.

18 frontend tests, 54 isolated backend tests, ESLint, Ruff and Vite build passed.
The sample-data preview build passed 20 frontend/demo tests, lint and build.
PostgreSQL migration idempotency/preservation was verified in a temporary schema
and rolled back; the final migration was applied to local development only.

Browser preview checked all nine image guides, each method, native keyboard
expand/collapse, reset when switching, new-batch options, light/dark readability
and no horizontal overflow at 390x844. No console warnings/errors were observed.
Preview expires 6 November 2026. See `COMPOST_GUIDES_UPDATE.md` for the link,
verification details and release status. Neon, live hosting and the installed
APK are unchanged by this review update; no live AI call or production test data.

### 0.2.4 approved release — 30 October 2026

Owner approved the guide preview. Shared Neon revision 0004 applied after a
private scoped catalogue backup; all original catalogue rows were compared
and retained. No production test accounts, scan/check-in/claim records or live
Gemini requests were created. User records and points were not changed.

Vercel production `dpl_2iG1t5twRCANs116RP4p59XUFmns` (source `1cf8b7a`)
was staged with production configuration, checked through authenticated read-only
requests, then promoted. Public API health reports connected database/configured
Gemini/PostgreSQL photos. The catalogue returns the three approved methods and
nine stages; live HTML/JS match the built assets.

Exact approved Firebase preview `319b06181b108bcb` (frontend source `a34d1c7`)
was cloned to live. Live HTML, release metadata, JS and CSS match the preview;
AI, backend, accounts and uploads remain disabled in the trainer demo. The
published guide and expanded first image were visibly checked in the browser.

Android build succeeded. APK 0.2.4 / 20261033 contains nine guide assets and the
existing online API URL with no dev-server URL, Google key pattern or demo
adapter. Installed with app data preserved and launched on the connected phone;
versionCode/versionName verified on-device. Native guide interaction and a live
AI response remain for owner testing. No billing or security settings changed.

APK SHA256: `d4941693100a5cddd2a5896fabea618685a496c4b2c86c1c67f6579d333d2ff8`.
See `COMPOST_GUIDES_UPDATE.md` for release details and artifact locations.
