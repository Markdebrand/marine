import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Optimiza para contenedores: genera salida standalone para reducir tamaño de imagen
  output: "standalone",
  async redirects() {
    return [
      {
        source: "/",
        destination: "/login",
        permanent: false,
      },
      {
        source: "/about",
        destination: "/login",
        permanent: false,
      },
      {
        source: "/services",
        destination: "/login",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
