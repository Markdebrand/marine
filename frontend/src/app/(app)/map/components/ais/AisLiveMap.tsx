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
import { apiFetch } from "@/lib/api";

type Vessel = {
  mmsi: string;
  lon: number;
  lat: number;
  cog?: number;
  sog?: number;
  name?: string;
};

type VesselDetails = {
  mmsi: string;
  data: {
    ship_name: string;
    imo_number: number;
    call_sign: string;
    ship_type: string;
    dimensions: {
      a: number;
      b: number;
      c: number;
      d: number;
      length: number;
      width: number;
    };
    fix_type: number;
    eta: string;
    draught: number;
    destination: string;
    timestamp: string;
    latitude?: number;  // 🆕 Added for routing
    longitude?: number; // 🆕 Added for routing
  };
  status: string;
};

type Port = {
  port_number: number;
  lat: number | null;  // ycoord from backend
  lon: number | null;  // xcoord from backend
};

type PortListResponse = {
  ports: Port[];
};

type PortDetails = Record<string, any>;  // Dynamic port details from backend

// 🆕 Tipo para el error de barco no disponible
type VesselError = {
  mmsi: string;
  message: string;
  type: 'not_found' | 'timeout' | 'error';
};

type Props = {
  center?: [number, number];
  zoom?: number;
};

