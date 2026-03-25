import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@autopilot/types", "@autopilot/ws"],
};

export default nextConfig;
