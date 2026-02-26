import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  basePath: "/tracking",
  trailingSlash: false,
};

export default nextConfig;