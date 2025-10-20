"use client";
import { useEffect, useRef } from "react";
// OpenLayers runtime imports
import OLMap from "ol/Map";
import { defaults as defaultControls } from "ol/control";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import OSM from "ol/source/OSM";
import XYZ from "ol/source/XYZ";
import { createXYZ } from "ol/tilegrid";

// Note: global CSS for OpenLayers is imported in app/globals.css via `@import 'ol/ol.css';`

type OpenLayersMapProps = {
  height?: number;
  center?: [number, number]; // lon, lat in EPSG:4326
  zoom?: number;
  // Enlarge seamarks by upscaling tiles: 0 (normal), 1 (~2x), 2 (~4x), 3 (~8x)
  seamarkZoomOffset?: 0 | 1 | 2 | 3;
};

export default function OpenLayersMap({ height = 560, center = [-3.7038, 40.4168], zoom = 3, seamarkZoomOffset = 1 }: OpenLayersMapProps) {
  const mapEl = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<OLMap | null>(null);

  useEffect(() => {
    if (!mapEl.current) return;

    // OpenLayers uses EPSG:3857 by default; OSM source expects that.
    // We pass lon/lat, so convert using fromLonLat lazily to avoid heavier imports at module load.
    (async () => {
      const { fromLonLat } = await import("ol/proj");
      const seamarkMaxZoom = Math.max(0, 18 - seamarkZoomOffset);
      const seamarkTileGrid = createXYZ({ maxZoom: seamarkMaxZoom });

      const map = new OLMap({
        target: mapEl.current!,
        // disable the built-in attribution control so we can render attribution outside the map canvas
        controls: defaultControls({ attribution: false }),
        layers: [
          // Base map: OpenStreetMap
          new TileLayer({
            source: new OSM(),
          }),
          // Maritime overlay: OpenSeaMap seamarks
          new TileLayer({
            source: new XYZ({
              url: "https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
              tileGrid: seamarkTileGrid,
              attributions:
                '',
              maxZoom: 18,
            }),
            zIndex: 10,
            opacity: 1,
            className: 'seamarks-layer',
          }),
        ],
        view: new View({
          center: fromLonLat(center),
          zoom,
        }),
      });
      mapRef.current = map;
    })();

    return () => {
      mapRef.current?.setTarget(undefined);
      mapRef.current = null;
    };
  }, [center, zoom, seamarkZoomOffset]);

  return (
    <div
      ref={mapEl}
      className="w-full rounded-lg overflow-hidden border border-slate-200"
      style={{ height }}
    />
  );
}
