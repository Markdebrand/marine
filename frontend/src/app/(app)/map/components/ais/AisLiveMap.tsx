"use client";
import { useEffect, useRef, useState } from "react";
import type {
  Map as MLMap,
  GeoJSONSource,
  MapGeoJSONFeature,
  SymbolLayerSpecification,
  GeoJSONSourceSpecification,
  StyleSpecification,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Feature, FeatureCollection, Point } from "geojson";
import type { Socket } from "socket.io-client";

type Vessel = {
  mmsi: string;
  lon: number;
  lat: number;
  cog?: number; // course over ground in degrees
  sog?: number; // speed over ground
  name?: string;
};

type Props = {
  center?: [number, number];
  zoom?: number;
};

export default function AisLiveMap({
  center = [-3.7038, 40.4168],
  zoom = 3,
}: Props) {
  const mapEl = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MLMap | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  // GeoJSON-based rendering for performance
  type AISProps = { name?: string; sog?: number; cog?: number };
  type AISFeature = Feature<Point, AISProps> & { id: string };
  const featuresRef = useRef<Map<string, AISFeature>>(new Map());
  const sourceReadyRef = useRef(false);
  const flushNeededRef = useRef(false);
  // const flushTimerRef = useRef<number | null>(null);
  const lastMsgTsRef = useRef<number>(0);
  const SOURCE_ID = "vessels-source";
  const LAYER_CLUSTERS_ID = "vessels-clusters";
  const LAYER_CLUSTER_COUNT_ID = "vessels-cluster-count";
  const LAYER_UNCLUSTERED_ID = "vessels-unclustered";
  const LAYER_SHIP_SYMBOL_ID = "vessels-ship-symbol";
  const SHIP_IMAGE_ID = "ship-icon";

  // const [connected, setConnected] = useState(false);
  // const [vesselCount, setVesselCount] = useState(0);
  const [wsState, setWsState] = useState<number | null>(null);
  // const [lastClose, setLastClose] = useState<{
  //   code?: number;
  //   reason?: string;
  // } | null>(null);
  const [lastMsg, setLastMsg] = useState<string | null>(null);

  const [hydrated, setHydrated] = useState(false);
  const [mounted, setMounted] = useState(false);


  // Manual refresh handler (must be outside useEffect)
  async function handleRefresh() {
    if (!sourceReadyRef.current || !mapRef.current) return;
    try {
      // Fetch latest vessels from backend
      const res = await fetch("/api/ais/positions");
      if (!res.ok) throw new Error("No se pudo obtener barcos");
      const data = await res.json();
      // Espera un array de objetos tipo { id, lon, lat, cog, sog, name }
      featuresRef.current.clear();
      for (const v of data) {
        if (!Number.isFinite(v.lon) || !Number.isFinite(v.lat)) continue;
        const id = String(v.id);
        const feat: AISFeature = {
          type: "Feature",
          id,
          properties: { name: v.name, sog: v.sog, cog: v.cog },
          geometry: { type: "Point", coordinates: [v.lon, v.lat] },
        };
        featuresRef.current.set(id, feat);
      }
      // Actualiza el mapa
      const features = Array.from(featuresRef.current.values());
      const fc: FeatureCollection<Point, AISProps> = {
        type: "FeatureCollection",
        features,
      };
      const src = mapRef.current.getSource(SOURCE_ID) as GeoJSONSource | undefined;
      if (src) {
        src.setData(fc);
        flushNeededRef.current = false;
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : typeof err === "string"
          ? err
          : "Unknown error";
      alert("Error al refrescar barcos: " + message);
    }
  }

  useEffect(() => {
    // mark component as hydrated on client to avoid SSR/CSR mismatches
    setHydrated(true);
    // additionally track mounted to avoid rendering heavy client-only DOM
    // on the first render — this prevents hydration mismatches.
    setMounted(true);
  }, []);

  useEffect(() => {
    // Don't run map/ws setup until component has hydrated on client
    if (!hydrated) return;
    if (!mapEl.current) return;
    let cancelled = false;
    let teardown: (() => void) | undefined;

    (async () => {
      const maplibregl = (await import("maplibre-gl")).default;
      // Basic raster OSM style
      const style: StyleSpecification = {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      };

      const map = new maplibregl.Map({
        container: mapEl.current!,
        style,
        center,
        zoom,
        attributionControl: false,
      });
      mapRef.current = map;

      // Setup GeoJSON source/layers once map is loaded
      const onLoad = () => {
        if (!mapRef.current?.getSource(SOURCE_ID)) {
          const sourceSpec = {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: [],
            } as FeatureCollection<Point, AISProps>,
            promoteId: "id",
            cluster: false, // Desactivado para que los iconos no desaparezcan
            // clusterRadius: 50,
            // clusterMaxZoom: 12,
          } as unknown as GeoJSONSourceSpecification;
          mapRef.current!.addSource(SOURCE_ID, sourceSpec);
        }

        // Add ship icon image to map
        if (mapRef.current) {
          if (!mapRef.current.hasImage(SHIP_IMAGE_ID)) {
            const img = new window.Image(32, 32);
            img.onload = () => {
              try {
                if (!mapRef.current) return;
                mapRef.current.addImage(SHIP_IMAGE_ID, img, { pixelRatio: 2 });
                // Add SymbolLayer after image is loaded
                if (!mapRef.current.getLayer(LAYER_SHIP_SYMBOL_ID)) {
                  const symbolLayer: SymbolLayerSpecification = {
                    id: LAYER_SHIP_SYMBOL_ID,
                    type: "symbol",
                    source: SOURCE_ID,
                    filter: ["!", ["has", "point_count"]],
                    layout: {
                      "icon-image": SHIP_IMAGE_ID,
                      "icon-size": 1,
                      "icon-allow-overlap": true,
                      "icon-rotate": ["get", "cog"],
                    },
                    paint: {},
                  };
                  mapRef.current.addLayer(symbolLayer);
                }
              } catch {}
            };
            img.src = "/images/ship.svg";
          } else {
            // Add SymbolLayer if image already loaded
            if (!mapRef.current.getLayer(LAYER_SHIP_SYMBOL_ID)) {
              const symbolLayer: SymbolLayerSpecification = {
                id: LAYER_SHIP_SYMBOL_ID,
                type: "symbol",
                source: SOURCE_ID,
                filter: ["!", ["has", "point_count"]],
                layout: {
                  "icon-image": SHIP_IMAGE_ID,
                  "icon-size": 1,
                  "icon-allow-overlap": true,
                  "icon-rotate": ["get", "cog"],
                },
                paint: {},
              };
              mapRef.current.addLayer(symbolLayer);
            }
          }
        }
        sourceReadyRef.current = true;

        // Zoom into clusters on click
        const m = mapRef.current!;
        m.on("click", LAYER_CLUSTERS_ID, (e) => {
          const features = (m.queryRenderedFeatures(e.point, {
            layers: [LAYER_CLUSTERS_ID],
          }) ?? []) as MapGeoJSONFeature[];
          const props = features[0]?.properties as
            | Record<string, unknown>
            | undefined;
          const clusterId =
            typeof props?.cluster_id === "number"
              ? (props.cluster_id as number)
              : undefined;
          const src = m.getSource(SOURCE_ID) as unknown as
            | {
                getClusterExpansionZoom: (
                  clusterId: number,
                  cb: (err?: unknown, zoom?: number) => void
                ) => void;
              }
            | undefined;
          if (src && clusterId != null) {
            src.getClusterExpansionZoom(clusterId, (_err, zoomTo) => {
              if (zoomTo == null) return;
              const geom = features[0]?.geometry as Point | undefined;
              if (geom?.type !== "Point") return;
              const [lng, lat] = geom.coordinates as [number, number];
              m.easeTo({ center: [lng, lat], zoom: Math.min(zoomTo, 18) });
            });
          }
        });
        m.on("mouseenter", LAYER_CLUSTERS_ID, () => {
          if (mapRef.current) {
            const canvas = mapRef.current.getCanvas();
            canvas.style.cursor = "pointer";
          }
        });
        m.on("mouseleave", LAYER_CLUSTERS_ID, () => {
          if (mapRef.current) {
            const canvas = mapRef.current.getCanvas();
            canvas.style.cursor = "";
          }
        });
      };
      if (mapRef.current?.loaded()) onLoad();
      else mapRef.current?.once("load", onLoad);

      // No auto flush, handled by refresh button
  // Manual refresh handler



      // Solo conectar a backend vía Socket.IO
      let socket: Socket | null = null;
      try {
        const { io } = await import("socket.io-client");
        const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? window.location.origin;
        const forcePolling = process.env.NEXT_PUBLIC_FORCE_POLLING === "true";
        socket = io(baseUrl, {
          path: "/socket.io",
          transports: forcePolling ? ["polling"] : ["polling", "websocket"],
          upgrade: !forcePolling,
        });
        socket.on("connect", () => {
          setWsState(1);
          console.debug("[AIS] Conectado a Socket.IO backend", socket?.id);
        });
        socket.on("ais_raw", (data: unknown) => {
          try {
            const now = Date.now();
            if (now - lastMsgTsRef.current > 1000) {
              setLastMsg(JSON.stringify(data).slice(0, 800));
              lastMsgTsRef.current = now;
            }
          } catch {}
        });
        socket.on(
          "ais_position",
          (pos: {
            id: string | number;
            lon: number;
            lat: number;
            cog?: number;
            sog?: number;
            name?: string;
          }) => {
            upsertFeature({
              mmsi: String(pos.id),
              lon: pos.lon,
              lat: pos.lat,
              cog: pos.cog,
              sog: pos.sog,
              name: pos.name,
            });
          }
        );
        socket.on(
          "ais_position_batch",
          (payload: {
            positions?: Array<{
              id: string | number;
              lon: number;
              lat: number;
              cog?: number;
              sog?: number;
              name?: string;
            }>;
          }) => {
            // Solo agregar/actualizar barcos, nunca borrar
            const list = payload?.positions ?? [];
            for (const p of list) {
              upsertFeature({
                mmsi: String(p.id),
                lon: p.lon,
                lat: p.lat,
                cog: p.cog,
                sog: p.sog,
                name: p.name,
              });
            }
            // Forzar flush para que el GeoJSON siempre incluya TODOS los barcos vistos
            flushNeededRef.current = true;
          }
        );
        socket.on("connect_error", (err: unknown) => {
          setWsState(0);
          console.debug("[AIS] Socket.IO connect_error", err);
        });
      } catch {
        setWsState(0);
        console.debug("[AIS] socket.io-client not available");
      }

      function upsertFeature(v: Vessel) {
        if (!Number.isFinite(v.lon) || !Number.isFinite(v.lat)) return;
        const id = v.mmsi;
        const existing = featuresRef.current.get(id);
        if (existing) {
          existing.geometry.coordinates = [v.lon, v.lat];
          existing.properties = {
            ...(existing.properties || {}),
            name: v.name,
            sog: v.sog,
            cog: v.cog,
          } as AISProps;
        } else {
          const feat: AISFeature = {
            type: "Feature",
            id,
            properties: { name: v.name, sog: v.sog, cog: v.cog },
            geometry: { type: "Point", coordinates: [v.lon, v.lat] },
          };
          featuresRef.current.set(id, feat);
        }
        flushNeededRef.current = true;
      }

      // Clean up
      const cleanup = () => {
        // Close socket if present
        try {
          (socket as Socket | null)?.close?.();
        } catch {}
        // Close direct WS
        wsRef.current?.close();
        wsRef.current = null;
        // Remove layers before removing source
        try {
          if (mapRef.current?.getLayer(LAYER_SHIP_SYMBOL_ID))
            mapRef.current.removeLayer(LAYER_SHIP_SYMBOL_ID);
          if (mapRef.current?.getLayer(LAYER_CLUSTER_COUNT_ID))
            mapRef.current.removeLayer(LAYER_CLUSTER_COUNT_ID);
          if (mapRef.current?.getLayer(LAYER_CLUSTERS_ID))
            mapRef.current.removeLayer(LAYER_CLUSTERS_ID);
          if (mapRef.current?.getLayer(LAYER_UNCLUSTERED_ID))
            mapRef.current.removeLayer(LAYER_UNCLUSTERED_ID);
          if (mapRef.current?.getSource(SOURCE_ID))
            mapRef.current.removeSource(SOURCE_ID);
        } catch {}
        mapRef.current?.remove();
        mapRef.current = null;
  // featuresRef.current.clear(); // Nunca limpiar los barcos para que nunca desaparezcan
      };

      teardown = cleanup;
      if (cancelled) cleanup();
    })();

    return () => {
      cancelled = true;
      teardown?.();
    };
  }, [center, zoom, hydrated]);

  if (!mounted) {
    // Render a lightweight placeholder on server / initial client render.
    return <div className="w-full h-[60vh] bg-slate-50" aria-hidden />;
  }

  return (
    <div className="fixed inset-0 z-0">
      <div ref={mapEl} className="w-full h-full">
        {/* Botón de refresh */}
        <button
          onClick={handleRefresh}
          className="absolute top-20 left-4 z-50 bg-white/80 hover:bg-white text-red-600 font-bold py-2 px-4 rounded shadow border border-red-200"
        >
          Refresh barcos
        </button>
        {/* Diagnostics panel */}
        <div className="absolute top-24 right-4 z-50 w-80 text-xs">
          <div className="glass-card p-3 rounded-md border border-white/30 shadow-[0_10px_30px_rgba(2,6,23,0.06)] backdrop-blur-md">
            <div className="font-medium text-slate-900">Diagnosis AIS</div>
            <div className="text-slate-600">State WS: {wsState ?? "—"}</div>
            <div className="mt-2 text-slate-700 break-words">
              <strong>Last Message:</strong>
              <pre
                className="max-h-32 overflow-auto text-xs p-1"
                style={{ whiteSpace: "pre-wrap" }}
              >
                {lastMsg ?? "—"}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
