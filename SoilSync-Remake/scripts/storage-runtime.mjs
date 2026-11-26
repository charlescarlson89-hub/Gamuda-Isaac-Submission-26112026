import { existsSync, readdirSync, readFileSync } from "node:fs";
import { delimiter, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

export const root = fileURLToPath(new URL("../", import.meta.url));
const cli = join(root, "node_modules/firebase-tools/lib/bin/firebase.js");
const data = join(root, "backend/.runtime/firebase-data");
export function usesStorageEmulator() {
  const env = readFileSync(join(root, "backend/.env"), "utf8");
  return (
    /^UPLOAD_STORAGE=firebase\s*$/m.test(env) &&
    /^STORAGE_EMULATOR_HOST=http:\/\/127\.0\.0\.1:9199\s*$/m.test(env)
  );
}
export function storageEnvironment() {
  const env = { ...process.env };
  const javaRoot = join(root, "backend/.runtime/java");
  const portable =
    existsSync(javaRoot) &&
    readdirSync(javaRoot).find((name) =>
      existsSync(join(javaRoot, name, "bin", "java.exe")),
    );
  if (portable) {
    env.JAVA_HOME = join(javaRoot, portable);
    env.PATH = join(env.JAVA_HOME, "bin") + delimiter + env.PATH;
  }
  return env;
}
export function startStorage() {
  if (!existsSync(cli))
    throw new Error(
      "Run npm install in the project root to install Firebase tools.",
    );
  const args = [
    cli,
    "emulators:start",
    "--only",
    "storage",
    "--project",
    "soilsync-bdd70",
    `--export-on-exit=${data}`,
  ];
  if (existsSync(join(data, "firebase-export-metadata.json")))
    args.push(`--import=${data}`);
  return spawn(process.execPath, args, {
    cwd: root,
    env: storageEnvironment(),
    stdio: "inherit",
    windowsHide: true,
  });
}
export async function exportStorage() {
  return new Promise((resolve) => {
    const child = spawn(
      process.execPath,
      [cli, "emulators:export", data, "--project", "soilsync-bdd70", "--force"],
      {
        cwd: root,
        env: storageEnvironment(),
        stdio: "ignore",
        windowsHide: true,
      },
    );
    const timeout = setTimeout(() => {
      child.kill();
      resolve(false);
    }, 20000);
    child.once("error", () => {
      clearTimeout(timeout);
      resolve(false);
    });
    child.once("exit", (code) => {
      clearTimeout(timeout);
      resolve(code === 0);
    });
  });
}
