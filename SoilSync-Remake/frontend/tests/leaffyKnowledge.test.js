import test from "node:test";
import assert from "node:assert/strict";
import { findLeaffyAnswer } from "../src/services/leaffyKnowledge.js";

test("offline guide describes the current app rather than the retired local AI prototype", () => {
  const technology = findLeaffyAnswer("What technology is SoilSync built with?");
  assert.match(technology, /Gemini/);
  assert.match(technology, /Neon PostgreSQL/);
  assert.doesNotMatch(technology, /Ollama|qwen|local FastAPI/);
  assert.match(findLeaffyAnswer("Where is Leaffy?"), /daily tip board/);
});

test("offline points guide keeps chat free of invented points or real vouchers", () => {
  const reply = findLeaffyAnswer("How do rewards and points work?");
  assert.match(reply, /10 EcoPoints/);
  assert.match(reply, /Chat earns no points/);
  assert.match(reply, /fulfilment is not connected/);
});


test("method guidance distinguishes sealed Bokashi from aerobic methods", () => {
  const bokashi = findLeaffyAnswer("How do I do Bokashi composting?");
  assert.match(bokashi, /sealed bucket/);
  assert.match(bokashi, /away from roots/);
  const methods = findLeaffyAnswer("Which composting methods are available?");
  for (const name of ["Hot Composting", "Cold Composting", "Bokashi Composting"]) assert.ok(methods.includes(name));
});
