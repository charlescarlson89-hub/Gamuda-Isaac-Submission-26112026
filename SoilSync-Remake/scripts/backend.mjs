import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
const backend = fileURLToPath(new URL("../backend/", import.meta.url));
const python = fileURLToPath(
  new URL(
    process.platform === "win32"
      ? "../backend/.venv/Scripts/python.exe"
      : "../backend/.venv/bin/python",
    import.meta.url,
  ),
);
const commands = {
  dev: [
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8001",
    "--reload",
  ],
  test: [
    "-m",
    "pytest",
    "tests",
    "-q",
    "--basetemp",
    `.runtime/pytest-${Date.now()}`,
  ],
  migrate: ["-m", "alembic", "upgrade", "head"],
  seed: ["scripts/seed.py"],
  smoke: ["scripts/smoke_test.py"],
  "reset-password": ["scripts/reset_password.py"],
  "hosting-demo": ["scripts/build_hosting_demo.py"],
  lint: ["-m", "ruff", "check", "app", "scripts", "tests"],
};
const selected = commands[process.argv[2]];
if (!selected) {
  console.error("Choose dev, test, migrate, seed or lint.");
  process.exit(1);
}
const result = spawnSync(python, [...selected, ...process.argv.slice(3)], {
  cwd: backend,
  stdio: "inherit",
  windowsHide: true,
});
if (result.error)
  console.error("Run npm run setup first.", result.error.message);
process.exit(result.status ?? 1);
