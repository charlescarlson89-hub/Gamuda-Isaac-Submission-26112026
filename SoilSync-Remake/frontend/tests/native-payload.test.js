import test from "node:test";
import assert from "node:assert/strict";
import { nativePayload } from "../src/services/native-payload.js";

test("Android multipart transport preserves image bytes and Unicode notes", async () => {
  const bytes = new Uint8Array([0, 255, 216, 195, 0, 128, 254]);
  const form = new FormData();
  form.append("photo", new File([bytes], "scraps.jpg", { type: "image/jpeg" }));
  form.append("note", "Compost observation 🌱");
  const payload = await nativePayload(form);
  assert.equal(payload.dataType, "formData");
  const file = payload.data.find((row) => row.key === "photo");
  assert.deepEqual(new Uint8Array(Buffer.from(file.value, "base64")), bytes);
  assert.equal(file.fileName, "scraps.jpg");
  assert.equal(file.contentType, "image/jpeg");
  assert.equal(
    payload.data.find((row) => row.key === "note").value,
    "Compost observation 🌱",
  );
});
