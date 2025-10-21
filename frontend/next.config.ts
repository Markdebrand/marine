import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Export estático para servir con Nginx
  output: "export",
  images: { unoptimized: true },
  // Evitar que el build falle por lint o tipos en CI/Docker
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
};

export default nextConfig;
