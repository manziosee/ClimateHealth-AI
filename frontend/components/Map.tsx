"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import { PredictionResponse } from "../app/types";

interface MapProps {
  predictions: PredictionResponse[];
  selectedDisease: "malaria" | "flu" | "cholera" | "all";
  onMapClick?: (lat: number, lon: number) => void;
  selectedPrediction?: PredictionResponse | null;
}

export default function Map({
  predictions,
  selectedDisease,
  onMapClick,
  selectedPrediction
}: MapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Standard center coordinates
    const initialLat = -1.9403;
    const initialLon = 29.8739;

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: 6,
      zoomControl: false, // Turn off default zoom to custom render a clean futuristic set
      attributionControl: false
    });

    // Dark-themed premium GIS tiles
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 19
    }).addTo(map);

    // Custom Zoom Controls in cyber style
    L.control.zoom({
      position: "topright"
    }).addTo(map);

    // Map Click Handler
    map.on("click", (e: L.LeafletMouseEvent) => {
      const { lat, lng } = e.latlng;
      const targetLat = Math.round(lat * 10000) / 10000;
      const targetLon = Math.round(lng * 10000) / 10000;
      if (onMapClick) {
        onMapClick(targetLat, targetLon);
      }
    });

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [onMapClick]);

  // Focus and Fly to Selected Spot
  useEffect(() => {
    if (mapRef.current && selectedPrediction) {
      mapRef.current.flyTo([selectedPrediction.lat, selectedPrediction.lon], 9, {
        animate: true,
        duration: 1.5
      });
    }
  }, [selectedPrediction]);

  // Update Markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear old markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // Filter predictions
    const filtered = predictions.filter((p) => {
      if (selectedDisease === "all") return true;
      return p.disease === selectedDisease;
    });

    filtered.forEach((p) => {
      // Determine neon cyber colors based on risk level and disease
      const themeColor =
        p.risk_level === "High"
          ? "#ef4444" // Neon Red
          : p.risk_level === "Medium"
          ? "#f59e0b" // Cyber Gold
          : "#06b6d4"; // Cyan blue

      const popupContent = `
        <div style="font-family: monospace; color: #e2e8f0; background: #030712; padding: 12px; border: 1px solid ${themeColor}; border-radius: 8px; box-shadow: 0 0 15px ${themeColor}40;">
          <div style="font-size: 11px; font-weight: 700; color: ${themeColor}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>[ TARGET DIAGNOSTICS ]</span>
          </div>
          <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; color: #fff; text-transform: uppercase;">
            ${p.location_name || `Vector (${p.lat.toFixed(2)}, ${p.lon.toFixed(2)})`}
          </h4>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px;">
            <span style="color: #64748b;">PATHOGEN:</span>
            <strong style="color: #3b82f6; text-transform: uppercase;">${p.disease}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px;">
            <span style="color: #64748b;">RISK FACTOR:</span>
            <strong style="color: ${themeColor};">${p.risk_level.toUpperCase()}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px;">
            <span style="color: #64748b;">ESTIMATED CASES:</span>
            <strong style="color: #fff;">${p.expected_cases}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 11px;">
            <span style="color: #64748b;">MODEL CONFIDENCE:</span>
            <strong style="color: #10b981;">${Math.round(p.confidence * 100)}%</strong>
          </div>
          <div style="border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 6px; font-size: 10px; color: #94a3b8; display: flex; justify-content: space-between;">
            <span>TEMP: ${p.temperature.toFixed(1)}°C</span>
            <span>RAIN: ${p.rainfall.toFixed(0)}mm</span>
          </div>
        </div>
      `;

      // Cyber Target Lock circular ring marker style
      const targetLockIcon = L.divIcon({
        className: "cyber-target-marker",
        html: `
          <div style="position: relative; width: 32px; height: 32px; display: flex; items-center: center; justify-content: center;">
            <!-- Outer rotating radar rings -->
            <span style="
              position: absolute;
              width: 32px;
              height: 32px;
              border: 1px dashed ${themeColor};
              border-radius: 50%;
              animation: spin 8s linear infinite;
              opacity: 0.8;
            "></span>
            <!-- Inner pulsing warning beacon -->
            <span style="
              position: absolute;
              top: 4px;
              left: 4px;
              width: 24px;
              height: 24px;
              border: 1.5px solid ${themeColor};
              border-radius: 50%;
              animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
              opacity: 0.5;
            "></span>
            <!-- Central core lock -->
            <span style="
              position: absolute;
              top: 12px;
              left: 12px;
              width: 8px;
              height: 8px;
              background-color: ${themeColor};
              border-radius: 50%;
              box-shadow: 0 0 10px ${themeColor};
            "></span>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = L.marker([p.lat, p.lon], { icon: targetLockIcon })
        .bindPopup(popupContent, { className: "custom-leaflet-popup" })
        .addTo(map);

      markersRef.current.push(marker);
    });
  }, [predictions, selectedDisease]);

  return (
    <div className="relative w-full h-full min-h-[460px] cyber-panel rounded-2xl overflow-hidden border border-blue-500/20 shadow-2xl">
      {/* Cyber Brackets */}
      <div className="cyber-corner cyber-corner-tl" />
      <div className="cyber-corner cyber-corner-tr" />
      <div className="cyber-corner cyber-corner-bl" />
      <div className="cyber-corner cyber-corner-br" />

      {/* Map Content */}
      <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: "460px" }} />

      {/* Cyber GIS Legend overlay */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-slate-950/85 backdrop-blur-md px-4 py-3.5 rounded-xl border border-blue-500/20 shadow-xl max-w-[210px] font-mono text-[10px]">
        <div className="flex items-center gap-1.5 mb-2.5 border-b border-blue-500/20 pb-1.5">
          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-ping" />
          <h4 className="font-bold text-blue-400 uppercase tracking-widest text-[9px]">GIS SENSORS ACTIVE</h4>
        </div>
        <div className="flex flex-col gap-2 text-slate-300">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 border border-slate-950" />
              <span>CRITICAL OUTBREAK</span>
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 border border-slate-950" />
              <span>WARNING RANGE</span>
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 border border-slate-950" />
              <span>LOW LEVEL RISK</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
