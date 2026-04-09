"use client";
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { Protected } from "@/components/auth/Protected";
import AisLiveMap from "@/app/(app)/map/components/ais/AisLiveMap";
import { useMapStore } from "@/app/(app)/map/store/mapStore";

// Monta el mapa una sola vez y lo muestra/oculta según la ruta
export default function PersistentMapHost() {
  const pathname = usePathname();
  const isMap = pathname === "/map" || pathname?.startsWith("/map/");
  const wasVisible = useRef<boolean>(isMap ?? false);
  // Track if map was ever requested on this session to avoid loading it entirely on heavy pages
  const [hasMounted, setHasMounted] = useState<boolean>(isMap ?? false);
  
  const center = useMapStore((s) => s.center);
  const zoom = useMapStore((s) => s.zoom);

  // Mount map once requested
  useEffect(() => {
    if (isMap && !hasMounted) {
      setHasMounted(true);
    }
  }, [isMap, hasMounted]);

  // Al volver a mostrarlo tras estar oculto, forzamos un resize para que MapLibre re-calibre el canvas
  useEffect(() => {
    if (isMap && !wasVisible.current) {
      // pequeño delay para que el estilo se aplique antes del resize
      const t = setTimeout(() => {
        window.dispatchEvent(new Event("resize"));
      }, 50);
      return () => clearTimeout(t);
    }
    wasVisible.current = !!isMap;
  }, [isMap]);

  return (
    <div
      aria-hidden={!isMap}
      // visibility:hidden hereda a los hijos (incluido el <div fixed> de AisLiveMap),
      // así evitamos interacción/pintado sin desmontar el componente.
      style={{ visibility: isMap ? "visible" : "hidden" }}
    >
      {hasMounted && (
        <Protected>
          {/* Pasamos la vista almacenada (si existe) para restaurar viewport tras remount */}
          <AisLiveMap center={center ?? undefined} zoom={zoom ?? undefined} />
        </Protected>
      )}
    </div>
  );
}
