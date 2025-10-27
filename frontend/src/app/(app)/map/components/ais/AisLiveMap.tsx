"use client";
import { useEffect, useRef, useState } from "react";
import type {
  Map as MLMap,
  GeoJSONSource,
  MapGeoJSONFeature,
  CircleLayerSpecification,
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
  token: string; // aisstream API key
  center?: [number, number];
  zoom?: number;
};

export default function AisLiveMap({
  token,
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
  const flushTimerRef = useRef<number | null>(null);
  const lastMsgTsRef = useRef<number>(0);
  const SOURCE_ID = "vessels-source";
  const LAYER_CLUSTERS_ID = "vessels-clusters";
  const LAYER_CLUSTER_COUNT_ID = "vessels-cluster-count";
  const LAYER_UNCLUSTERED_ID = "vessels-unclustered";

  const [connected, setConnected] = useState(false);
  const [vesselCount, setVesselCount] = useState(0);
  const [wsState, setWsState] = useState<number | null>(null);
  const [lastClose, setLastClose] = useState<{
    code?: number;
    reason?: string;
  } | null>(null);
  const [lastMsg, setLastMsg] = useState<string | null>(null);

  const [hydrated, setHydrated] = useState(false);
  const [mounted, setMounted] = useState(false);

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
    if (!token) {
      console.warn(
        "[AIS] NEXT_PUBLIC_AISSTREAM_KEY no está definido. El mapa se renderizará sin datos en vivo."
      );
    }
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
            cluster: true,
            clusterRadius: 50,
            clusterMaxZoom: 12,
          } as unknown as GeoJSONSourceSpecification;
          mapRef.current!.addSource(SOURCE_ID, sourceSpec);
        }
        // Clusters layer
        if (!mapRef.current?.getLayer(LAYER_CLUSTERS_ID)) {
          const clustersLayer: CircleLayerSpecification = {
            id: LAYER_CLUSTERS_ID,
            type: "circle",
            source: SOURCE_ID,
            filter: ["has", "point_count"],
            paint: {
              "circle-color": [
                "step",
                ["get", "point_count"],
                "#9ca3af",
                50,
                "#60a5fa",
                200,
                "#ef4444",
              ],
              "circle-radius": [
                "step",
                ["get", "point_count"],
                12,
                50,
                16,
                200,
                22,
              ],
              "circle-opacity": 0.85,
              "circle-stroke-color": "#ffffff",
              "circle-stroke-width": 2,
            },
          };
          mapRef.current!.addLayer(clustersLayer);
        }
        // Cluster count symbols
        if (!mapRef.current?.getLayer(LAYER_CLUSTER_COUNT_ID)) {
          const clusterCountLayer: SymbolLayerSpecification = {
            id: LAYER_CLUSTER_COUNT_ID,
            type: "symbol",
            source: SOURCE_ID,
            filter: ["has", "point_count"],
            layout: {
              "text-field": ["get", "point_count_abbreviated"],
              "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
              "text-size": 12,
            },
            paint: {
              "text-color": "#111827",
            },
          };
          mapRef.current!.addLayer(clusterCountLayer);
        }
        // Unclustered points
        if (!mapRef.current?.getLayer(LAYER_UNCLUSTERED_ID)) {
          const unclusteredLayer: CircleLayerSpecification = {
            id: LAYER_UNCLUSTERED_ID,
            type: "circle",
            source: SOURCE_ID,
            filter: ["!", ["has", "point_count"]],
            paint: {
              "circle-radius": 5,
              "circle-color": "#ef4444",
              "circle-stroke-color": "#ffffff",
              "circle-stroke-width": 2,
              "circle-opacity": 0.9,
            },
          };
          mapRef.current!.addLayer(unclusteredLayer);
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

      // Throttled flush to update source data in batches
      const startFlush = () => {
        if (flushTimerRef.current != null) return;
        flushTimerRef.current = window.setInterval(() => {
          if (
            !flushNeededRef.current ||
            !sourceReadyRef.current ||
            !mapRef.current
          )
            return;
          const features = Array.from(featuresRef.current.values());
          const fc: FeatureCollection<Point, AISProps> = {
            type: "FeatureCollection",
            features,
          };
          const src = mapRef.current.getSource(SOURCE_ID) as
            | GeoJSONSource
            | undefined;
          if (src) {
            src.setData(fc);
            flushNeededRef.current = false;
            setVesselCount(featuresRef.current.size);
          }
        }, 250);
      };
      startFlush();

      // Prefer connecting to backend Socket.IO at /socket.io (bridge). If unavailable, fallback to AISStream WS.
      let socket: Socket | null = null;
      let socketConnected = false;
      let fallbackTimer: number | null = null;
      const disableWsFallback =
        process.env.NEXT_PUBLIC_DISABLE_AIS_WS_FALLBACK === "true" ||
        process.env.NEXT_PUBLIC_FORCE_POLLING === "true";

      try {
        const { io } = await import("socket.io-client");
        // Prefer explicit backend URL in dev to avoid 404 from Next dev server
        const baseUrl =
          process.env.NEXT_PUBLIC_BACKEND_URL ?? window.location.origin;
        const forcePolling =
          process.env.NEXT_PUBLIC_FORCE_POLLING === "true";
        // Prefer starting with polling, then upgrade to websocket unless forced polling-only
        socket = io(baseUrl, {
          path: "/socket.io",
          transports: forcePolling ? ["polling"] : ["polling", "websocket"],
          upgrade: !forcePolling,
        });
        // Handle connect
        socket.on("connect", () => {
          socketConnected = true;
          if (fallbackTimer != null) window.clearTimeout(fallbackTimer);
          setConnected(true);
          setWsState(1);
          console.debug("[AIS] Conectado a Socket.IO backend", socket?.id);
        });
        // Diagnostics raw messages
        socket.on("ais_raw", (data: unknown) => {
          try {
            const now = Date.now();
            if (now - lastMsgTsRef.current > 1000) {
              setLastMsg(JSON.stringify(data).slice(0, 800));
              lastMsgTsRef.current = now;
            }
          } catch {
            /* ignore */
          }
        });
        // Position single
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
        // Batch of positions
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
          }
        );
        // Fallback quickly if connection cannot be established
        socket.on("connect_error", (err: unknown) => {
          console.debug(
            "[AIS] Socket.IO connect_error, fallback to direct WS",
            err
          );
        });
        // Set a short timer to fallback if not connected promptly (optional)
        if (!disableWsFallback) {
          fallbackTimer = window.setTimeout(() => {
            if (!socketConnected) {
              openDirectWebSocket();
            }
          }, 1500);
        }
      } catch {
        // dynamic import failed or socket.io-client missing; fall back to WS
        console.debug(
          "[AIS] socket.io-client not available, using direct WebSocket"
        );
        openDirectWebSocket();
      }

      function openDirectWebSocket() {
        if (disableWsFallback) {
          console.debug(
            "[AIS] Fallback WS deshabilitado por NEXT_PUBLIC_DISABLE_AIS_WS_FALLBACK"
          );
          return;
        }
        // Evitar abrir WS si no hay token; de lo contrario el servidor cerrará con error
        if (!token) {
          console.warn(
            "[AIS] No hay NEXT_PUBLIC_AISSTREAM_KEY, omitiendo conexión WebSocket directa"
          );
          return;
        }
        if (
          wsRef.current &&
          (wsRef.current.readyState === WebSocket.OPEN ||
            wsRef.current.readyState === WebSocket.CONNECTING)
        )
          return;
        const ws = new WebSocket("wss://stream.aisstream.io/v0/stream");
        wsRef.current = ws;
        ws.addEventListener("open", () => {
          setConnected(true);
          const sub = {
            Apikey: token,
            BoundingBoxes: [
              [
                [-180, -85],
                [180, 85],
              ],
            ],
          };
          const masked = token ? token.replace(/.(?=.{4})/g, "*") : "";
          console.debug(`[AIS] Suscripción WS abierta (token: ${masked})`);
          ws.send(JSON.stringify(sub));
        });

        ws.addEventListener("close", (ev) => {
          setConnected(false);
          setLastClose({
            code: (ev as CloseEvent).code,
            reason: (ev as CloseEvent).reason,
          });
          setWsState(ws.readyState);
          console.debug(
            "[AIS] WebSocket cerrado",
            (ev as CloseEvent).code,
            (ev as CloseEvent).reason
          );
        });

        ws.addEventListener("error", (err) => {
          setConnected(false);
          setWsState(ws.readyState);
          console.debug(
            "[AIS] WebSocket error (posible token ausente o rechazo de servidor)",
            err
          );
          try {
            ws.close();
          } catch {}
        });

        ws.addEventListener("message", (ev) => {
          const raw = typeof ev.data === "string" ? ev.data : "";
          const now = Date.now();
          if (now - lastMsgTsRef.current > 1000) {
            setLastMsg(raw.slice(0, 800));
            lastMsgTsRef.current = now;
          }
          setWsState(ws.readyState);
          try {
            const data = JSON.parse(ev.data as string);
            const msgType = data?.MessageType;
            if (msgType === "PositionReport") {
              const v: Vessel = {
                mmsi: String(data?.MMSI ?? ""),
                lon: Number(data?.Position?.lon),
                lat: Number(data?.Position?.lat),
                cog: data?.COG ? Number(data.COG) : undefined,
                sog: data?.SOG ? Number(data.SOG) : undefined,
                name: data?.Name ? String(data.Name) : undefined,
              };
              if (Number.isFinite(v.lon) && Number.isFinite(v.lat))
                upsertFeature(v);
            }
          } catch {
            /* ignore */
          }
        });
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
        if (fallbackTimer != null) {
          window.clearTimeout(fallbackTimer);
          fallbackTimer = null;
        }
        if (flushTimerRef.current != null) {
          window.clearInterval(flushTimerRef.current);
          flushTimerRef.current = null;
        }
        try {
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
        featuresRef.current.clear();
        setConnected(false);
        setVesselCount(0);
      };

      teardown = cleanup;
      if (cancelled) cleanup();
    })();

    return () => {
      cancelled = true;
      teardown?.();
    };
  }, [token, center, zoom, hydrated]);

  if (!mounted) {
    // Render a lightweight placeholder on server / initial client render.
    return <div className="w-full h-[60vh] bg-slate-50" aria-hidden />;
  }

  return (
    <div className="fixed inset-0 z-0">
      <div ref={mapEl} className="w-full h-full">
        {/* Diagnostics panel */}
        <div className="absolute top-24 right-4 z-50 w-80 text-xs">
          <div className="glass-card p-3 rounded-md border border-white/30 shadow-[0_10px_30px_rgba(2,6,23,0.06)] backdrop-blur-md">
            <div className="font-medium text-slate-900">Diagnosis AIS</div>
            <div className="text-slate-600">State WS: {wsState ?? "—"}</div>
            <div className="text-slate-600">
              Last Close:{" "}
              {lastClose
                ? `${lastClose.code ?? "—"} ${lastClose.reason ?? ""}`
                : "—"}
            </div>
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
