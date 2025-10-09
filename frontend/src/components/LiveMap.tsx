"use client";
import { useEffect, useRef } from "react";

type Props = { height?: number };

export default function LiveMap({ height = 360 }: Props) {
	const mapRef = useRef<HTMLDivElement | null>(null);

	useEffect(() => {
		let cleanup: (() => void) | undefined;
		(async () => {
			try {
				const maplibregl = (await import("maplibre-gl")).default;
				// Minimal style using OSM tiles via raster style
						const map = new maplibregl.Map({
					container: mapRef.current!,
							style: {
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
						layers: [
							{ id: "osm", type: "raster", source: "osm" },
						],
							} as unknown as maplibregl.StyleSpecification,
					center: [-3.7038, 40.4168], // Madrid
					zoom: 3,
				});
				cleanup = () => map.remove();
					} catch {
				// no-op if map fails to init
			}
		})();
		return () => { cleanup?.(); };
	}, []);

	return (
		<div
			ref={mapRef}
			style={{ height }}
			className="w-full rounded-xl overflow-hidden border border-slate-200"
		/>
	);
}

