// Empty/undefined resolves to a relative path, so the browser always calls
// the api at the page's own origin (proxied by next.config.ts's rewrite)
// rather than a build-time-baked host -- see docs/DOST_DEMO.md Section 5.
// An operator can still override it with an absolute URL when needed.
export function normalizeApiBaseUrl(value?: string): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) {
    return "";
  }
  const url = new URL(trimmed);
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

// Server-only: the container-to-container api target for the initial,
// server-rendered health fetch (apps/web/src/app/page.tsx) -- never sent to
// the browser. Mirrors next.config.ts's rewrite defaults, which the browser
// uses for every subsequent client-side refresh instead.
export function internalHealthEndpoint(): string {
  const host = process.env.KENDRA_API_INTERNAL_HOST || "api";
  const port = process.env.KENDRA_API_INTERNAL_PORT || "8000";
  return `http://${host}:${port}/api/v1/health`;
}

// Baked in at `npm run build` time via apps/web/Dockerfile's build ARG/ENV
// (mirroring NEXT_PUBLIC_KENDRA_API_BASE_URL); never hard-coded here. Falls
// back to "unknown" for a plain `npm run dev` where no build arg was supplied.
export function gitCommit(): string {
  return process.env.NEXT_PUBLIC_KENDRA_GIT_COMMIT || "unknown";
}
