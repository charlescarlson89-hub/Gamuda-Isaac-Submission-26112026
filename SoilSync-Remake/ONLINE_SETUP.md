# SoilSync mobile and online backend

The Android app bundles the React screens and opens the app directly. An HTTPS
FastAPI backend supplies login, the catalogue, Gemini image analysis, batches,
check-ins and rewards. PostgreSQL stores account data and private approved
check-in photos. The Gemini key belongs only in the server environment.

## Vercel backend

The current live frontend and API are at https://soilsync-api.vercel.app/.
Swagger is at https://soilsync-api.vercel.app/docs.

Deploy `backend/` as the `soilsync-api` project, using `backend/vercel.json`.
The project uses the free Hobby plan. No paid service is enabled by these files.
Provider quotas still apply; a free hosting plan does not promise unlimited AI.

Required production variables:

- `APP_ENV=production`
- `DATABASE_URL`: a working PostgreSQL connection URL using SSL
- `GEMINI_API_KEY`: sensitive server variable
- `GEMINI_MODEL`: a vision model available to that key
- `COOKIE_SECURE=true`
- `UPLOAD_STORAGE=postgres`
- `FRONTEND_ORIGINS`: JSON list containing `https://localhost`,
  `capacitor://localhost` and the actual public frontend origin if hosted

Keep `.env`, `.vercel`, passwords, local uploads and service-account files out of
Git and deployment uploads. `.vercelignore` excludes local development files.
Run migrations explicitly after checking the destination database. Do not replace
existing team tables or run mock-account seeding against production.

The local PostgreSQL database and Neon are separate databases. A connection in
pgAdmin does not automatically copy or synchronize data between them.

## Android build

From the project root in PowerShell:

```powershell
npm run android:build -- -ApiBaseUrl https://soilsync-api.vercel.app
```

The build rejects an insecure or localhost backend URL. The generated APK is
`frontend/android/app/build/outputs/apk/debug/app-debug.apk`. It is signed for
local device testing, not a Play Store release. The package ID is retained so
it can update the earlier USB app without uninstalling it.

For USB-only development, use `npm run android:build -- -Usb` and start the local
services. The normal configuration has no USB server address.

## Verification before installing the online APK

1. Check HTTPS `/api/health`: database connected, Gemini configured, photo storage
   `postgres`.
2. Check login, catalogue and persistent account state through the hosted API.
3. Test a real waste image and confirm database IDs and recipe matches.
4. Test approved compost proof and rejection of unrelated photos; verify that
   another account cannot view the photo.
5. Build with the confirmed API URL, install the APK, and test with USB reverse
   forwarding removed. Internet is required for login and AI; the laptop is not.

The UI labels image percentages as identification confidence. A photograph does
not measure NPK composition or prove compost maturity. Rewards remain project
concepts until partner fulfilment is connected.

## Device handoff — 30 October 2026

Version 0.2.0 (20261029) was installed successfully as an update on the connected
OPPO CPH2607 and launched. The APK bundles its screens, targets the live HTTPS API,
has no development server URL and does not contain a Google API key. No USB
reverse forwarding was configured during this check.

Read-only cloud checks returned HTTP 200 for the frontend, OpenAPI (25 paths), and
health. Health reported database connected, Gemini configured and PostgreSQL
photo storage. Configuration alone does not prove a successful live AI request.

At the owner's request, no production test accounts, scans, batches, check-ins or
claims were created, and no new Gemini calls were made during this handoff. The
owner confirmed that login and an AI waste scan work on the phone with USB
disconnected. This is an owner-reported device test; it does not establish general
recognition accuracy or verify every workflow.

### Appearance update

Version 0.2.3 (20261032) is the latest installed device build. Open Profile →
Appearance and choose Device, Light or Dark. This preference is saved locally
on each device and does not require a database migration. The update also
adjusts app typography, reduces plant-card names and fixes switch thumb travel.
Version 0.2.2 also fixes the expanded maintenance cards' text contrast in both
light and dark themes.

### Leaffy and the daily tip board

Leaffy now sits beside the Home screen's Did you know? board. Tap her or Ask
Leaffy to open chat. She sleeps at night (19:00–07:00 Kuala Lumpur time), wakes
when tapped and uses the existing daytime blink/wave routine. Reduced-motion
preferences and the chat's pause control are supported.

The board has 16 short, sourced composting tips. Its starting tip changes at
Kuala Lumpur midnight; Another tip browses the library without an AI request.
Tip sources: https://www.epa.gov/recycle/composting-home and
https://compost.css.cornell.edu/faq.html.

Chat uses the existing server-side Gemini endpoint and does not award points.
Messages are held in screen memory rather than saved to the app database.
When live AI is unavailable, a clearly labelled bundled project guide can
answer common questions. The updated backend prompt and frontend were promoted
to https://soilsync-api.vercel.app/; no database migration is needed.
