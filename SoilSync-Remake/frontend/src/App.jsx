import React, { useEffect } from "react";
import { Capacitor } from "@capacitor/core";
import {
  Link,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import {
  Bell,
  Camera,
  ChevronLeft,
  CirclePlus,
  Home as HomeIcon,
  SlidersHorizontal,
  Sprout,
} from "lucide-react";
import { useSoilSync } from "./state";
import Welcome from "./pages/Welcome";
import Home from "./pages/Home";
import Rewards, { RedemptionHistory } from "./pages/Rewards";
import Scan from "./pages/Scan";
import { Fertilizer, Batch, WasteGuide } from "./pages/Garden";
import CheckinCamera from "./pages/CheckinCamera";
import Settings from "./pages/Settings";
import LandingPage from "./pages/LandingPage";

const navigation = [
  ["/home", "Home", HomeIcon, "Home"],
  ["/rewards", "Rewards", CirclePlus, "Rewards"],
  ["/scan", "", Camera, "Snap waste"],
  ["/fertilizer", "Fertilizer", Sprout, "Fertilizer and compost guides"],
  ["/profile", "Profile", SlidersHorizontal, "Your profile"],
];
function Layout() {
  const { state, notice, loadError, loading, refresh, busy } = useSoilSync();
  const location = useLocation();
  const titles = {
    "/home": "SoilSync",
    "/scan": "Snap Waste",
    "/scan/result": "Snap Waste",
    "/fertilizer": "Make Fertilizer Guide",
    "/batch": "Active Batch Tracker",
    "/settings": "Settings & Notifications",
    "/profile": "Settings & Notifications",
    "/rewards": "Rewards",
    "/rewards/history": "Redemption History",
    "/learn": "Back",
  };
  const cameraRoute = location.pathname === "/batch/check-in";
  const wasteRoute = location.pathname === "/learn";
  const scanRoute = ["/scan", "/scan/result"].includes(location.pathname);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);
  if (loading)
    return (
      <main className="welcome-page final-welcome" aria-busy="true">
        <h1>SoilSync</h1>
        <p>Loading your account…</p>
      </main>
    );
  if (!state.profile.id) return <Navigate to="/login" replace />;
  return (
    <div
      className={`app-shell final-app ${cameraRoute ? "camera-route" : ""} ${wasteRoute ? "waste-route" : ""}`}
    >
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      {!cameraRoute && (
        <header className="app-header">
          <div className="header-brand-row">
            <Link
              className="icon-button back-button"
              to={
                location.pathname === "/rewards/history" ? "/rewards" : "/home"
              }
              aria-label="Back to home"
            >
              <ChevronLeft size={23} />
            </Link>
            <Link
              to="/home"
              className="header-brand"
              aria-label="SoilSync home"
            >
              <strong>{titles[location.pathname] || "SoilSync"}</strong>
            </Link>
          </div>
          {["/home", "/scan", "/scan/result"].includes(location.pathname) && (
            <div className="header-actions">
              <Link
                to="/settings"
                className="icon-button notification-button"
                aria-label="Notification settings"
              >
                <Bell size={21} strokeWidth={1.5} />
                <i />
              </Link>
            </div>
          )}
        </header>
      )}
      <main
        id="main-content"
        key={scanRoute ? location.key : location.pathname}
        className="app-view"
        tabIndex={-1}
      >
        <Outlet />
      </main>
      {loadError && (
        <div className="storage-alert" role="alert">
          <p>{loadError}</p>
          <button
            className="text-button"
            onClick={() => refresh().catch(() => {})}
          >
            Try again
          </button>
        </div>
      )}
      {notice && (
        <div className="toast" role="status">
          {notice}
        </div>
      )}
      {!cameraRoute && !wasteRoute && (
        <nav className="bottom-nav" aria-label="Main navigation">
          {navigation.map(([to, label, Icon, accessibleLabel]) => (
            <NavLink
              key={to}
              to={to}
              state={to === "/scan" ? { openCamera: true } : undefined}
              aria-disabled={to === "/scan" && scanRoute && busy ? true : undefined}
              onClick={(event) => {
                if (to === "/scan" && scanRoute && busy) event.preventDefault();
              }}
              aria-label={accessibleLabel}
              className={({ isActive }) =>
                `${to === "/scan" ? "scan-tab" : ""} ${isActive ? "active" : ""}`
              }
            >
              <span>
                <Icon size={23} strokeWidth={1.8} aria-hidden="true" />
              </span>
              <b>{label}</b>
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
}
export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          Capacitor.isNativePlatform() ? (
            <Navigate to="/home" replace />
          ) : (
            <LandingPage />
          )
        }
      />
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/welcome" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Welcome />} />
      <Route element={<Layout />}>
        <Route path="/home" element={<Home />} />
        <Route path="/rewards" element={<Rewards />} />
        <Route path="/rewards/history" element={<RedemptionHistory />} />
        <Route path="/scan" element={<Scan />} />
        <Route path="/scan/result" element={<Scan />} />
        <Route path="/fertilizer" element={<Fertilizer />} />
        <Route path="/batch" element={<Batch />} />
        <Route path="/batch/check-in" element={<CheckinCamera />} />
        <Route path="/learn" element={<WasteGuide />} />
        <Route path="/profile" element={<Settings profile />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  );
}
