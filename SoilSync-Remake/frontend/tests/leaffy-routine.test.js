import test from "node:test";
import assert from "node:assert/strict";
import {
  getLeaffyPeriod,
  nextSunshineDelay,
  shouldLeaffyYawn,
} from "../src/services/leaffyRoutine.js";

test("Leaffy follows 07:00–19:00 Kuala Lumpur time regardless of host timezone", () => {
  for (const [iso, period] of [
    ["2026-10-15T22:59:59Z", "night"],
    ["2026-10-15T23:00:00Z", "day"],
    ["2026-10-16T10:59:59Z", "day"],
    ["2026-10-16T11:00:00Z", "night"],
    ["2026-10-16T16:00:00Z", "night"],
  ])
    assert.equal(getLeaffyPeriod(new Date(iso)), period, iso);
});

test("Sunshine bursts use a bounded random delay", () => {
  assert.equal(nextSunshineDelay(0), 24000);
  assert.equal(nextSunshineDelay(0.5), 36000);
  assert.equal(nextSunshineDelay(1), 48000);
  assert.equal(nextSunshineDelay(-1), 24000);
  assert.equal(nextSunshineDelay(2), 48000);
});

test("Idle yawn waits 45 seconds without activity", () => {
  assert.equal(shouldLeaffyYawn(200000, 155001, 0), false);
  assert.equal(shouldLeaffyYawn(200000, 155000, 0), true);
  assert.equal(shouldLeaffyYawn(200000, 199000, 0), false);
});

test("Yawn cooldown prevents repeated yawns and rejects backwards clock intervals", () => {
  assert.equal(shouldLeaffyYawn(200000, 0, 140000), false);
  assert.equal(shouldLeaffyYawn(205000, 0, 140000), true);
  assert.equal(shouldLeaffyYawn(200000, 210000, 0), false);
});