export default function AisLiveMap({
  center = [-3.7038, 40.4168],
  zoom = 3,
}: Props) {
  const persistedCenter = useMapStore((s) => s.center);
  const persistedZoom = useMapStore((s) => s.zoom);
  if (persistedCenter) center = persistedCenter;
  if (persistedZoom != null) zoom = persistedZoom;
  const mapEl = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MLMap | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  
  type AISProps = { 
    mmsi?: string;
    name?: string; 
    sog?: number; 
    cog?: number 
  };
  type AISFeature = Feature<Point, AISProps> & { id: string };
  const featuresRef = useRef<Map<string, AISFeature>>(new Map());

  const [selectedVessel, setSelectedVessel] = useState<VesselDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const vesselDetailsCache = useRef(new Map<string, VesselDetails>());
  
  // 🆕 Estado para manejar errores de barcos
  const [vesselError, setVesselError] = useState<VesselError | null>(null);

  // 🆕 Helper para formatear fechas de manera consistente (M/D/YYYY, 12h)
  const formatDate = (dateValue: string | number | Date | null | undefined) => {
    if (!dateValue || dateValue === "N/A") return "N/A";
    try {
      const d = new Date(dateValue);
      if (isNaN(d.getTime())) return String(dateValue);
      return d.toLocaleString("en-US");
    } catch {
      return String(dateValue);
    }
  };

  
  // 🆕 Estado para puertos
  const [selectedPort, setSelectedPort] = useState<PortDetails | null>(null);
  const [loadingPortDetails, setLoadingPortDetails] = useState(false);
  
  // 🆕 Route state & ref to prevent stale closures in background loops
  const [routeData, setRouteData] = useState<Feature<any> | null>(null);
  const routeDataRef = useRef<Feature<any> | null>(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  
  // Keep ref in sync with state
  useEffect(() => {
    routeDataRef.current = routeData;
  }, [routeData]);

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
  const PORTS_SOURCE_ID = "ports-source";
  const PORTS_LAYER_ID = "ports-layer";
  const PORT_IMAGE_ID = "port-icon";
  const ROUTE_SOURCE_ID = "route-source";
  const ROUTE_LAYER_ID = "route-layer";

  const [connected, setConnected] = useState(false);
  const [vesselCount, setVesselCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [loadingVesselCount, setLoadingVesselCount] = useState(false);

  const [hydrated, setHydrated] = useState(false);
  const [mounted, setMounted] = useState(false);
  const initialCenterRef = useRef(center);
  const initialZoomRef = useRef(zoom);
  const [portsLoaded, setPortsLoaded] = useState(false);

  const fetchTotalVessels = async () => {
    setLoadingVesselCount(true);
    try {
      const response = await apiFetch<{
        total: number;
        page: number;
        page_size: number;
        items: Array<{ id: string; lat: number; lon: number }>;
      }>("/aisstream/positions?page_size=1");
      
      setVesselCount(response.total);
      setLastUpdate(new Date().toLocaleTimeString());
      console.debug(`[AIS] Total de barcos actualizado: ${response.total}`);
    } catch (error) {
      console.error("[AIS] Error al obtener el total de barcos:", error);
    } finally {
      setLoadingVesselCount(false);
    }
  };

  useEffect(() => {
    setHydrated(true);
    setMounted(true);
  }, []);

  // 🆕 EFECTO: Reaccionar a cambios en el store (center/zoom) y mover el mapa suavemente
  useEffect(() => {
    if (!mapRef.current) return;
    
    // Obtenemos el estado actual del mapa para evitar movimientos innecesarios
    const currentCenter = mapRef.current.getCenter();
    const currentZoom = mapRef.current.getZoom();
    
    const storeCenter = useMapStore.getState().center;
    const storeZoom = useMapStore.getState().zoom;
    
    // Si no hay centro en el store, no hacemos nada
    if (!storeCenter) return;
    
    const [ln, lt] = storeCenter;
    const z = storeZoom ?? currentZoom;
    
    // Comprobamos si la diferencia es significativa para evitar loops
    const dist = Math.sqrt(
      Math.pow(ln - currentCenter.lng, 2) + Math.pow(lt - currentCenter.lat, 2)
    );
    
    // Si la distancia es pequeña y el zoom es similar, ignoramos
    if (dist < 0.0001 && Math.abs(z - currentZoom) < 0.1) return;
    
    // Usamos flyTo para una transición suave
    mapRef.current.flyTo({
      center: [ln, lt],
      zoom: z,
      speed: 1.2, // Velocidad de vuelo (1.2 es default)
      curve: 1.42, // Curvatura del vuelo
      essential: true // Esta animación es esencial (no se omite si el usuario ha deshabilitado animaciones)
    });
    
  }, [persistedCenter, persistedZoom]); // Dependemos de las props suscritas

  // 🆕 EFECTO: Actualizar la capa de ruta cuando routeData cambia
  useEffect(() => {
    if (!mapRef.current) return;
    
    // Check if source exists
    const routeSource = mapRef.current.getSource(ROUTE_SOURCE_ID) as GeoJSONSource | undefined;
    
    if (routeSource) {
      console.debug("[ROUTE] Updating route data", routeData);
      routeSource.setData({
        type: "FeatureCollection",
        features: routeData ? [routeData] : []
      });
    } else {
        // If source doesn't exist yet but we have data, we might need to add it?
        // Usually the main onLoad adds the source. If this runs before onLoad, it might miss.
        // But mapRef.current check handles most cases.
        // We can just log specific warning if map is ready but source isn't.
        if (mapRef.current.loaded() && routeData) {
            console.warn("[ROUTE] Map loaded but route source not found when trying to update data.");
        }
    }
  }, [routeData]);

  useEffect(() => {
    if (!hydrated) return;
    if (!mapEl.current) return;
    if (mapRef.current) return;
    let cancelled = false;
    let teardown: (() => void) | undefined;

    (async () => {
      const maplibregl = (await import("maplibre-gl")).default;
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
        center: initialCenterRef.current,
        zoom: initialZoomRef.current,
        attributionControl: false,
      });
      mapRef.current = map;

      const onLoad = () => {
        if (!mapRef.current?.getSource(SOURCE_ID)) {
          const sourceSpec = {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: [],
            } as FeatureCollection<Point, AISProps>,
            cluster: true,
            clusterRadius: 60,
            clusterMaxZoom: 12,
          } as unknown as GeoJSONSourceSpecification;
          mapRef.current!.addSource(SOURCE_ID, sourceSpec);
        }

        // 🆕 Add route source and layer (moved to main onLoad for reliability)
        if (mapRef.current && !mapRef.current.getSource(ROUTE_SOURCE_ID)) {
          console.debug("[ROUTE] initializing route source with:", routeDataRef.current);
          mapRef.current.addSource(ROUTE_SOURCE_ID, {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: routeDataRef.current ? [routeDataRef.current] : []
            }
          });

          mapRef.current.addLayer({
            id: ROUTE_LAYER_ID,
            type: "line",
            source: ROUTE_SOURCE_ID,
            layout: {
              "line-join": "round",
              "line-cap": "round"
            },
            paint: {
              "line-color": "#3b82f6", // Blue-500
              "line-width": 4,
              "line-dasharray": [2, 1]
            }
          });
        }

        if (mapRef.current) {
          if (!mapRef.current.hasImage(SHIP_IMAGE_ID)) {
            const img = new window.Image(24, 24);
            img.onload = () => {
              try {
                if (!mapRef.current) return;
                mapRef.current.addImage(SHIP_IMAGE_ID, img, { pixelRatio: 2 });
                if (!mapRef.current.getLayer(LAYER_CLUSTERS_ID)) {
                  mapRef.current.addLayer({
                    id: LAYER_CLUSTERS_ID,
                    type: "symbol",
                    source: SOURCE_ID,
                    filter: ["has", "point_count"],
                    layout: {
                      "icon-image": SHIP_IMAGE_ID,
                      "icon-size": [
                        "interpolate",
                        ["linear"],
                        ["zoom"],
                        0,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 1.5,
                          100, 2.0,
                          500, 2.8
                        ],
                        6,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 2.0,
                          100, 2.8,
                          500, 3.6
                        ],
                        10,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 2.8,
                          100, 3.6,
                          500, 4.8
                        ],
                        14,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 3.6,
                          100, 4.6,
                          500, 6.0
                        ],
                        18,
                        [
                          "interpolate",
                          ["linear"],
                          ["get", "point_count"],
                          1, 5.0,
                          100, 6.2,
                          500, 8.0
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
            if (!mapRef.current.getLayer(LAYER_CLUSTERS_ID)) {
              mapRef.current.addLayer({
                id: LAYER_CLUSTERS_ID,
                type: "symbol",
                source: SOURCE_ID,
                filter: ["has", "point_count"],
                layout: {
                  "icon-image": SHIP_IMAGE_ID,
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
        
        // ✨ Load and add ports layer
        if (mapRef.current && !mapRef.current.hasImage(PORT_IMAGE_ID)) {
          const portImg = new window.Image(24, 24);
          portImg.onload = () => {
            try {
              if (!mapRef.current) return;
              mapRef.current.addImage(PORT_IMAGE_ID, portImg, { pixelRatio: 2 });
              
              // Add ports source
              if (!mapRef.current.getSource(PORTS_SOURCE_ID)) {
                mapRef.current.addSource(PORTS_SOURCE_ID, {
                  type: "geojson",
                  data: {
                    type: "FeatureCollection",
                    features: [],
                  } as FeatureCollection<Point>,
                } as unknown as GeoJSONSourceSpecification);
              }
              
              // Add ports layer
              if (!mapRef.current.getLayer(PORTS_LAYER_ID)) {
                mapRef.current.addLayer({
                  id: PORTS_LAYER_ID,
                  type: "symbol",
                  source: PORTS_SOURCE_ID,
                  layout: {
                    "icon-image": PORT_IMAGE_ID,
                    "icon-size": [
                      "interpolate",
                      ["linear"],
                      ["zoom"],
                      0, 0.8,
                      6, 1.0,
                      10, 1.2,
                      14, 1.5,
                      18, 2.0
                    ],
                    "icon-allow-overlap": true,  // Ensure ports always render on top
                    "icon-ignore-placement": true,  // Ports don't affect placement of other symbols
                    "symbol-z-order": "source",  // Maintain source order for consistent rendering
                  },
                  paint: {},
                });
              }
              
              // Fetch and display ports
              void (async () => {
                try {
                  const portsResponse = await apiFetch<PortListResponse>("/ports/list");
                  const features = portsResponse.ports
                    .filter(p => p.lat != null && p.lon != null && Number.isFinite(p.lat) && Number.isFinite(p.lon))
                    .map(p => ({
                      type: "Feature" as const,
                      id: p.port_number,
                      geometry: {
                        type: "Point" as const,
                        coordinates: [p.lon!, p.lat!],
                      },
                      properties: {
                        port_number: p.port_number,
                      },
                    }));
                    
                  const fc: FeatureCollection<Point> = {
                    type: "FeatureCollection",
                    features,
                  };
                  
                  const portsSource = mapRef.current?.getSource(PORTS_SOURCE_ID) as GeoJSONSource | undefined;
                  if (portsSource) {
                    portsSource.setData(fc);
                    setPortsLoaded(true);
                    console.debug(`[PORTS] Loaded ${features.length} ports`);
                  }
                } catch (error) {
                  console.error("[PORTS] Failed to load ports:", error);
                }
              })();
            } catch (error) {
              console.error("[PORTS] Error adding port layer:", error);
            }
          };
          portImg.src = "/images/port.svg";
        }
        
        sourceReadyRef.current = true;

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

        if (mapRef.current) {
          const onMoveEnd = () => {
            try {
              const c = mapRef.current!.getCenter();
              const z = mapRef.current!.getZoom();
              useMapStore.getState().setView([c.lng, c.lat], z);
            } catch {}
          };
          mapRef.current.on("moveend", onMoveEnd);
          const originalTear = teardown;
          teardown = () => {
            try {
              mapRef.current?.off("moveend", onMoveEnd);
            } catch {}
            originalTear?.();
          };
        }

        // 🔧 MODIFICADO: Evento de clic con manejo de errores
        if (mapRef.current) {
            const currentMap = mapRef.current; // Almacena el valor de mapRef.current

            currentMap.on("click", LAYER_SHIP_SYMBOL_ID, async (e) => {
                const features = currentMap.queryRenderedFeatures(e.point, {
                    layers: [LAYER_SHIP_SYMBOL_ID],
                });

                if (!features || features.length === 0) return;

                const feature = features[0];
                const props = (feature.properties ?? {}) as Record<string, unknown>;
                
                // 🔧 FIX: MapLibre stores properties as loose types. Strings like "001234567" might become numbers.
                // We ensure it's a string and pad it back to 9 digits if leading zeros were stripped.
                let rawMmsi = props?.mmsi ? String(props.mmsi) : "";
                let mmsi = rawMmsi.padStart(9, '0');

                // Validar que el MMSI sea exactamente 9 dígitos numéricos
                if (!mmsi || mmsi.length !== 9 || !/^\d{9}$/.test(mmsi)) {
                    console.warn(`[AIS] Click ignored: Invalid MMSI. Raw="${rawMmsi}", Padded="${mmsi}"`, props);
                    return;
                }
                
                if (rawMmsi !== mmsi) {
                    console.debug(`[AIS] Fixed MMSI: "${rawMmsi}" -> "${mmsi}"`);
                }

                // Limpiar estados previos
                setVesselError(null);
                setSelectedVessel(null);
                setRouteData(null); // Clear route on selection change

                // Verificar cache
                const cached = vesselDetailsCache.current.get(mmsi);
                if (cached) {
                    setSelectedVessel(cached);
                    return;
                }

                setLoadingDetails(true);
                try {
                    const response = await apiFetch<VesselDetails>(`/details/${mmsi}`);
                    vesselDetailsCache.current.set(mmsi, response);
                    setSelectedVessel(response);
                } catch (error: any) {
                    // Manejo de errores
                    const status = error?.response?.status || error?.status;

                    if (status === 404) {
                        setVesselError({
                            mmsi,
                            message: "This vessel isn't sending static data right now",
                            type: 'not_found'
                        });
                    } else if (status === 408) {
                        setVesselError({
                            mmsi,
                            message: "Timeout waiting for vessel data",
                            type: 'timeout'
                        });
                    } else {
                        setVesselError({
                            mmsi,
                            message: "Error loading vessel details",
                            type: 'error'
                        });
                    }

                    console.error("[VESSEL] Error fetching details:", error);
                } finally {
                    setLoadingDetails(false);
                }
            });

            currentMap.on("mouseenter", LAYER_SHIP_SYMBOL_ID, () => {
                currentMap.getCanvas().style.cursor = "pointer";
            });

            currentMap.on("mouseleave", LAYER_SHIP_SYMBOL_ID, () => {
                currentMap.getCanvas().style.cursor = "";
            });
            
            // 🆕 Port click handler
            currentMap.on("click", PORTS_LAYER_ID, async (e) => {
                const features = currentMap.queryRenderedFeatures(e.point, {
                    layers: [PORTS_LAYER_ID],
                });

                if (!features || features.length === 0) return;

                const feature = features[0];
                const props = (feature.properties ?? {}) as Record<string, unknown>;
                const portNumber = props?.port_number;

                if (!portNumber || typeof portNumber !== 'number') {
                    console.warn(`[PORT] Click ignored: Invalid port_number`, props);
                    return;
                }

                // Clear previous selections
                setVesselError(null);
                setSelectedVessel(null);
                setSelectedPort(null);
                setRouteData(null); // Clear route on selection change

                setLoadingPortDetails(true);
                try {
                    const response = await apiFetch<PortDetails>(`/ports/details/${portNumber}`);
                    setSelectedPort({ ...response, port_number: portNumber });
                } catch (error: any) {
                    console.error("[PORT] Error fetching details:", error);
                    // Could add port error handling similar to vessels if needed
                } finally {
                    setLoadingPortDetails(false);
                }
            });

            currentMap.on("mouseenter", PORTS_LAYER_ID, () => {
                currentMap.getCanvas().style.cursor = "pointer";
            });

            currentMap.on("mouseleave", PORTS_LAYER_ID, () => {
                currentMap.getCanvas().style.cursor = "";
            });
        } else {
            console.error("mapRef.current es null al intentar añadir evento de clic");
        }

        void (async () => {
          try {
            const m = mapRef.current;
            if (!m) return;
            const b = m.getBounds();
            const west = b.getWest();
            const south = b.getSouth();
            const east = b.getEast();
            const north = b.getNorth();

            const PAGE_SIZE = 1000;
            const MAX_ITEMS = 5000;
            let page = 1;
            let received = 0;
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
              await new Promise((r) => setTimeout(r, 0));
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

      const startFlush = () => {
        if (flushTimerRef.current != null) return;
        flushTimerRef.current = window.setInterval(() => {
          if (!sourceReadyRef.current || !mapRef.current) return;

          // 🆕 Watchdog: Ensure route layer is in sync with state
          // Moved before flushNeededRef check to be truly independent
          const routeSource = mapRef.current.getSource(ROUTE_SOURCE_ID) as GeoJSONSource | undefined;
          if (routeSource) {
            // Only update if there's actually data, to avoid flickering with empty sets if not needed
            // But if routeDataRef.current is null, we DO want to clear it.
            routeSource.setData({
              type: "FeatureCollection",
              features: routeDataRef.current ? [routeDataRef.current] : []
            });
          }

          if (!flushNeededRef.current) return;
          
          const m = mapRef.current;
          const b = m.getBounds();
          const west = b.getWest();
          const south = b.getSouth();
          const east = b.getEast();
          const north = b.getNorth();
          const crossesAntimeridian = west > east;
          const MAX_RENDERED = 8000;

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

      const startPolling = () => {
        setConnected(true);
        console.debug("[AIS] Iniciando polling periódico a /aisstream/positions");
        
        const pollPositions = async () => {
          try {
            const m = mapRef.current;
            if (!m) return;
            
            const b = m.getBounds();
            const west = b.getWest();
            const south = b.getSouth();
            const east = b.getEast();
            const north = b.getNorth();
            
            const res = await apiFetch<{
              total: number;
              page: number;
              page_size: number;
              items: Array<{ id: string | number; lat: number; lon: number }>;
            }>(
              `/aisstream/positions?page=1&page_size=2000` +
                `&west=${west}&south=${south}&east=${east}&north=${north}`
            );
            
            const list = res?.items ?? [];
            let updatedCount = 0;
            
            for (const item of list) {
              if (
                typeof item?.lon !== "number" ||
                !Number.isFinite(item.lon) ||
                typeof item?.lat !== "number" ||
                !Number.isFinite(item.lat)
              )
                continue;
              
              upsertFeature({
                mmsi: String(item.id),
                lon: item.lon,
                lat: item.lat,
                cog: 0,
                sog: undefined,
                name: undefined,
              });
              updatedCount++;
            }
            
            flushNeededRef.current = true;
            
            console.debug(`[AIS] Polling actualizado: ${updatedCount} barcos, total: ${featuresRef.current.size}`);
          } catch (error) {
            console.error("[AIS] Error en polling:", error);
            setConnected(false);
          }
        };
        
        void pollPositions();
        
        pollingIntervalRef.current = window.setInterval(() => {
          void pollPositions();
        }, 30000);
      };
      
      startPolling();
      void fetchTotalVessels();

      function upsertFeature(v: Vessel) {
        if (!v.mmsi || v.mmsi.length > 9 || !/^\d+$/.test(v.mmsi)) {
          return;
        }
        
        if (!Number.isFinite(v.lon) || !Number.isFinite(v.lat)) return;
        
        const id = v.mmsi;
        const nextProps: AISProps = {
          mmsi: v.mmsi,
          name: v.name,
          sog: Number.isFinite(v.sog ?? NaN) ? v.sog : undefined,
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

      const cleanup = () => {
        if (pollingIntervalRef.current != null) {
          window.clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        setConnected(false);
        try {
          if (mapRef.current?.getLayer(LAYER_SHIP_SYMBOL_ID))
            mapRef.current.removeLayer(LAYER_SHIP_SYMBOL_ID);
          if (mapRef.current?.getLayer(LAYER_CLUSTER_COUNT_ID))
            mapRef.current.removeLayer(LAYER_CLUSTER_COUNT_ID);
          if (mapRef.current?.getLayer(LAYER_CLUSTERS_ID))
            mapRef.current.removeLayer(LAYER_CLUSTERS_ID);
          if (mapRef.current?.getLayer(LAYER_UNCLUSTERED_ID))
            mapRef.current.removeLayer(LAYER_UNCLUSTERED_ID);
          if (mapRef.current?.getLayer(PORTS_LAYER_ID))
            mapRef.current.removeLayer(PORTS_LAYER_ID);
          if (mapRef.current?.getSource(SOURCE_ID))
            mapRef.current.removeSource(SOURCE_ID);
          if (mapRef.current?.getSource(PORTS_SOURCE_ID))
            mapRef.current.removeSource(PORTS_SOURCE_ID);
        } catch {}
        mapRef.current?.remove();
        mapRef.current = null;
        if (refreshTimer != null) window.clearTimeout(refreshTimer);
      };

      teardown = cleanup;
      if (cancelled) cleanup();
    })();

    return () => {
      cancelled = true;
      teardown?.();
    };
  }, [hydrated]);

  // 🗑️ REMOVIDO: Este efecto anterior usaba jumpTo y conflictuaba con la nueva lógica de flyTo
  // La nueva lógica en el useEffect anterior (líneas ~135) ya maneja las actualizaciones del centro y zoom
  /*
  useEffect(() => {
    const m = mapRef.current;
    if (!m) return;
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
  */

  if (!mounted) {
    return <div className="w-full h-[60vh] bg-slate-50" aria-hidden />;
  }

  return (
    <div className="fixed inset-0 z-0">
      <div ref={mapEl} className="w-full h-full" />
      
      {/* 🆕 Panel de error cuando el barco no envía datos estáticos */}
      {vesselError && (
        <div className="absolute top-4 right-4 bg-white p-6 rounded-lg shadow-lg max-w-md z-10 border-l-4 border-orange-500">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center gap-3">
              <div className="text-orange-500 text-2xl">⚠️</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">Vessel Not Available</h3>
                <p className="text-sm text-gray-600">MMSI: {vesselError.mmsi}</p>
              </div>
            </div>
            <button 
              onClick={() => setVesselError(null)}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ✕
            </button>
          </div>
          
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <p className="text-gray-700">
              {vesselError.message}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              The vessel may not be broadcasting static data at this moment. Try again later.
            </p>
          </div>
        </div>
      )}
      
      {/* 🆕 Panel de detalles del puerto */}
      {selectedPort && (
        <div className="absolute top-4 right-4 bg-white p-6 rounded-lg shadow-lg max-w-md z-10 border-l-4 border-emerald-500">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                {selectedPort.port_name || selectedPort.name || "Port Details"}
              </h2>
              <p className="text-sm text-emerald-600">Port #{selectedPort.port_number}</p>
            </div>
            <button 
              onClick={() => setSelectedPort(null)}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {selectedPort.port_name && (
              <div className="flex justify-between">
                <span className="font-medium">Port Name:</span>
                <span>{selectedPort.port_name}</span>
              </div>
            )}
            {selectedPort.country_name && (
              <div className="flex justify-between">
                <span className="font-medium">Country:</span>
                <span>{selectedPort.country_name}</span>
              </div>
            )}
            {selectedPort.region_name && (
              <div className="flex justify-between">
                <span className="font-medium">Region:</span>
                <span>{selectedPort.region_name}</span>
              </div>
            )}
            {selectedPort.unlocode && (
              <div className="flex justify-between">
                <span className="font-medium">UN/LOCODE:</span>
                <span className="font-mono text-sm">{selectedPort.unlocode}</span>
              </div>
            )}
            {(selectedPort.ycoord != null && selectedPort.xcoord != null) && (
              <div className="flex justify-between">
                <span className="font-medium">Coordinates:</span>
                <span className="font-mono text-sm">
                  {selectedPort.ycoord?.toFixed(4)}, {selectedPort.xcoord?.toFixed(4)}
                </span>
              </div>
            )}
            {selectedPort.alternate_name && (
              <div className="flex justify-between">
                <span className="font-medium">Alternate Name:</span>
                <span>{selectedPort.alternate_name}</span>
              </div>
            )}
            {selectedPort.nav_area && (
              <div className="flex justify-between">
                <span className="font-medium">Nav Area:</span>
                <span>{selectedPort.nav_area}</span>
              </div>
            )}
            {selectedPort.publication_number && (
              <div className="flex justify-between">
                <span className="font-medium">Publication:</span>
                <span>{selectedPort.publication_number}</span>
              </div>
            )}
            {selectedPort.chart_number && (
              <div className="flex justify-between">
                <span className="font-medium">Chart:</span>
                <span>{selectedPort.chart_number}</span>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Panel de detalles del barco (exitoso) */}
      {selectedVessel && !selectedPort && (
        <div className="absolute top-4 right-4 bg-white p-6 rounded-lg shadow-lg max-w-md z-10">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold text-gray-800">
              {selectedVessel.data.ship_name || "N/A"}
            </h2>
            <button 
              onClick={() => setSelectedVessel(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">MMSI:</span>
              <span>{selectedVessel.mmsi}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">IMO:</span>
              <span>{selectedVessel.data.imo_number || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Call Sign:</span>
              <span>{selectedVessel.data.call_sign || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Ship Type:</span>
              <span>{selectedVessel.data.ship_type || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Destination:</span>
              <span>{selectedVessel.data.destination || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Draught:</span>
              <span>{selectedVessel.data.draught ? `${selectedVessel.data.draught}m` : "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Dimensions:</span>
              <span>{selectedVessel.data.dimensions ? `${selectedVessel.data.dimensions.length}m x ${selectedVessel.data.dimensions.width}m` : "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">ETA:</span>
              <span>{formatDate(selectedVessel.data.eta)}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Last Update:</span>
              <span>{formatDate(selectedVessel.data.timestamp)}</span>
            </div>
          </div>

          {/* 🆕 Route Logic */}
          {selectedVessel.data.destination && selectedVessel.data.destination !== "N/A" && (selectedVessel.data.latitude != null && selectedVessel.data.longitude != null) && (
             <button
               onClick={async () => {
                   if (!selectedVessel.data.destination) return;
                   setLoadingRoute(true);
                   try {
                       const dest = selectedVessel.data.destination.trim();
                       // Backend handles normalization now (e.g. USXXX -> US XXX, splitting >>)
                       
                       const port = await apiFetch<PortDetails>(`/ports/search?unlocode=${encodeURIComponent(dest)}`);
                       
                       if (port && port.xcoord && port.ycoord) {
                           const routeFeature: Feature = {
                               type: "Feature",
                               geometry: {
                                   type: "LineString",
                                   coordinates: [
                                       [selectedVessel.data.longitude!, selectedVessel.data.latitude!],
                                       [port.xcoord, port.ycoord]
                                   ]
                               },
                               properties: {}
                           };
                           setRouteData(routeFeature);
                           
                           // Fit bounds to show route
                           if (mapRef.current) {
                               const maplibregl = (await import("maplibre-gl")).default;
                               const bounds = new maplibregl.LngLatBounds();
                               bounds.extend([selectedVessel.data.longitude!, selectedVessel.data.latitude!]);
                               bounds.extend([port.xcoord, port.ycoord]);
                               mapRef.current.fitBounds(bounds, { padding: 100 });
                           }
                       } else {
                           alert("Destination port coordinates not found.");
                       }
                   } catch (e) {
                       console.error("Failed to find route endpoint", e);
                       alert("Could not find destination port.");
                   } finally {
                       setLoadingRoute(false);
                   }
               }}
               className="mt-4 w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2"
               disabled={loadingRoute}
             >
                 {loadingRoute ? "Calculating..." : "Show Route to Destination"}
             </button>
          )}
        </div>
      )}

      {/* Indicador de estado de conexión */}
      <div className="absolute top-3 right-3 z-50">
        <div
          className="px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2"
          style={{ background: "rgba(255,255,255,0.9)" }}
        >
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-rose-500'}`} />
          <span>{connected ? "Conectado" : "Desconectado"}</span>
          <span className="text-slate-600">·</span>
          <span className="text-slate-600">{vesselCount.toLocaleString()} buques</span>
          {lastUpdate && (
            <>
              <span className="text-slate-600">·</span>
              <span className="text-slate-600">{lastUpdate}</span>
            </>
          )}
          <button
            onClick={fetchTotalVessels}
            disabled={loadingVesselCount}
            className="ml-2 px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingVesselCount ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              '↻'
            )}
          </button>
        </div>
      </div>

      {/* Indicador de carga */}
      {(loadingDetails || loadingPortDetails) && (
        <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg z-10">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            <span>Loading {loadingPortDetails ? 'port' : 'vessel'} details...</span>
          </div>
        </div>
      )}
    </div>
  );
}