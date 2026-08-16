const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function normalizeApiBaseUrl(value?: string): string {
  const url = new URL(value || DEFAULT_API_BASE_URL);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("NEXT_PUBLIC_KENDRA_API_BASE_URL must use HTTP or HTTPS");
  }
  if (url.username || url.password) {
    throw new Error("NEXT_PUBLIC_KENDRA_API_BASE_URL must not contain credentials");
  }
  return url.toString().replace(/\/$/, "");
}

export function healthEndpoint(value?: string): string {
  return `${normalizeApiBaseUrl(value)}/api/v1/health`;
}
