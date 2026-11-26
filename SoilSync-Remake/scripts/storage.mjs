import { spawn } from "node:child_process";
import { startStorage, exportStorage } from "./storage-runtime.mjs";

const child = startStorage();
let closing = false;
const backup = setInterval(() => exportStorage(), 60000);
async function stop() {
  if (closing) return;
  closing = true;
  clearInterval(backup);
  if (!(await exportStorage()))
    console.error(
      "Storage export failed. Keep the emulator open and retry before stopping it.",
    );
  if (process.platform === "win32")
    spawn("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
      stdio: "ignore",
      windowsHide: true,
    });
  else child.kill("SIGINT");
  setTimeout(() => process.exit(), 800);
}
child.on("error", (error) => {
  console.error(error.message);
  process.exit(1);
});
child.on("exit", (code) => {
  if (!closing) process.exit(code || 0);
});
process.on("SIGINT", stop);
process.on("SIGTERM", stop);
