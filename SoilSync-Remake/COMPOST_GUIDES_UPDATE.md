# SoilSync 0.2.4 — compost guides release

Review preview (sample data, AI off):
https://soilsync-bdd70--soilsync-compost-024-2o9pusft.web.app/#/fertilizer

Available until 6 November 2026. Open the preview with the supplied sample login.
The preview does not create real accounts, analyse photos or update shared data.

## Changes

- Exactly three methods for recipes, new batches and scan recommendations:
  Hot Composting (ID 4), Cold Composting (ID 5), Bokashi Composting (ID 6).
- Three independent native dropdowns per method. Each reveals a local SVG
  illustration and database instructions. All nine illustrations have alt text.
- Method switching resets expanded steps; Enter opens/closes a focused step.
  Touch targets, text contrast and reduced-motion behaviour follow app themes.
- Guidance differentiates aerobic piles from sealed Bokashi fermentation and
  further breakdown. Leaffy's guide and AI instructions list current methods.
- Recipe IDs 1–3 remain historical records. Existing batches preserve their
  recipe identity; new batches cannot select historical methods. Existing scan
  detections remain stored unchanged while recommendations resolve to current
  database matches. Dry garden browns do not match the Bokashi food route.

Sources: EPA home composting, CalRecycle home composting and the RHS Bokashi
 guide. Source links appear beneath the illustrated steps.

## Database and release status

Released on 30 October 2026 after the owner approved the review.

- Local and shared Neon databases are at Alembic revision 0004. A private scoped
  catalogue backup was saved before the shared migration. Every pre-existing
  catalogue row was compared afterward and preserved exactly. No user, batch,
  scan, point, account or photo record was edited by the migration.
- Online API/frontend: https://soilsync-api.vercel.app/ . Production deployment
  `dpl_2iG1t5twRCANs116RP4p59XUFmns`, built from source `1cf8b7a`, was staged,
  verified read-only using Vercel authentication, then promoted. Public health,
  catalogue, HTML and JS checks passed. Gemini is configured; no live provider
  request was made by the agent.
- Firebase trainer demo: https://soilsync-bdd70.web.app/ . Exact tested preview
  `319b06181b108bcb` from frontend source `a34d1c7` was cloned to live. HTML,
  release metadata and JS/CSS matched the approved preview byte-for-byte. Demo
  mode, AI off, no real accounts and no uploads remain in effect.
- Android 0.2.4 / 20261033 built successfully, installed over the existing app on
  OPPO CPH2607 and launched. Package version was checked on-device. All nine
  guide images and the hosted API URL are bundled; no development server URL,
  Google key pattern or demo adapter is in the APK. Native interaction and AI
  responses were not independently exercised after installation.
- Ready APK: workspace parent
  `output/soilsync-0.2.4/SoilSync-0.2.4-online-debug.apk`.
  SHA256: `d4941693100a5cddd2a5896fabea618685a496c4b2c86c1c67f6579d333d2ff8`.

Frozen migration SQL remains in `backend/alembic/data/0004_compost_methods.sql`;
`backend/sql/006_compost_methods.sql` is the pgAdmin equivalent. The shared
migration is already applied; do not create another database or reset the seed.
No billing, permissions, Firebase Auth/Storage or API credential settings changed.

## Verification

- 18 frontend tests, ESLint, Vite build, 54 isolated backend tests and Ruff passed.
- Preview build: 20 frontend/demo tests, lint and build passed at source a34d1c7.
- Frozen PostgreSQL migration ran twice in an isolated schema; original recipe
  data remained unchanged and all synthetic schema/data were rolled back.
  Updated migration then applied successfully to the local development database.
- Preview checked at 390x844: three method options; all nine loaded images;
  expand/collapse, Enter activation, reset on switching, new-batch selector,
  light/dark text readability and no horizontal overflow. Browser console had
  no warnings/errors. Temporary viewport override was restored.
- No live Gemini request, production test record, billing or security change
  was made. The approved cloud catalogue migration is recorded above.
  Screenshots are in the workspace parent's
  `output/soilsync-0.2.4/` folder.
