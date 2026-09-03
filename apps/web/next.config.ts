import type { NextConfig } from "next";

// Internal, container-to-container target for the /api rewrite below --
// never browser-visible. Defaults match docker-compose.yml's `api` service
// name/port; KENDRA_API_INTERNAL_HOST/_PORT let a non-default compose
// project (e.g. a drill under a different project name) override them.
// Read at server start (this file runs inside the Next.js standalone
// server, not baked into the client bundle), so a plain container restart
// with a different environment picks up a new value without a rebuild.
const apiInternalHost = process.env.KENDRA_API_INTERNAL_HOST || "api";
const apiInternalPort = process.env.KENDRA_API_INTERNAL_PORT || "8000";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `http://${apiInternalHost}:${apiInternalPort}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
