# Firebase Hosting trainer demo — 30 October 2026

Live website: https://soilsync-bdd70.web.app/

Released on **30 October 2026 (MYT)** from the verified `soilsync-compost-024` preview.
Preview version: `319b06181b108bcb`; exact preview cloned to live.
Frontend source commit: `a34d1c76645e73770e3dfc55ce005d61043af72d` (SoilSync 0.2.4).
Live entry JavaScript: `/assets/index-B78Me9eX.js`.
Live stylesheet: `/assets/index-BnUtqIvw.css`.

This release presents the latest committed frontend screens with an isolated, browser-only sample-data adapter. It replaces the older frontend snapshot. The normal frontend and FastAPI application sources retain their existing API integration.

## Show the trainer

Open the live link, choose **Explore SoilSync**, then **Log In** with the supplied sample fields. No real password is required. The registration tab is a visual preview and creates no account.

The demo includes the latest mobile screens, cinematic landing page, Home daily tip board with animated Leaffy, Device/Light/Dark appearance, corrected notification switches, larger typography, multiple batches, sample weekly stages, rewards and history, sample scans, recipes/plant guidance, profile and logout. The only selectable methods are Hot, Cold and Bokashi Composting, each with three expandable illustrated steps. In either camera flow choose **Use sample photo · demo only** to explore without granting camera access.

The banner states **Trainer frontend demo · Sample data · AI off · No online accounts**. AI scanning is disabled. Leaffy answers from the built-in project guide. Weekly stages add sample points without claiming AI approval. Reward receipts say `DEMO-NOT-REDEEMABLE`.

Notes, profile edits, sample points and claims stay in the visitor's browser under a separate demo storage key. Photos remain temporary local previews: no photo is uploaded, stored or analysed. Entering the demo ignores supplied credential fields; passwords and email inputs are not retained. The catalogue comes from an in-memory synthetic seed, not the real database. No API/Gemini request is made, and the laptop can be off.

## Verification

- 20 frontend/demo tests passed, including no-network operation, ignored credentials/photos, reload persistence, independent batches, ordered stages, single point awards/debits and private-photo rejection without network access.
- ESLint, production build and backend-script Ruff passed.
- Production dependency audit: zero findings. Dependency installation reported three moderate development-tool findings; those tools are not served by static Hosting. No unrelated dependency upgrades were applied.
- Firebase preview browser checks passed: sample access, Home, Leaffy guide labels and EcoPoints answer, dark mode, notification switch off/on positions, sample scan/result, ordered weekly check-in save and its 100 sample points, and updated 23-item reward catalogue.
- Built public assets checked for credential patterns: no matches. The isolated generated demo contains no online API transport.
- Exact tested preview cloned to live. Live HTML, release metadata and entry JavaScript/CSS matched the local build byte-for-byte. Live demo login and Home/banner were visibly verified. Screenshot: workspace parent `output/soilsync-0.2.4/live-firebase-guide.png`.
- The last read-only Cloud Billing check on 30 October verified **disabled**. Only static Hosting content published by this Firebase update. No backend, database, Storage bucket, Firebase Auth configuration or billing settings changed. Hosting remains subject to no-cost quotas.
- Preview deployment used `--no-authorized-domains` to avoid Firebase Auth-domain synchronization. The real API-connected frontend, Android APK and Vercel service were not modified by this update.

## Rebuild and update

From the project root:

```powershell
npm run build:hosting-demo
```

The builder exports `HEAD`'s frontend into a new ignored release folder, checks demo-copy substitutions, substitutes the transport, generates a synthetic catalogue, installs dependencies, runs tests/lint and builds. It strips inherited `VITE_*` overrides and prints the generated Firebase config path. It does not deploy or modify local application screens. Commit frontend changes before building. Review failed substitutions when changing screen copy rather than bypassing them.

Deploy the printed config to preview, inspect it, then promote:

```powershell
node node_modules/firebase-tools/lib/bin/firebase.js hosting:channel:deploy soilsync-remake-review --expires 2d --project soilsync-bdd70 --config PATH_PRINTED_BY_BUILD --non-interactive --no-authorized-domains
node node_modules/firebase-tools/lib/bin/firebase.js hosting:clone soilsync-bdd70:soilsync-remake-review soilsync-bdd70:live --project soilsync-bdd70 --non-interactive
```

The root `firebase.json` remains the local Storage emulator configuration. The generated release config contains Hosting only. Do not deploy `firebase.hosting.example.json` with its unconfigured future backend rewrite. Earlier live versions remain in Hosting release history; previous approved preview/live content was `26093f9a8d565518`.

Refresh an old page with **Ctrl+F5**. The deployed `/release.json` identifies the frontend source and disabled online capabilities.
