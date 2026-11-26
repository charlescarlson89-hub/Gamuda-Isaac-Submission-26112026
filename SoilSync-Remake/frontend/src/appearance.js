export const themeStorageKey = "soilsync:appearance:v1";
export const themeOptions = ["system", "light", "dark"];

export function readThemePreference(storage) {
  try {
    const value = (storage ?? window.localStorage).getItem(themeStorageKey);
    return themeOptions.includes(value) ? value : "system";
  } catch {
    return "system";
  }
}

export function resolveTheme(preference, systemDark) {
  return preference === "dark" || (preference === "system" && systemDark)
    ? "dark"
    : "light";
}

export function saveThemePreference(storage, preference) {
  if (!themeOptions.includes(preference)) return;
  try {
    (storage ?? window.localStorage).setItem(themeStorageKey, preference);
  } catch {
    // The theme still works for this session when device storage is unavailable.
  }
}

export function applyTheme(preference) {
  const theme = resolveTheme(
    preference,
    window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute(
    "content",
    theme === "dark" ? "#2a332c" : "#d9e0ce",
  );
}
