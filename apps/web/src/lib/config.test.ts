import { afterEach, describe, expect, it } from "vitest";

import { gitCommit, healthEndpoint, normalizeApiBaseUrl } from "./config";

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

describe("gitCommit", () => {
  const originalValue = process.env.NEXT_PUBLIC_KENDRA_GIT_COMMIT;

  afterEach(() => {
    process.env.NEXT_PUBLIC_KENDRA_GIT_COMMIT = originalValue;
  });

  it("reports the build-time commit when baked in", () => {
    process.env.NEXT_PUBLIC_KENDRA_GIT_COMMIT = "abc1234";
    expect(gitCommit()).toBe("abc1234");
  });

  it("falls back to unknown when no commit was baked in", () => {
    delete process.env.NEXT_PUBLIC_KENDRA_GIT_COMMIT;
    expect(gitCommit()).toBe("unknown");
  });
});
