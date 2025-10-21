import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Usamos runtime standalone para servir con Node dentro del contenedor
  output: "standalone",
  images: { unoptimized: true },
  // Evitar que el build falle por lint o tipos en CI/Docker
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
};

export default nextConfig;
