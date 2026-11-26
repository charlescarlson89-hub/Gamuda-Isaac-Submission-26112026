import test from "node:test";
import assert from "node:assert/strict";
import { createDemoApi, privatePhoto, STORAGE_KEY } from "../src/services/demo-runtime.js";
import catalog, { sampleScan, sampleMatch } from "../src/services/demo-catalogue.js";

function fixture() {
  const values = new Map();
  const storage = { getItem: (key) => values.get(key), setItem: (key, value) => values.set(key, value) };
  const api = createDemoApi({ catalog, sampleScan, sampleMatch, storage });
  return { api, values, storage };
}
test("demo never calls the network or saves supplied credentials", async () => {
  const { api, values, storage } = fixture();
  const original = globalThis.fetch;
  globalThis.fetch = () => { throw new Error("Network must never be used"); };
  try {
    await assert.rejects(api("/state"), { status: 401 });
    await api("/auth/login", { method: "POST", body: { identifier: "do-not-store@example.test", password: "private-test-value" } });
    const state = await api("/state");
    assert.equal(state.profile.name, "Trainer");
    assert.deepEqual(state.catalog.fertilizers.map(({ id }) => id), [4, 5, 6, 7, 8]);
    for (const id of ["vinda-tissue", "vinda-kitchen-paper", "petpet-diapers"]) {
      assert.ok(state.catalog.rewards.some((reward) => reward.id === id));
    }
    const match = await api(`/scans/${state.scan.id}/method-match`);
    assert.ok(state.catalog.fertilizers.some(({ id }) => id === match.recommendation.recipeId));
    assert.equal(state.scan.pointsEarned, 0);
    const saved = values.get(STORAGE_KEY);
    assert.ok(!saved.includes("private-test-value") && !saved.includes("do-not-store"));
    assert.equal((await createDemoApi({ catalog, sampleScan, sampleMatch, storage })("/state")).profile.id, "trainer-demo");
    await assert.rejects(api("/scans", { method: "POST" }), { status: 501 });
    await assert.rejects(api("/ai/chat", { method: "POST" }), { status: 501 });
    await assert.rejects(privatePhoto("/api/photos/1"), { status: 501 });
    await api("/auth/logout", { method: "POST" });
    await assert.rejects(api("/state"), { status: 401 });
  } finally { globalThis.fetch = original; }
});
test("demo preserves independent batches, ordered stages and single awards", async () => {
  const { api, values } = fixture();
  await api("/auth/register", { method: "POST", body: {} });
  const initial = await api("/state");
  assert.equal((await api("/daily-checkins", { method: "POST" })).pointsAwarded, 10);
  assert.equal((await api("/daily-checkins", { method: "POST" })).pointsAwarded, 0);
  assert.equal((await api("/state")).balance, initial.balance + 10);
  assert.equal(initial.batches[0].quests.length, 3);
  const created = await api("/batches", { method: "POST", body: { name: "Trainer bin", fertilizer_type_id: 8, client_request_id: "demo-new" } });
  assert.equal(created.quests.length, 4);
  await assert.rejects(api(`/batches/${created.id}`, { method: "DELETE" }), { status: 409 });
  const form = new FormData(); form.append("note", "Demo stage");
  form.append("photo", "DO-NOT-PERSIST-PHOTO");
  await assert.rejects(api(`/batches/${created.id}/quests/2/complete`, { method: "POST", body: form }), { status: 409 });
  await assert.rejects(api(`/batches/${created.id}/quests/5/complete`, { method: "POST", body: form }), { status: 404 });
  for (const week of [1, 2, 3, 4]) {
    const path = `/batches/${created.id}/quests/${week}/complete`;
    const approved = await api(path, { method: "POST", body: form });
    assert.equal(approved.pointsAwarded, 100);
    assert.equal(approved.batch.quests[week - 1].status, "DONE");
    assert.equal(approved.batch.progress, week * 25);
    assert.equal(approved.batch.checkins.at(-1).verification, null);
    assert.equal(approved.batch.checkins.at(-1).photoUrl, null);
    assert.ok(!values.get(STORAGE_KEY).includes("DO-NOT-PERSIST-PHOTO"));
    assert.equal((await api(path, { method: "POST", body: form })).pointsAwarded, 0);
  }
  await api(`/batches/${created.id}`, { method: "DELETE" });
  assert.equal((await api("/state")).batches.length, initial.batches.length);
  assert.ok(!values.get(STORAGE_KEY).includes("DO-NOT-PERSIST-PHOTO"));
});
test("demo reward retries produce one clearly invalid claim and debit", async () => {
  const { api } = fixture();
  await api("/auth/login", { method: "POST" });
  const before = (await api("/state")).balance;
  const reward = catalog.rewards.find((row) => row.id === "eco-bag");
  for (let i = 0; i < 3; i++) {
    const result = await api("/rewards/eco-bag/claims", { method: "POST" });
    assert.equal(result.claim.claimCode, "DEMO-NOT-REDEEMABLE");
  }
  const state = await api("/state");
  assert.equal(state.balance, before - reward.cost);
  assert.equal(state.redemptions.length, 1);
});
