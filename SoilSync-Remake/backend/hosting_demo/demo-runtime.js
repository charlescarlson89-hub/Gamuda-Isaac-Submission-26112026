// Copied only into the static trainer build. Never imported by the live app.
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export async function privatePhoto() {
  throw new ApiError("Trainer demo: no private photos are stored or fetched.", 501);
}

export const STORAGE_KEY = "soilsync-trainer-demo-2026-10-22";
export function createDemoApi({ catalog, sampleScan, sampleMatch, storage, now = () => new Date(), uuid = () => crypto.randomUUID() }) {
  const clone = (value) => structuredClone(value);
  const at = () => now().toISOString();
  const scanExample = { ...sampleScan, at: at() };
  function refreshStages(batch) {
    // The trainer keeps three short sample stages for the original methods.
    const total = batch.fertilizerTypeId === 8 ? 4 : 3;
    const done = batch.checkins.length;
    batch.progress = Math.round(done / total * 100);
    batch.status = done === total ? "Completed" : "Active";
    batch.quests = Array.from({ length: total }, (_, index) => ({
      id: `${batch.id}-quest-${index + 1}`,
      week: index + 1,
      status: index < done ? "DONE" : index === done ? "CURRENT" : "UPCOMING",
      points: 100,
      canClaim: index === done,
    }));
    return batch;
  }
  function batch(id, name, count, recipeId = 4) {
    return refreshStages({
      id, name, number: "DEMO", fertilizerTypeId: recipeId, fertilizerName: catalog.fertilizers.find(r => r.id === recipeId)?.name, startedAt: at(),
      estimatedCompletionDate: null,
      checkins: Array.from({ length: count }, (_, i) => ({
        id: `${id}-week-${i + 1}`, week: i + 1, at: at(),
        note: "Illustrative demo check-in. No photo or AI verification.", photoUrl: null, verification: null,
      })),
    });
  }
  let state = {
    version: 3,
    profile: { id: null, name: "Trainer", email: "trainer@soilsync.example", location: "Kota Kinabalu", tier: "Tier 1: Beginner", streakDays: 0 },
    balance: 1278, checkins: [], redemptions: [],
    preferences: { checkin: true, rewards: true, service: true, claim: true },
    quietHours: { start: "22:00", end: "07:00" },
    batches: [batch("demo-kitchen", "Kitchen batch · demo", 1), batch("demo-garden", "Garden batch · demo", 3, 5)],
    scan: scanExample, catalog,
  };
  try {
    const saved = JSON.parse(storage?.getItem(STORAGE_KEY) || "null");
    if (saved?.version === 3 && saved.profile?.email === "trainer@soilsync.example" && Array.isArray(saved.batches) && Array.isArray(saved.redemptions) && Number.isSafeInteger(saved.balance) && saved.balance >= 0) {
      state = { ...saved, catalog, scan: scanExample };
      const legacy = { 1: "Home aerobic compost", 2: "Worm compost", 3: "Leafmould soil conditioner" };
      state.batches = state.batches.map(b => refreshStages({ ...b, fertilizerName: b.fertilizerName || legacy[b.fertilizerTypeId] || catalog.fertilizers.find(r => r.id === b.fertilizerTypeId)?.name }));
    }
  } catch { /* A fresh in-memory demo also works when storage is unavailable. */ }
  function persist() {
    try { storage?.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* Optional local persistence. */ }
  }
  return async function api(path, { method = "GET", body } = {}) {
    if (path === "/ai/chat" || path === "/scans")
      throw new ApiError("Trainer demo: live AI is off. Browse the illustrative example and project guide.", 501);
    if (["/auth/login", "/auth/register"].includes(path) && method === "POST") {
      // Deliberately ignore every credential field; never save a password or email.
      state.profile.id = "trainer-demo";
      persist();
      return { user: clone(state.profile) };
    }
    if (path === "/auth/logout" && method === "POST") {
      state.profile.id = null;
      persist();
      return { ok: true };
    }
    if (!state.profile.id) throw new ApiError("Open the trainer demo first.", 401);
    if (path === "/state" && method === "GET") return clone(state);
    if (path === `/scans/${scanExample.id}/method-match` && method === "GET") return clone(sampleMatch);
    let result = true;
    if (path === "/profile" && method === "PATCH") {
      state.profile.name = String(body.username).trim().slice(0, 40) || "Trainer";
      state.profile.location = String(body.location).trim().slice(0, 80);
    } else if (path === "/daily-checkins" && method === "POST") {
      const today = now().toLocaleDateString("en-CA", { timeZone: "Asia/Kuala_Lumpur" });
      const pointsAwarded = state.checkins.includes(today) ? 0 : 10;
      if (!state.checkins.includes(today)) {
        state.checkins.push(today);
        state.balance += 10;
      }
      result = { pointsAwarded };
    } else if (path === "/user-settings" && method === "PATCH") {
      const keys = { checkin_reminder: "checkin", reward_received_notify: "rewards", service_notices_notify: "service", claim_reward_reminder: "claim" };
      for (const [key, value] of Object.entries(body)) if (keys[key]) state.preferences[keys[key]] = Boolean(value);
    } else if (path === "/batches" && method === "POST") {
      if (!catalog.fertilizers.some((row) => row.id === body.fertilizer_type_id)) throw new ApiError("Choose a recipe.", 422);
      result = state.batches.find((row) => row.id === body.client_request_id);
      if (!result) {
        result = batch(body.client_request_id || uuid(), String(body.name).trim().slice(0, 60), 0, body.fertilizer_type_id);
        state.batches.push(result);
      }
    } else if (/^\/batches\/[^/]+$/.test(path) && method === "DELETE") {
      const id = decodeURIComponent(path.split("/")[2]);
      const selected = state.batches.find((row) => row.id === id);
      if (!selected) throw new ApiError("Batch not found.", 404);
      if (selected.progress < 100) throw new ApiError("Complete the demo stages first.", 409);
      state.batches = state.batches.filter((row) => row.id !== id);
    } else if (/^\/batches\/[^/]+\/quests\/[1-9]\d*\/complete$/.test(path) && method === "POST") {
      const parts = path.split("/"), week = Number(parts[4]);
      const selected = state.batches.find((row) => row.id === decodeURIComponent(parts[2]));
      if (!selected) throw new ApiError("Batch not found.", 404);
      if (week > selected.quests.length) throw new ApiError("Demo stage not found.", 404);
      if (week > selected.checkins.length + 1) throw new ApiError("Complete stages in order.", 409);
      const pointsAwarded = week <= selected.checkins.length ? 0 : 100;
      if (pointsAwarded) {
        // Ignore photo fields entirely: no upload, storage or AI approval.
        selected.checkins.push({ id: uuid(), week, at: at(), note: String(body?.get("note") || "Demo observation").slice(0, 250), photoUrl: null, verification: null });
        refreshStages(selected);
        state.balance += pointsAwarded;
      }
      result = { batch: selected, pointsAwarded };
    } else if (/^\/rewards\/[^/]+\/claims$/.test(path) && method === "POST") {
      const rewardId = decodeURIComponent(path.split("/")[2]);
      const reward = catalog.rewards.find((row) => row.id === rewardId);
      if (!reward || !reward.active) throw new ApiError("Reward unavailable.", 404);
      let claim = state.redemptions.find((row) => row.rewardId === rewardId);
      if (!claim) {
        if (state.balance < reward.cost) throw new ApiError("Not enough demo points.", 409);
        claim = { id: uuid(), rewardId, at: at(), cost: reward.cost, claimCode: "DEMO-NOT-REDEEMABLE", expiresAt: null, isRedeemed: false };
        state.redemptions.push(claim);
        state.balance -= reward.cost;
      }
      result = { claim };
    } else throw new ApiError("This feature is not available in the frontend demo.", 501);
    persist();
    return clone(result);
  };
}
