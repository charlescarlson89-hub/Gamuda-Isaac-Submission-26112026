export const localDay = (at = new Date()) =>
  new Date(at).toLocaleDateString("en-CA", { timeZone: "Asia/Kuala_Lumpur" });

export function availableCompostMethods(methods, match) {
  const preferred = (match?.featuredMethods || []).filter((method) => method.matchesScan);
  const options = methods.filter((method) => preferred.some(({ id }) => id === method.id));
  return options.length ? options : methods;
}

// Signed-out state contains no cached account data or locally minted points.
export function emptyState() {
  return {
    version: 3,
    profile: { id: null, name: "", email: "", location: "Kota Kinabalu" },
    balance: 0,
    checkins: [],
    redemptions: [],
    preferences: { checkin: true, rewards: true, service: true, claim: true },
    quietHours: { start: "22:00", end: "07:00" },
    batches: [],
    scan: null,
    catalog: {
      rewards: [],
      fertilizers: [],
      wasteTypes: [],
      pointRules: { daily: 10, scan: 50, weekly: 100 },
    },
  };
}

export function rewardAvailability(state, reward) {
  if (reward.active === false) return "Currently unavailable";
  if (state.redemptions.some((claim) => claim.rewardId === reward.id))
    return "Already claimed";
  if (state.balance < reward.cost)
    return `${reward.cost - state.balance} more pts`;
  return null;
}

export const batchProgress = (batch) =>
  Math.max(
    0,
    Math.min(
      100,
      Number.isFinite(batch.progress)
        ? batch.progress
        : Math.round((batch.checkins.length / (batch.quests?.length || 3)) * 100),
    ),
  );

export function selectedBatch(state, id) {
  return id
    ? state.batches.find((batch) => String(batch.id) === String(id))
    : state.batches.find((batch) => batchProgress(batch) < 100) ||
        state.batches[0];
}
