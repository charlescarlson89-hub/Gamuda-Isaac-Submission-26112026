import test from "node:test";
import assert from "node:assert/strict";
import { compostTips, dailyCompostTip } from "../src/data/compostTips.js";
import { localDay } from "../src/model.js";

test("daily tips change at Kuala Lumpur midnight and cycle without duplicates", () => {
  const before = localDay(new Date("2026-10-29T15:59:59Z"));
  const after = localDay(new Date("2026-10-29T16:00:00Z"));
  assert.notEqual(dailyCompostTip(before).id, dailyCompostTip(after).id);
  const seen = new Set(compostTips.map((_, i) => dailyCompostTip(after, i).id));
  assert.equal(seen.size, compostTips.length);
  assert.equal(dailyCompostTip(after, compostTips.length).id, dailyCompostTip(after).id);
  assert.equal(dailyCompostTip(after, -1).id, dailyCompostTip(after, compostTips.length - 1).id);
});

test("all editorial tips remain short and link to a verified primary source", () => {
  assert.equal(new Set(compostTips.map(tip => tip.id)).size, compostTips.length);
  for (const tip of compostTips) {
    assert.ok(tip.text.length > 20 && tip.text.length < 150);
    assert.ok(["www.epa.gov", "compost.css.cornell.edu"].includes(new URL(tip.source.url).hostname));
  }
});
