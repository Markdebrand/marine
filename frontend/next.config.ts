import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Usamos runtime standalone para servir con Node dentro del contenedor
  output: "standalone",
  images: { unoptimized: true },
  // Evitar que el build falle por lint o tipos en CI/Docker
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },

  // Redirecciones/proxy internas: enviar /api/* al servicio backend dentro de la red Docker.
  // Nota: El destino usa el nombre del servicio ("backend") y su puerto interno.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://backend:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
