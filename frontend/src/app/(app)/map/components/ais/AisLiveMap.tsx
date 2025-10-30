"use client";
import { useEffect, useRef, useState } from "react";
import { useMapStore } from "@/app/(app)/map/store/mapStore";
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
import { apiFetch } from "@/lib/api";

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
  // If a persisted view exists in the store, prefer it as the initial viewport.
  const persistedCenter = useMapStore((s) => s.center);
  const persistedZoom = useMapStore((s) => s.zoom);
  if (persistedCenter) center = persistedCenter;
  if (persistedZoom != null) zoom = persistedZoom;
  const mapEl = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MLMap | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  // GeoJSON-based rendering for performance
  type AISProps = { name?: string; sog?: number; cog?: number };
  type AISFeature = Feature<Point, AISProps> & { id: string };
  const featuresRef = useRef<Map<string, AISFeature>>(new Map());

  // --- Persistencia en localStorage ---
  // Cargar barcos guardados al montar
  useEffect(() => {
    try {
      const raw = localStorage.getItem("ais_vessels");
      if (raw) {
        const arr: AISFeature[] = JSON.parse(raw);
        for (const feat of arr) {
          if (feat && feat.id) {
            featuresRef.current.set(feat.id as string, feat);
          }
        }
      }
    } catch {}
  }, []);

  // Guardar barcos en localStorage cada vez que cambian
  useEffect(() => {
    const save = () => {
      try {
        const arr = Array.from(featuresRef.current.values());
        localStorage.setItem("ais_vessels", JSON.stringify(arr));
      } catch {}
    };
    const interval = setInterval(save, 2000);
    return () => clearInterval(interval);
  }, []);
  const sourceReadyRef = useRef(false);
  const flushNeededRef = useRef(false);
  const flushTimerRef = useRef<number | null>(null);
  const lastMsgTsRef = useRef<number>(0);
  const SOURCE_ID = "vessels-source";
  const LAYER_CLUSTERS_ID = "vessels-clusters";
  const LAYER_CLUSTER_COUNT_ID = "vessels-cluster-count";
  const LAYER_UNCLUSTERED_ID = "vessels-unclustered";
  const LAYER_SHIP_SYMBOL_ID = "vessels-ship-symbol";
  const SHIP_IMAGE_ID = "ship-icon";

  // const [connected, setConnected] = useState(false);
  // const [vesselCount, setVesselCount] = useState(0);
  // Only keep setters because we only update these diagnostics; the values are unused
  const setWsState = useState<number | null>(null)[1];
  // const [lastClose, setLastClose] = useState<{
  //   code?: number;
  //   reason?: string;
  // } | null>(null);
  const setLastMsg = useState<string | null>(null)[1];

  const [hydrated, setHydrated] = useState(false);
  const [mounted, setMounted] = useState(false);
  // Capturar el centro/zoom iniciales para usarlos solo en la creación del mapa
  const initialCenterRef = useRef(center);
  const initialZoomRef = useRef(zoom);




  useEffect(() => {
    // mark component as hydrated on client to avoid SSR/CSR mismatches
    setHydrated(true);
    // additionally track mounted to avoid rendering heavy client-only DOM
    // on the first render — this prevents hydration mismatches.
    setMounted(true);
  }, []);

  useEffect(() => {
    // Inicializamos el mapa y los subsistemas SOLO una vez, cuando esté hidratado
    if (!hydrated) return;
    if (!mapEl.current) return;
    // Evitar re-inicializar si ya existe una instancia
    if (mapRef.current) return;
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
        // Usar SOLO los valores iniciales para la creación
        center: initialCenterRef.current,
        zoom: initialZoomRef.current,
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
            // Activamos clustering para escalar cuando hay miles de puntos.
            cluster: true,
            clusterRadius: 60,
            clusterMaxZoom: 12,
          } as unknown as GeoJSONSourceSpecification;
          mapRef.current!.addSource(SOURCE_ID, sourceSpec);
        }

        // Add ship icon image to map
        if (mapRef.current) {
          if (!mapRef.current.hasImage(SHIP_IMAGE_ID)) {
            const img = new window.Image(24, 24);
            img.onload = () => {
              try {
                if (!mapRef.current) return;
                mapRef.current.addImage(SHIP_IMAGE_ID, img, { pixelRatio: 2 });
                // Cluster layer usando icono de barco + contador
                if (!mapRef.current.getLayer(LAYER_CLUSTERS_ID)) {
                  mapRef.current.addLayer({
                    id: LAYER_CLUSTERS_ID,
                    type: "symbol",
                    source: SOURCE_ID,
                    filter: ["has", "point_count"],
                    layout: {
                      "icon-image": SHIP_IMAGE_ID,
                      // Escala combinada por tamaño de cluster y nivel de zoom
                      // Top-level zoom interpolate; outputs incorporate cluster size factor
                      "icon-size": [
                        "interpolate",
                        ["linear"],
                        ["zoom"],
                        0,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 0.9,
                          100, 1.2,
                          500, 1.5
                        ],
                        6,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 1.1,
                          100, 1.4,
                          500, 1.8
                        ],
                        10,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 1.5,
                          100, 1.9,
                          500, 2.4
                        ],
                        14,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 2.0,
                          100, 2.6,
                          500, 3.2
                        ],
                        18,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 2.6,
                          100, 3.4,
                          500, 4.2
                        ]
                      ],
                      "icon-allow-overlap": true,
                      "text-field": ["get", "point_count_abbreviated"],
                      "text-size": [
                        "interpolate",
                        ["linear"],
                        ["zoom"],
                        0, 12,
                        10, 14,
                        14, 18,
                        18, 22
                      ],
                      "text-offset": [0, 0.9],
                      "text-anchor": "top",
                      "text-allow-overlap": true,
                    },
                    paint: {
                      "text-color": "#0f172a",
                      "text-halo-color": "#ffffff",
                      "text-halo-width": 1.2,
                    },
                  });
                }
                // Add SymbolLayer after image is loaded
                if (!mapRef.current.getLayer(LAYER_SHIP_SYMBOL_ID)) {
                  const symbolLayer: SymbolLayerSpecification = {
                    id: LAYER_SHIP_SYMBOL_ID,
                    type: "symbol",
                    source: SOURCE_ID,
                    filter: ["!", ["has", "point_count"]],
                    layout: {
                      "icon-image": SHIP_IMAGE_ID,
                      // Hacer el barco más grande al acercar (zoom)
                      "icon-size": [
                        "interpolate",
                        ["linear"],
                        ["zoom"],
                        0, 1.5,
                        6, 2.0,
                        10, 2.8,
                        14, 3.6,
                        18, 5.0
                      ],
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
            // Cluster layer usando icono de barco + contador
            if (!mapRef.current.getLayer(LAYER_CLUSTERS_ID)) {
              mapRef.current.addLayer({
                id: LAYER_CLUSTERS_ID,
                type: "symbol",
                source: SOURCE_ID,
                filter: ["has", "point_count"],
                layout: {
                  "icon-image": SHIP_IMAGE_ID,
                  // Top-level zoom interpolate; outputs incorporate cluster size factor
                  "icon-size": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    0,
                    [
                      "interpolate",
                      ["linear"],
                      ["get", "point_count"],
                      1, 0.9,
                      100, 1.2,
                      500, 1.5
                    ],
                    6,
                    [
                      "interpolate",
                      ["linear"],
                      ["get", "point_count"],
                      1, 1.1,
                      100, 1.4,
                      500, 1.8
                    ],
                    10,
                    [
                      "interpolate",
                      ["linear"],
                      ["get", "point_count"],
                      1, 1.5,
                      100, 1.9,
                      500, 2.4
                    ],
                    14,
                    [
                      "interpolate",
                      ["linear"],
                      ["get", "point_count"],
                      1, 2.0,
                      100, 2.6,
                      500, 3.2
                    ],
                    18,
                    [
                      "interpolate",
                      ["linear"],
                      ["get", "point_count"],
                      1, 2.6,
                      100, 3.4,
                      500, 4.2
                    ]
                  ],
                  "icon-allow-overlap": true,
                  "text-field": ["get", "point_count_abbreviated"],
                  "text-size": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    0, 10,
                    10, 12,
                    14, 14,
                    18, 18
                  ],
                  "text-offset": [0, 0.9],
                  "text-anchor": "top",
                  "text-allow-overlap": true,
                },
                paint: {
                  "text-color": "#0f172a",
                  "text-halo-color": "#ffffff",
                  "text-halo-width": 1.2,
                },
              });
            }
            if (!mapRef.current.getLayer(LAYER_SHIP_SYMBOL_ID)) {
              const symbolLayer: SymbolLayerSpecification = {
                id: LAYER_SHIP_SYMBOL_ID,
                type: "symbol",
                source: SOURCE_ID,
                filter: ["!", ["has", "point_count"]],
                layout: {
                  "icon-image": SHIP_IMAGE_ID,
                  "icon-size": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    0, 1.0,
                    6, 1.3,
                    10, 1.8,
                    14, 2.4,
                    18, 3.2
                  ],
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

        // Restore map view if persisted (extra safety after load)
        try {
          if (mapRef.current) {
            const storeCenter = useMapStore.getState().center;
            const storeZoom = useMapStore.getState().zoom;
            if (storeCenter) {
              mapRef.current.setCenter(storeCenter as [number, number]);
            }
            if (storeZoom != null) {
              mapRef.current.setZoom(storeZoom as number);
            }
          }
        } catch {}

        // Keep the stored viewport in sync when the user moves/zooms the map
        if (mapRef.current) {
          const onMoveEnd = () => {
            try {
              const c = mapRef.current!.getCenter();
              const z = mapRef.current!.getZoom();
              useMapStore.getState().setView([c.lng, c.lat], z);
            } catch {}
          };
          mapRef.current.on("moveend", onMoveEnd);
          // remove listener on source teardown
          const originalTear = teardown;
          teardown = () => {
            try {
              mapRef.current?.off("moveend", onMoveEnd);
            } catch {}
            originalTear?.();
          };
        }
        // Carga inicial paginada por REST en el área visible
        void (async () => {
          try {
            const m = mapRef.current;
            if (!m) return;
            const b = m.getBounds();
            const west = b.getWest();
            const south = b.getSouth();
            const east = b.getEast();
            const north = b.getNorth();

            // Limitar la cantidad inicial para no bloquear el main thread
            const PAGE_SIZE = 1000;
            const MAX_ITEMS = 5000; // tope inicial
            let page = 1;
            let received = 0;
            // Bucle de páginas hasta llenar tope o quedarnos sin datos
            while (received < MAX_ITEMS) {
              const res = await apiFetch<{
                total: number;
                page: number;
                page_size: number;
                items: Array<{ id: string | number; lat: number; lon: number }>;
              }>(
                `/aisstream/positions?page=${page}&page_size=${PAGE_SIZE}` +
                  `&west=${west}&south=${south}&east=${east}&north=${north}`
              );
              const list = res?.items ?? [];
              if (!Array.isArray(list) || list.length === 0) break;
              for (const it of list) {
                if (
                  typeof it?.lon !== "number" ||
                  !Number.isFinite(it.lon) ||
                  typeof it?.lat !== "number" ||
                  !Number.isFinite(it.lat)
                )
                  continue;
                upsertFeature({
                  mmsi: String(it.id),
                  lon: it.lon,
                  lat: it.lat,
                });
              }
              received += list.length;
              page += 1;
              // Ceder al event loop para mantener la UI fluida
              await new Promise((r) => setTimeout(r, 0));
              // Si el mapa cambió de bounds mientras cargábamos, detenemos la precarga
              const nb = m.getBounds();
              if (
                nb.getWest() !== west ||
                nb.getSouth() !== south ||
                nb.getEast() !== east ||
                nb.getNorth() !== north
              ) {
                break;
              }
            }
            flushNeededRef.current = true;
          } catch (e) {
            console.debug("[AIS] initial REST load failed", e);
          }
        })();

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
          // Culling por viewport + muestreo estable para limitar draw calls
          const m = mapRef.current;
          const b = m.getBounds();
          const west = b.getWest();
          const south = b.getSouth();
          const east = b.getEast();
          const north = b.getNorth();
          const crossesAntimeridian = west > east;
          const MAX_RENDERED = 8000; // tope para mantener fluidez

          const all = Array.from(featuresRef.current.values());
          const visible = all.filter((f) => {
            const [lon, lat] = f.geometry.coordinates as [number, number];
            const inLat = lat >= south && lat <= north;
            const inLon = crossesAntimeridian
              ? lon >= west || lon <= east
              : lon >= west && lon <= east;
            return inLat && inLon;
          });
          let features: typeof visible = visible;
          if (features.length > MAX_RENDERED) {
            const stride = Math.ceil(features.length / MAX_RENDERED);
            // Muestreo estable por id para evitar parpadeos
            const stableHash = (s: string) => {
              let h = 2166136261 >>> 0;
              for (let i = 0; i < s.length; i++) {
                h ^= s.charCodeAt(i);
                h = Math.imul(h, 16777619);
              }
              return h >>> 0;
            };
            features = features.filter((f) => stableHash(String(f.id)) % stride === 0);
          }
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
          }
        }, 400);
      };
      startFlush();
  // Manual refresh handler

      // Debounced refresh on viewport changes: fetch first page for current bounds
      let refreshTimer: number | null = null;
      const requestViewportPage = async () => {
        try {
          const m = mapRef.current;
          if (!m) return;
          const b = m.getBounds();
          const res = await apiFetch<{
            items: Array<{ id: string | number; lat: number; lon: number }>;
          }>(
            `/aisstream/positions?page=1&page_size=1000` +
              `&west=${b.getWest()}&south=${b.getSouth()}&east=${b.getEast()}&north=${b.getNorth()}`
          );
          const list = res?.items ?? [];
          for (const it of list) {
            if (
              typeof it?.lon !== "number" ||
              !Number.isFinite(it.lon) ||
              typeof it?.lat !== "number" ||
              !Number.isFinite(it.lat)
            )
              continue;
            upsertFeature({ mmsi: String(it.id), lon: it.lon, lat: it.lat });
          }
          flushNeededRef.current = true;
        } catch (e) {
          console.debug("[AIS] viewport REST load failed", e);
        }
      };
      const scheduleViewportRefresh = () => {
        if (refreshTimer != null) window.clearTimeout(refreshTimer);
        refreshTimer = window.setTimeout(() => {
          refreshTimer = null;
          void requestViewportPage();
        }, 800);
      };
      mapRef.current?.on("moveend", scheduleViewportRefresh);



      // Solo conectar a backend vía Socket.IO
      let socket: Socket | null = null;
      try {
        const { io } = await import("socket.io-client");
        const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? window.location.origin;
        const forcePolling = process.env.NEXT_PUBLIC_FORCE_POLLING === "true";
        // Debug: log where the client will attempt to connect. Helpful to confirm rewrites/env.
        try {
          console.debug("[AIS] socket baseUrl:", baseUrl, "forcePolling:", forcePolling, "env NEXT_PUBLIC_BACKEND_URL:", process.env.NEXT_PUBLIC_BACKEND_URL);
        } catch {}
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
            lon: number | null | undefined;
            lat: number | null | undefined;
            cog?: number;
            sog?: number;
            name?: string;
          }) => {
            if (typeof pos.lon !== "number" || !Number.isFinite(pos.lon)) return;
            if (typeof pos.lat !== "number" || !Number.isFinite(pos.lat)) return;
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
              lon: number | null | undefined;
              lat: number | null | undefined;
              cog?: number;
              sog?: number;
              name?: string;
            }>;
          }) => {
            // Solo agregar/actualizar barcos, nunca borrar
            const list = payload?.positions ?? [];
            for (const p of list) {
              if (typeof p.lon !== "number" || !Number.isFinite(p.lon)) continue;
              if (typeof p.lat !== "number" || !Number.isFinite(p.lat)) continue;
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
        const nextProps: AISProps = {
          name: v.name,
          sog: Number.isFinite(v.sog ?? NaN) ? v.sog : undefined,
          // MapLibre espera un número en icon-rotate; si falta, usa 0 para evitar errores.
          cog: Number.isFinite(v.cog ?? NaN) ? (v.cog as number) : 0,
        };
        const existing = featuresRef.current.get(id);
        if (existing) {
          existing.geometry.coordinates = [v.lon, v.lat];
          existing.properties = nextProps;
        } else {
          const feat: AISFeature = {
            type: "Feature",
            id,
            properties: nextProps,
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
    if (refreshTimer != null) window.clearTimeout(refreshTimer);
  // featuresRef.current.clear(); // Nunca limpiar los barcos para que nunca desaparezcan
      };

      teardown = cleanup;
      if (cancelled) cleanup();
    })();

    return () => {
      cancelled = true;
      teardown?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated]);

  // Efecto separado para ACTUALIZAR la vista sin recrear el mapa
  useEffect(() => {
    const m = mapRef.current;
    if (!m) return;
    // Solo cuando hay valores válidos
    if (center && Array.isArray(center) && center.length === 2) {
      const cur = m.getCenter();
      const dx = Math.abs(cur.lng - center[0]);
      const dy = Math.abs(cur.lat - center[1]);
      if (dx > 1e-6 || dy > 1e-6) {
        m.jumpTo({ center: center as [number, number] });
      }
    }
    if (typeof zoom === "number") {
      const curZ = m.getZoom();
      if (Math.abs(curZ - zoom) > 1e-6) {
        m.setZoom(zoom);
      }
    }
  }, [center, zoom]);

  if (!mounted) {
    // Render a lightweight placeholder on server / initial client render.
    return <div className="w-full h-[60vh] bg-slate-50" aria-hidden />;
  }

  return (
    <div className="fixed inset-0 z-0">
      <div ref={mapEl} className="w-full h-full">
      </div>
    </div>
  );
}
