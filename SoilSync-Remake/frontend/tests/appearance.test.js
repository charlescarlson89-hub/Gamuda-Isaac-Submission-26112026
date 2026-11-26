import test from "node:test";
import assert from "node:assert/strict";
import {
  readThemePreference, resolveTheme, saveThemePreference, themeStorageKey,
} from "../src/appearance.js";

test("device theme follows system changes; explicit choices take precedence", () => {
  assert.equal(resolveTheme("system", true), "dark");
  assert.equal(resolveTheme("system", false), "light");
  assert.equal(resolveTheme("light", true), "light");
  assert.equal(resolveTheme("dark", false), "dark");
});

test("theme choice survives reload and rejects unknown persisted values", () => {
  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key),
    setItem: (key, value) => values.set(key, value),
  };
  assert.equal(readThemePreference(storage), "system");
  saveThemePreference(storage, "dark");
  assert.equal(readThemePreference(storage), "dark");
  saveThemePreference(storage, "unexpected");
  assert.equal(readThemePreference(storage), "dark");
  values.set(themeStorageKey, "unexpected");
  assert.equal(readThemePreference(storage), "system");
});

test("blocked device storage does not prevent appearance selection", () => {
  const storage = {
    getItem() { throw new Error("Storage blocked"); },
    setItem() { throw new Error("Storage blocked"); },
  };
  assert.equal(readThemePreference(storage), "system");
  assert.doesNotThrow(() => saveThemePreference(storage, "dark"));
});
