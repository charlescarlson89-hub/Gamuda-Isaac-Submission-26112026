# SoilSync USB (Android development build)

This installs the full frontend as a separate **SoilSync USB** app
(`com.tedabyte.soilsync.usb`). It uses FastAPI, PostgreSQL and Google Gemini on
your laptop over USB. It needs the cable connected and the laptop running.
Your existing SoilSync installation and its data are separate.

The Android app opens directly to the dashboard for an active session, or to
login when signed out. The website keeps its landing page.

## Phone interface trial

Home uses a compact points overview, a scan shortcut and two batch previews.
**Show all batches** expands the remaining batches. Daily check-in and the waste
guide search sit below them. Bottom navigation uses **Home / Rewards / Scan /
Grow / You**, with full accessible labels for the existing destinations.

On Android, Scan opens the camera. Capture a photo, review it, then explicitly
choose **Identify waste** to send it for analysis. Retake and Gallery remain
available. The camera stops when leaving the screen or backgrounding the app;
choose Open camera to resume after returning. Motion respects the device's
reduced-motion preference. These changes are a design trial on the Android
test branch, pending team review.

## Start it again

From this project folder in VS Code:

```powershell
npm run dev
```

`npm run dev` also maintains the USB forwarding link when Android platform-tools
are installed. Unlock the phone and authorise USB debugging when prompted.
If the dev server was started before this reconnect helper was added, run this
in a second terminal and leave it running:

```powershell
npm run android:connect
```

Open **SoilSync USB** on the phone. The helper restores the forwarding link after
reconnecting USB or restarting the phone; retry a failed request after it says
the connection is restored. With multiple authorised devices, set
`SOILSYNC_ANDROID_SERIAL` to the intended phone's ADB serial first.
Accept the camera permission on the phone when
you choose **Use camera**. Only camera access is requested; no microphone access.

The private server configuration remains at
`%LOCALAPPDATA%/SoilSyncRemake/.env`. No Gemini key or database password goes into
the APK. An active Google AI account's own quota/pricing applies to AI requests;
this build does not enable billing or create cloud services.

## Rebuild and install

```powershell
npm run android:build
& "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe" install -r frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

The build script requires an installed Android SDK (API 36) and Java 21. Set
`JAVA_HOME` or `ANDROID_HOME` if they are not in the detected Windows locations.
The APK uses a development signature. Do not uninstall an existing app to bypass
a signature mismatch without backing up its data first.

## Development-only configuration

`frontend/capacitor.config.json` points at `http://127.0.0.1:5173`, forwarded over
ADB USB. Vite proxies `/api` to FastAPI at `127.0.0.1:8001`, so session cookies
and CSRF protection use the same origin as the existing web app.

Cleartext HTTP is enabled only by the Android debug manifest, for this loopback
development connection. This is not a standalone release APK or a Play Store
configuration. A public mobile release needs an HTTPS backend, a bundled frontend
configuration and release signing. Firebase's trainer demo is unchanged.
# Current online app

The latest phone app is SoilSync 0.2.3 and works through the hosted HTTPS API.
See [ONLINE_SETUP.md](ONLINE_SETUP.md) for the normal Android build. The USB
instructions below are retained for laptop-only development; pass `-Usb` to the
Android build script for that configuration.
