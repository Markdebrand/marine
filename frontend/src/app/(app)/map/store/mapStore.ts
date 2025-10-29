"use client";
import { create } from "zustand";

type MapState = {
  center: [number, number] | null;
  zoom: number | null;
  setView: (center: [number, number], zoom?: number) => void;
  reset: () => void;
};

export const useMapStore = create<MapState>((set) => ({
  center: null,
  zoom: null,
  setView: (center, zoom) => set({ center, zoom: zoom ?? null }),
  reset: () => set({ center: null, zoom: null }),
}));
