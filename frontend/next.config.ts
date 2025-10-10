import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Export estático para servir con Nginx
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
