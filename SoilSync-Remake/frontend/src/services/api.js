import { Capacitor, CapacitorHttp } from "@capacitor/core";
import { nativePayload } from "./native-payload";

const base = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const nativeHeaders = () =>
  Capacitor.isNativePlatform() ? { Origin: location.origin } : {};
let csrfToken = null;
let csrfRequest = null;

async function request(
  path,
  { method = "GET", body, headers = {}, signal } = {},
) {
  signal?.throwIfAborted();
  if (Capacitor.isNativePlatform() && base) {
    // Native networking retains secure server cookies and an explicit Origin;
    // the Android app does not depend on third-party WebView cookie settings.
    const payload = await nativePayload(body);
    const result = await CapacitorHttp.request({
      url: `${base}${path}`,
      method,
      ...payload,
      headers: {
        ...nativeHeaders(),
        ...headers,
        ...(body instanceof FormData
          ? { "Content-Type": "multipart/form-data" }
          : {}),
      },
      responseType: "json",
      connectTimeout: 15000,
      readTimeout: 60000,
    });
    signal?.throwIfAborted();
    return new Response(
      result.status === 204 ? null : JSON.stringify(result.data),
      { status: result.status, headers: result.headers },
    );
  }
  return fetch(`${base}${path}`, {
    method,
    credentials: "include",
    headers,
    signal,
    body:
      body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function readResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.map((item) => item.msg).join(" ");
    throw new ApiError(
      detail || "SoilSync could not complete this request. Please try again.",
      response.status,
    );
  }
  return data;
}

async function csrf() {
  if (csrfToken) return csrfToken;
  if (!csrfRequest)
    csrfRequest = request("/api/auth/csrf")
      .then(readResponse)
      .then((data) => {
        csrfToken = data.csrfToken;
        return csrfToken;
      })
      .finally(() => {
        csrfRequest = null;
      });
  return csrfRequest;
}

export async function api(path, { method = "GET", body, signal } = {}) {
  const headers = nativeHeaders();
  try {
    if (method !== "GET") headers["X-CSRF-Token"] = await csrf();
    if (body && !(body instanceof FormData))
      headers["Content-Type"] = "application/json";
    const response = await request(`/api${path}`, {
      method,
      headers,
      signal,
      body,
    });
    if (response.status === 403) csrfToken = null;
    return await readResponse(response);
  } catch (error) {
    if (error instanceof ApiError || error.name === "AbortError") throw error;
    throw new ApiError(
      "Could not reach SoilSync. Please try again when the service is available.",
      0,
    );
  }
}

export function clearCsrf() {
  csrfToken = null;
}

export async function privatePhoto(path, signal) {
  if (!/^\/api\/photos\/\d+$/.test(path))
    throw new ApiError("Invalid photo reference.", 400);
  if (Capacitor.isNativePlatform() && base) {
    signal?.throwIfAborted();
    const response = await CapacitorHttp.get({
      url: `${base}${path}`,
      headers: nativeHeaders(),
      responseType: "arraybuffer",
      connectTimeout: 15000,
      readTimeout: 30000,
    });
    signal?.throwIfAborted();
    if (response.status !== 200)
      throw new ApiError("This private photo is unavailable.", response.status);
    return new Blob(
      [Uint8Array.from(atob(response.data), (char) => char.charCodeAt(0))],
      { type: "image/jpeg" },
    );
  }
  const response = await fetch(`${base}${path}`, {
    credentials: "include",
    headers: nativeHeaders(),
    signal,
  });
  if (!response.ok)
    throw new ApiError("This private photo is unavailable.", response.status);
  return response.blob();
}
