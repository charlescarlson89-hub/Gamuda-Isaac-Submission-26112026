import React from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router-dom";
import { SoilSyncProvider } from "./state";
import App from "./App";
import { ThemeProvider } from "./ThemeProvider";
import { applyTheme, readThemePreference } from "./appearance";
import "./styles.css";
import "./app-polish.css";
import "./final-design.css";
import "./appearance.css";
import "./readability.css";
applyTheme(readThemePreference());
createRoot(document.getElementById("root")).render(
  <HashRouter>
    <ThemeProvider>
      <SoilSyncProvider>
        <App />
      </SoilSyncProvider>
    </ThemeProvider>
  </HashRouter>,
);
