"use client";
import { useEffect, useRef, useState } from "react";
import type { Map as MLMap, Marker } from "maplibre-gl";
import type { StyleSpecification } from "maplibre-gl";
import 'maplibre-gl/dist/maplibre-gl.css';

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


export default function AisLiveMap({ token, center = [-3.7038, 40.4168], zoom = 3 }: Props) {
	const mapEl = useRef<HTMLDivElement | null>(null);
	const mapRef = useRef<MLMap | null>(null);
	const markersRef = useRef<Map<string, Marker>>(new Map());
	const wsRef = useRef<WebSocket | null>(null);

	const [connected, setConnected] = useState(false);
	const [vesselCount, setVesselCount] = useState(0);
	const [wsState, setWsState] = useState<number | null>(null);
	const [lastClose, setLastClose] = useState<{code?: number; reason?: string} | null>(null);
	const [lastMsg, setLastMsg] = useState<string | null>(null);

	const [hydrated, setHydrated] = useState(false);

	useEffect(() => {
		// mark component as hydrated on client to avoid SSR/CSR mismatches
		setHydrated(true);
	}, []);

	useEffect(() => {
		// Don't run map/ws setup until component has hydrated on client
		if (!hydrated) return;
		if (!mapEl.current) return;
		if (!token) {
			console.warn("[AIS] NEXT_PUBLIC_AISSTREAM_KEY no está definido. El mapa se renderizará sin datos en vivo.");
		}
		let destroyed = false;

			(async () => {
			const maplibregl = (await import("maplibre-gl")).default;
			// Basic raster OSM style
				const style = {
				version: 8,
				sources: {
					osm: {
						type: 'raster',
						tiles: [
							'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
							'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
							'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
						],
						tileSize: 256,
						attribution: '© OpenStreetMap contributors',
					},
				},
				layers: [
					{ id: 'osm', type: 'raster', source: 'osm' },
				],
				} as unknown as StyleSpecification;

					const map = new maplibregl.Map({
				container: mapEl.current!,
				style,
				center,
						zoom,
						attributionControl: false,
			});
			mapRef.current = map;

			const ws = new WebSocket('wss://stream.aisstream.io/v0/stream');
			wsRef.current = ws;
			ws.addEventListener('open', () => {
				setConnected(true);
				// Subscribe to a wide bbox initially (worldwide demo); adjust as needed
				const sub = {
					Apikey: token,
					BoundingBoxes: [
						// world-ish bounds broken into 2 to avoid anti-meridian complexity
						[[-180, -85], [180, 85]],
					],
					// You can filter by message types; Keep default for positions
				};
				// Mask token to avoid leaking it in logs
				const masked = token ? token.replace(/.(?=.{4})/g, "*") : "";
				console.debug(`[AIS] Suscripción abierta (token: ${masked})`);
				ws.send(JSON.stringify(sub));
			});

			ws.addEventListener('close', (ev) => {
				setConnected(false);
				setLastClose({ code: (ev as CloseEvent).code, reason: (ev as CloseEvent).reason });
				setWsState(ws.readyState);
				console.debug('[AIS] WebSocket cerrado', (ev as CloseEvent).code, (ev as CloseEvent).reason);
			});
			ws.addEventListener('error', (err) => {
				setConnected(false);
				setWsState(ws.readyState);
				console.error('[AIS] WebSocket error', err);
			});

			ws.addEventListener('message', (ev) => {
				// Store a short raw snippet for diagnostics (don't store huge payloads)
				const raw = typeof ev.data === 'string' ? ev.data : '';
				setLastMsg(raw.slice(0, 800));
				setWsState(ws.readyState);
				console.debug('[AIS] mensaje entrante', raw.slice(0, 200));
				
			});

			// Re-add message handler with parsing separated to keep diagnostics above
			ws.addEventListener('message', (ev) => {
				try {
					const data = JSON.parse(ev.data as string);
					// aisstream position sample: { MessageType: 'PositionReport', MMSI, Position: { lon, lat }, COG, SOG, Name }
					const msgType = data?.MessageType;
					if (msgType !== 'PositionReport' && msgType !== 'ShipStaticData') return;

					if (msgType === 'PositionReport') {
						const v: Vessel = {
							mmsi: String(data?.MMSI ?? ''),
							lon: Number(data?.Position?.lon),
							lat: Number(data?.Position?.lat),
							cog: data?.COG ? Number(data.COG) : undefined,
							sog: data?.SOG ? Number(data.SOG) : undefined,
							name: data?.Name ? String(data.Name) : undefined,
						};
						if (!Number.isFinite(v.lon) || !Number.isFinite(v.lat)) return;
						upsertMarker(v);
					}
					// Optionally merge static data (ShipStaticData) for names
					if (msgType === 'ShipStaticData') {
						const mmsi = String(data?.MMSI ?? '');
						const name = data?.Name ? String(data.Name) : undefined;
						if (name && markersRef.current.has(mmsi)) {
							// Update title/tooltip
							const m = markersRef.current.get(mmsi)!;
							const el = m.getElement();
							el.setAttribute('title', name);
						}
					}
				} catch {
					// ignore broken messages
				}
			});

							function upsertMarker(v: Vessel) {
				const id = v.mmsi;
				const existing = markersRef.current.get(id);
				if (existing) {
					existing.setLngLat([v.lon, v.lat]);
					rotateMarker(existing, v.cog);
					return;
				}
				// Create a small rotated marker (red vessel dot with pointer)
				const el = document.createElement('div');
				el.className = 'ais-marker';
				el.style.width = '14px';
				el.style.height = '14px';
				el.style.borderRadius = '50%';
				el.style.background = '#ef4444';
				el.style.border = '2px solid white';
				el.style.boxShadow = '0 0 0 1px rgba(0,0,0,0.15)';
				el.title = v.name ? `${v.name} (${v.mmsi})` : v.mmsi;

						const marker = new maplibregl.Marker({ element: el, rotationAlignment: 'map' })
					.setLngLat([v.lon, v.lat])
					.addTo(map);
				rotateMarker(marker, v.cog);
				markersRef.current.set(id, marker);
					// update visible count
					setVesselCount(markersRef.current.size);
			}

			function rotateMarker(marker: Marker, cog?: number) {
				if (typeof cog === 'number') {
					const el = marker.getElement();
					el.style.transform = `rotate(${cog}deg)`;
				}
			}

			// Clean up
					const markers = markersRef.current;
					const cleanup = () => {
						wsRef.current?.close();
						wsRef.current = null;
						markers.forEach((m) => m.remove());
						markers.clear();
						mapRef.current?.remove();
						mapRef.current = null;
						setConnected(false);
						setVesselCount(0);
					};

			if (destroyed) cleanup();
			return cleanup;
		})();

		return () => {
			destroyed = true;
			wsRef.current?.close();
			mapRef.current?.remove();
			markersRef.current.forEach((m) => m.remove());
			markersRef.current.clear();
			setConnected(false);
			setVesselCount(0);
		};
		}, [token, center, zoom]);

	return (
		<div className="fixed inset-0 z-0">
			<div ref={mapEl} className="w-full h-full" />
			{/* Connection status pill */}
			<div className="absolute top-3 right-3 z-50">
				<div className="px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2" style={{background: 'rgba(255,255,255,0.9)'}}>
					<span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500' : 'bg-rose-500'}`} />
					<span>{connected ? 'Conectado' : 'Desconectado'}</span>
					<span className="text-slate-600">·</span>
					<span className="text-slate-600">{vesselCount} buques</span>
				</div>
			</div>
			{/* Diagnostics panel */}
			<div className="absolute top-24 right-4 z-50 w-80 text-xs">
				<div className="glass-card p-3 rounded-md border border-white/30 shadow-[0_10px_30px_rgba(2,6,23,0.06)] backdrop-blur-md">
					<div className="font-medium text-slate-900">Diagnosis AIS</div>
					<div className="text-slate-600">State WS: {wsState ?? '—'}</div>
					<div className="text-slate-600">Last Close: {lastClose ? `${lastClose.code ?? '—'} ${lastClose.reason ?? ''}` : '—'}</div>
					<div className="mt-2 text-slate-700 break-words"><strong>Last Message:</strong>
						<pre className="max-h-32 overflow-auto text-xs p-1" style={{whiteSpace: 'pre-wrap'}}>{lastMsg ?? '—'}</pre>
					</div>
				</div>
			</div>
		</div>
	);
}

