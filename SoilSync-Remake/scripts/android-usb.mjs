import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";
import { promisify } from "node:util";
import { pathToFileURL } from "node:url";

const execute = promisify(execFile);
const sdk = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT ||
  (process.platform === "win32"
    ? join(process.env.LOCALAPPDATA || join(homedir(), "AppData", "Local"), "Android", "Sdk")
    : join(homedir(), process.platform === "darwin" ? "Library/Android/sdk" : "Android/Sdk"));
const adb = join(sdk, "platform-tools", process.platform === "win32" ? "adb.exe" : "adb");

// Only the authorised device with our USB test package is eligible. Never grant
// debugging/OS permissions or alter forwarding ports belonging to other apps.
export function startAndroidUsb() {
  if (!existsSync(adb)) return () => {};
  let stopped = false;
  let timer;
  let previous = "";
  const announce = (message) => {
    if (message !== previous) console.log(`SoilSync USB: ${message}`);
    previous = message;
  };
  const run = async (...args) =>
    (await execute(adb, args, { windowsHide: true, timeout: 5000 })).stdout;
  async function check() {
    try {
      const devices = (await run("devices")).split(/\r?\n/)
        .map((line) => line.trim().split(/\s+/))
        .filter(([, state]) => state === "device")
        .map(([serial]) => serial);
      const selected = process.env.SOILSYNC_ANDROID_SERIAL;
      const serial = selected
        ? devices.find((device) => device === selected)
        : devices.length === 1 ? devices[0] : null;
      if (!serial) {
        announce("waiting for one authorised USB phone (or set SOILSYNC_ANDROID_SERIAL).");
        return;
      }
      if (!(await run("-s", serial, "shell", "pm", "path", "com.tedabyte.soilsync.usb")).includes("package:")) {
        announce("install SoilSync USB on the selected phone first.");
        return;
      }
      const forwards = await run("-s", serial, "reverse", "--list");
      if (!forwards.split(/\r?\n/).some((line) => /\stcp:5173\s+tcp:5173\s*$/.test(line))) {
        await run("-s", serial, "reverse", "tcp:5173", "tcp:5173");
        announce("connection restored. Retry the app request.");
      } else {
        announce("connected; keeping the link ready while this terminal runs.");
      }
    } catch {
      announce("waiting for the USB connection; check the cable and debugging authorisation.");
    } finally {
      if (!stopped) timer = setTimeout(check, 3000);
    }
  }
  check();
  return () => { stopped = true; clearTimeout(timer); };
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  if (!existsSync(adb)) {
    console.error("Android platform-tools not found. Set ANDROID_HOME to your Android SDK.");
    process.exitCode = 1;
  } else {
    const stop = startAndroidUsb();
    process.on("SIGINT", () => { stop(); process.exit(0); });
    process.on("SIGTERM", () => { stop(); process.exit(0); });
  }
}
