import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { emptyState } from "./model";
import { api, clearCsrf } from "./services/api";

const Context = createContext(null);
const preferenceKeys = {
  checkin: "checkin_reminder",
  rewards: "reward_received_notify",
  service: "service_notices_notify",
  claim: "claim_reward_reminder",
};

export function SoilSyncProvider({ children }) {
  const [state, setState] = useState(emptyState);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [loadError, setLoadError] = useState("");
  const inFlight = useRef(false);
  const current = useRef(state);
  const publish = useCallback((next) => {
    current.current = next;
    setState(next);
  }, []);
  const refresh = useCallback(async () => {
    try {
      const next = await api("/state");
      publish(next);
      setLoadError("");
      return next;
    } catch (error) {
      if (error.status === 401) {
        publish(emptyState());
        setLoadError("");
        return null;
      }
      setLoadError(error.message);
      throw error;
    }
  }, [publish]);
  useEffect(() => {
    refresh()
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [refresh]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(""), 6000);
    return () => clearTimeout(timer);
  }, [notice]);

  async function authenticate(mode, body) {
    if (inFlight.current) return false;
    inFlight.current = true;
    setBusy(true);
    try {
      await api(`/auth/${mode}`, { method: "POST", body });
      await refresh();
      return true;
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  async function act(action) {
    if (inFlight.current) return false;
    inFlight.current = true;
    setBusy(true);
    try {
      let result;
      switch (action.type) {
        case "PROFILE":
          result = await api("/profile", {
            method: "PATCH",
            body: { username: action.name, location: action.location },
          });
          break;
        case "CHECKIN":
          result = await api("/daily-checkins", { method: "POST" });
          break;
        case "PREFERENCE":
          result = await api("/user-settings", {
            method: "PATCH",
            body: { [preferenceKeys[action.key]]: action.value },
          });
          break;
        case "START_BATCH":
          result = await api("/batches", {
            method: "POST",
            body: {
              name: action.name,
              fertilizer_type_id: Number(action.fertilizerTypeId),
              client_request_id: action.id || crypto.randomUUID(),
            },
          });
          break;
        case "DELETE_BATCH":
          result = await api(`/batches/${encodeURIComponent(action.batchId)}`, {
            method: "DELETE",
          });
          break;
        case "BATCH_CHECKIN": {
          const batch = current.current.batches.find(
            (row) => row.id === action.batchId,
          );
          if (!batch || !action.photo)
            throw new Error("Choose a batch and a check-in photo first.");
          const form = new FormData();
          form.append("photo", action.photo, "weekly-checkin.jpg");
          form.append("note", action.note || "");
          result = await api(
            `/batches/${encodeURIComponent(batch.id)}/quests/${action.week}/complete`,
            { method: "POST", body: form },
          );
          break;
        }
        case "REDEEM": {
          const response = await api(
            `/rewards/${encodeURIComponent(action.rewardId)}/claims`,
            {
              method: "POST",
              body: { request_id: action.id || crypto.randomUUID() },
            },
          );
          result = response.claim;
          break;
        }
        case "SIGNOUT":
          await api("/auth/logout", { method: "POST" });
          clearCsrf();
          publish(emptyState());
          setNotice("");
          return true;
        default:
          throw new Error("This action is unavailable.");
      }
      await refresh();
      return result || true;
    } catch (error) {
      setNotice(error.message);
      if (error.status === 401) publish(emptyState());
      return false;
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  async function scanPhoto(photo) {
    if (inFlight.current) return null;
    inFlight.current = true;
    setBusy(true);
    try {
      const form = new FormData();
      form.append("photo", photo, "waste-photo.jpg");
      const result = await api("/scans", { method: "POST", body: form });
      const next = await refresh();
      if (next) publish({ ...next, scan: result.scan });
      setNotice(
        result.duplicate
          ? "This photo was already recorded. No additional points awarded."
          : result.pointsAwarded
            ? `Waste identified. +${result.pointsAwarded} EcoPoints!`
            : "No compostable waste identified. No points awarded.",
      );
      return result.scan;
    } catch (error) {
      setNotice(error.message);
      throw error;
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  return (
    <Context.Provider
      value={{
        state,
        act,
        authenticate,
        refresh,
        scanPhoto,
        loading,
        busy,
        notice,
        setNotice,
        loadError,
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useSoilSync() {
  const value = useContext(Context);
  if (!value) throw new Error("SoilSyncProvider is required.");
  return value;
}
