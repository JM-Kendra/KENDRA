import { describe, expect, it } from "vitest";

import { healthEndpoint, normalizeApiBaseUrl } from "./config";

describe("frontend configuration", () => {
  it("builds the health URL from the configured loopback API", () => {
    expect(healthEndpoint("http://127.0.0.1:9000/")).toBe(
      "http://127.0.0.1:9000/api/v1/health",
    );
  });

  it("rejects credentials in a browser-visible API URL", () => {
    expect(() => normalizeApiBaseUrl("http://user:secret@localhost:8000")).toThrow(
      "must not contain credentials",
    );
  });
});
