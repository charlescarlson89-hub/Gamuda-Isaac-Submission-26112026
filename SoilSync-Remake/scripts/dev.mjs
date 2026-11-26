import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { createServer } from "node:net";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";
import { startAndroidUsb } from "./android-usb.mjs";
import {
  startStorage,
  exportStorage,
  usesStorageEmulator,
} from "./storage-runtime.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const backend = fileURLToPath(new URL("../backend/", import.meta.url));
const python = fileURLToPath(
  new URL(
    process.platform === "win32"
      ? "../backend/.venv/Scripts/python.exe"
      : "../backend/.venv/bin/python",
    import.meta.url,
  ),
);
if (!existsSync(python)) {
  console.error(
    "Run npm run setup first to install the frontend and backend dependencies.",
  );
  process.exit(1);
}
const emulate = usesStorageEmulator();
for (const port of [8001, 5173, ...(emulate ? [9199, 4000, 4400, 4500] : [])]) {
  try {
    await new Promise((resolve, reject) => {
      const server = createServer();
      server.once("error", reject);
      server.listen(port, "127.0.0.1", () => server.close(resolve));
    });
  } catch {
    console.error(
      `Port ${port} is in use. Stop the existing SoilSync task with Ctrl+C, then try npm run dev again.`,
    );
    process.exit(1);
  }
}
const children = [];
let closing = false;
let backup;
let stopUsb = () => {};
async function stop(code = 0) {
  if (closing) return;
  closing = true;
  stopUsb();
  clearInterval(backup);
  if (emulate && !(await exportStorage()))
    console.error(
      "Could not export emulator photos. Check backend/.runtime/firebase-data before restarting.",
    );
  for (const child of children) {
    if (!child.pid || child.exitCode !== null) continue;
    if (process.platform === "win32")
      spawn("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
        stdio: "ignore",
        windowsHide: true,
      });
    else child.kill("SIGTERM");
  }
  setTimeout(() => process.exit(code), 600);
}
function watch(child, name) {
  children.push(child);
  child.on("error", (error) => {
    if (closing) return;
    console.error(`${name}: ${error.message}`);
    void stop(1);
  });
  child.on("exit", (code, signal) => {
    if (closing) return;
    console.error(`${name} stopped (${signal || code}).`);
    void stop(code || 1);
  });
}

async function waitForApi() {
  const apiBase = "http://127.0.0.1:8001/api";
  const deadline = Date.now() + 40_000;
  let status;
  while (!closing && Date.now() < deadline) {
    try {
      const response = await fetch(`${apiBase}/health`, {
        signal: AbortSignal.timeout(7_000),
      });
      status = response.status;
      await response.body?.cancel();
      if (response.ok) break;
    } catch {
      status = undefined;
    }
    await delay(350);
  }
  if (closing) return;
  if (status !== 200) {
    throw new Error(
      status
        ? `FastAPI health check returned HTTP ${status}. Check the database connection and the FastAPI log above.`
        : "FastAPI did not respond. Check the FastAPI log above.",
    );
  }
  const catalogue = await fetch(`${apiBase}/catalog`, {
    signal: AbortSignal.timeout(20_000),
  });
  await catalogue.body?.cancel();
  if (!catalogue.ok) {
    throw new Error(`FastAPI catalogue returned HTTP ${catalogue.status}. Check the FastAPI log above.`);
  }
}

process.on("SIGINT", () => void stop());
process.on("SIGTERM", () => void stop());
if (emulate) {
  watch(startStorage(), "Firebase Storage emulator");
  backup = setInterval(() => exportStorage(), 60000);
}
const api = spawn(
  python,
  [
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8001",
    "--reload",
    "--reload-dir",
    "app",
    "--reload-include",
    ".env",
  ],
  {
    cwd: backend,
    stdio: "inherit",
    windowsHide: true,
    env: { ...process.env, SOILSYNC_USE_SAVED_DATABASES: "1" },
  },
);
watch(api, "FastAPI");
console.log("Waiting for FastAPI and the recipe catalogue before starting React...");
try {
  await waitForApi();
} catch (error) {
  if (!closing) {
    console.error(`SoilSync startup failed. ${error.message}`);
    await stop(1);
  }
}
if (!closing) {
  const web =
    process.platform === "win32"
      ? spawn(
          process.env.ComSpec || "cmd.exe",
          ["/d", "/s", "/c", "npm --prefix frontend run dev"],
          { cwd: root, stdio: "inherit", windowsHide: true },
        )
      : spawn("npm", ["--prefix", "frontend", "run", "dev"], {
          cwd: root,
          stdio: "inherit",
        });
  watch(web, "React");
  stopUsb = startAndroidUsb();
  console.log(
    "SoilSync: frontend http://127.0.0.1:5173/ · API docs http://127.0.0.1:8001/docs",
  );
}
