import React, { createContext, useContext, useEffect, useState } from "react";
import {
  applyTheme,
  readThemePreference,
  resolveTheme,
  saveThemePreference,
  themeOptions,
  themeStorageKey,
} from "./appearance";

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [preference, setPreference] = useState(() =>
    readThemePreference(),
  );
  const [systemDark, setSystemDark] = useState(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const theme = resolveTheme(preference, systemDark);
  useEffect(() => {
    applyTheme(preference);
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const followSystem = () => {
      setSystemDark(media.matches);
      applyTheme(preference);
    };
    followSystem();
    media.addEventListener("change", followSystem);
    return () => media.removeEventListener("change", followSystem);
  }, [preference]);
  useEffect(() => {
    const sync = (event) => {
      if (event.key === themeStorageKey || event.key === null)
        setPreference(readThemePreference());
    };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  function chooseTheme(value) {
    if (!themeOptions.includes(value)) return;
    applyTheme(value);
    saveThemePreference(undefined, value);
    setPreference(value);
  }
  return (
    <ThemeContext.Provider value={{ preference, theme, chooseTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
