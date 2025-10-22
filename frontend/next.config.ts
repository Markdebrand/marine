import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Optimiza para contenedores: genera salida standalone para reducir tamaño de imagen
  output: "standalone",
};

export default nextConfig;
