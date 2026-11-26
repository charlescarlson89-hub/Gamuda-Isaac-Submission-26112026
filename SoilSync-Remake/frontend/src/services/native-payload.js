// Capacitor's native multipart bridge transports file bytes as base64.
export async function nativePayload(body) {
  if (!(body instanceof FormData)) return { data: body };
  const data = [];
  for (const [key, value] of body.entries()) {
    if (value instanceof Blob) {
      const bytes = new Uint8Array(await value.arrayBuffer());
      let binary = "";
      for (let offset = 0; offset < bytes.length; offset += 32768)
        binary += String.fromCharCode(
          ...bytes.subarray(offset, offset + 32768),
        );
      data.push({
        key,
        value: btoa(binary),
        type: "base64File",
        contentType: value.type,
        fileName: value.name || "photo.jpg",
      });
    } else data.push({ key, value, type: "string" });
  }
  return { data, dataType: "formData" };
}
