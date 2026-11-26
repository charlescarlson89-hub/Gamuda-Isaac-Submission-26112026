import test from "node:test";
import assert from "node:assert/strict";
import {
  availableCompostMethods,
  emptyState,
  localDay,
  rewardAvailability,
  batchProgress,
  selectedBatch,
} from "../src/model.js";

test("the picker limits options to the preferred methods that match, or lists all guides", () => {
  const methods = [4, 5, 6, 7, 8].map((id) => ({ id }));
  const options = (blender, rice) => availableCompostMethods(methods, {
    featuredMethods: [{ id: 7, matchesScan: blender }, { id: 8, matchesScan: rice }],
  }).map(({ id }) => id);
  assert.deepEqual(options(true, true), [7, 8]);
  assert.deepEqual(options(false, true), [8]);
  assert.deepEqual(options(false, false), [4, 5, 6, 7, 8]);
  assert.deepEqual(availableCompostMethods(methods, null), methods);
});

test("signed-out state has no account identity, cached wallet or batches", () => {
  const state = emptyState();
  assert.equal(state.profile.id, null);
  assert.equal(state.balance, 0);
  assert.deepEqual(state.batches, []);
  assert.deepEqual(state.catalog.pointRules, {
    daily: 10,
    scan: 50,
    weekly: 100,
  });
});
test("daily display follows Kuala Lumpur midnight regardless of host timezone", () => {
  assert.equal(localDay("2026-10-20T15:59:59Z"), "2026-10-20");
  assert.equal(localDay("2026-10-20T16:00:00Z"), "2026-10-21");
});
test("claimed, inactive and unaffordable rewards have distinct button states", () => {
  const bag = { id: "eco-bag", cost: 50, active: true };
  assert.equal(rewardAvailability(emptyState(), bag), "50 more pts");
  assert.equal(rewardAvailability({ ...emptyState(), balance: 50 }, bag), null);
  assert.equal(
    rewardAvailability(
      { ...emptyState(), balance: 100, redemptions: [{ rewardId: "eco-bag" }] },
      bag,
    ),
    "Already claimed",
  );
  assert.equal(
    rewardAvailability(emptyState(), { ...bag, active: false }),
    "Currently unavailable",
  );
});
test("explicit unknown/deleted batch IDs cannot select another user's displayed batch", () => {
  const first = { id: "11", progress: 100, checkins: [1, 2, 3] };
  const second = { id: "12", progress: 33, checkins: [1] };
  const state = { ...emptyState(), batches: [first, second] };
  assert.equal(selectedBatch(state), second);
  assert.equal(selectedBatch(state, "11"), first);
  assert.equal(selectedBatch(state, "999"), undefined);
  assert.equal(selectedBatch(emptyState()), undefined);
});
test("progress uses the server value and cannot overflow its display bounds", () => {
  assert.equal(batchProgress({ progress: 67, checkins: [] }), 67);
  assert.equal(batchProgress({ progress: 150, checkins: [] }), 100);
  assert.equal(batchProgress({ progress: -1, checkins: [] }), 0);
});
