import { spawnSync } from "node:child_process";
import { existsSync, copyFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

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
function run(command, args, cwd = root) {
  const result = spawnSync(command, args, {
    cwd,
    stdio: "inherit",
    windowsHide: true,
  });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if (result.status !== 0) process.exit(result.status || 1);
}
if (process.platform === "win32") {
  run(process.env.ComSpec || "cmd.exe", ["/d", "/s", "/c", "npm ci"]);
  run(process.env.ComSpec || "cmd.exe", [
    "/d",
    "/s",
    "/c",
    "npm --prefix frontend ci",
  ]);
} else {
  run("npm", ["ci"]);
  run("npm", ["--prefix", "frontend", "ci"]);
}
if (!existsSync(python))
  run(
    process.env.PYTHON || (process.platform === "win32" ? "python" : "python3"),
    ["-m", "venv", "backend/.venv"],
  );
run(python, ["-m", "pip", "install", "-r", "requirements.lock.txt"], backend);
const env = fileURLToPath(new URL("../backend/.env", import.meta.url));
if (!existsSync(env))
  copyFileSync(
    fileURLToPath(new URL("../backend/.env.example", import.meta.url)),
    env,
  );
console.log(
  "Dependencies installed. Configure backend/.env, create your database, then run npm run db:migrate and npm run db:seed.",
);
