"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Activity, ShieldAlert, Droplets, Thermometer, Globe, RefreshCw, BarChart2, Radio } from "lucide-react";
import { PredictionResponse } from "./types";
import { mockPredictions } from "./mockData";

// Dynamically load Map component to bypass SSR 'window is not defined' errors
const Map = dynamic(() => import("../components/Map"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[460px] bg-slate-950/60 rounded-2xl flex flex-col items-center justify-center text-slate-500 gap-3 border border-blue-500/20">
      <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
      <span className="text-xs uppercase tracking-widest font-mono">Initializing GIS Matrix...</span>
    </div>
  )
});

import OutbreakCalculator from "../components/OutbreakCalculator";
import TrendsChart from "../components/TrendsChart";
import AlertsPanel from "../components/AlertsPanel";

export default function Home() {
  const [predictions, setPredictions] = useState<PredictionResponse[]>(mockPredictions);
  const [selectedDisease, setSelectedDisease] = useState<"malaria" | "flu" | "cholera" | "all">("all");
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionResponse | null>(null);
  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [systemTime, setSystemTime] = useState<string>("");

  const [mapClickedCoords, setMapClickedCoords] = useState<{ lat: number; lon: number }>({
    lat: -1.9403,
    lon: 29.8739
  });

  useEffect(() => {
    // Dynamic digital clock matching sci-fi header
    const updateClock = () => {
      const now = new Date();
      setSystemTime(now.toLocaleDateString() + " " + now.toLocaleTimeString());
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchPredictions = async () => {
    try {
      const res = await fetch("/api/v1/predictions");
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setPredictions(data);
        }
      }
    } catch (e) {
      console.warn("Backend API not reachable, running locally with fallback mock.", e);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, []);

  const handleRunPrediction = async (input: {
    lat: number;
    lon: number;
    disease: "malaria" | "flu" | "cholera";
    population_density: number;
  }) => {
    setIsPredicting(true);
    setStatusMessage("");
    try {
      const res = await fetch("/api/v1/predictions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input)
      });

      if (res.ok) {
        const data: PredictionResponse = await res.json();
        const updated = [data, ...predictions.filter((p) => p.id !== data.id && (p.lat !== data.lat || p.lon !== data.lon))];
        setPredictions(updated);
        setSelectedPrediction(data);
        setStatusMessage("DIAGNOSTIC CALCULATION COMPLETE.");
      } else {
        // Mock fallback simulation
        const mockResult: PredictionResponse = {
          id: Math.floor(Math.random() * 10000),
          lat: input.lat,
          lon: input.lon,
          location_name: `Grid-Sec (${input.lat.toFixed(2)}, ${input.lon.toFixed(2)})`,
          disease: input.disease,
          risk_level: input.population_density > 800 ? "High" : "Medium",
          expected_cases: Math.round(input.population_density * 0.15 + (input.disease === "malaria" ? 45 : 20)),
          confidence: 0.88,
          temperature: input.disease === "flu" ? 11 : 27.2,
          rainfall: input.disease === "malaria" ? 190 : 35,
          humidity: 80,
          predicted_at: new Date().toISOString()
        };
        const updated = [mockResult, ...predictions];
        setPredictions(updated);
        setSelectedPrediction(mockResult);
        setStatusMessage("SIMULATION PROCESSED (DEMO MODE).");
      }
    } catch (e) {
      console.error(e);
      setStatusMessage("DIAGNOSTIC ERROR ENCOUNTERED.");
    } finally {
      setIsPredicting(false);
    }
  };

  const handleMapClick = (lat: number, lon: number) => {
    setMapClickedCoords({ lat, lon });
  };

  // Metrics
  const totalPredictedCases = predictions.reduce((sum, p) => sum + p.expected_cases, 0);
  const activeAlertsCount = predictions.filter((p) => p.risk_level === "High").length;
  const avgTemp = predictions.length > 0 ? (predictions.reduce((sum, p) => sum + p.temperature, 0) / predictions.length).toFixed(1) : "22.5";

  return (
    <div className="min-h-screen bg-[#02050b] text-slate-100 font-mono relative cyber-grid selection:bg-blue-600/30">
      {/* Sci-Fi scanlines layer */}
      <div className="scanlines" />

      {/* HEADER SECTION (Futuristic visual style) */}
      <header className="border-b border-blue-500/25 bg-slate-950/80 backdrop-blur-md sticky top-0 z-[1001] px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/30 border border-blue-400/40">
            <Radio className="w-6 h-6 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <h1 className="text-xl font-black tracking-widest text-white text-glow-blue uppercase">
                CLIMATEHEALTH MATRIX
              </h1>
            </div>
            <p className="text-[9px] text-blue-400 font-mono tracking-widest uppercase">
              Global Environmental Outbreak Prognosis Matrix
            </p>
          </div>
        </div>

        {/* Real-time details */}
        <div className="flex flex-col md:flex-row items-center gap-4 text-[10px] text-slate-400">
          <div className="bg-slate-900/80 border border-blue-500/20 px-3.5 py-1.5 rounded-lg flex items-center gap-2">
            <span className="text-blue-500">SYSTEM TIME:</span>
            <span className="text-white font-bold">{systemTime || "CONNECTING..."}</span>
          </div>
          {/* Quick Filters */}
          <div className="flex bg-slate-950/80 p-0.5 rounded-xl border border-blue-500/20">
            {(["all", "malaria", "flu", "cholera"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setSelectedDisease(mode)}
                className={`px-3 py-1 rounded-lg font-bold uppercase transition-all duration-200 cursor-pointer text-[9px] tracking-wider ${
                  selectedDisease === mode
                    ? "bg-blue-600 text-white shadow-md border border-blue-400/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* DASHBOARD CONTENT (3-column layout combined Reference 1 & 2 styles) */}
      <main className="max-w-[1600px] mx-auto p-6 grid grid-cols-1 xl:grid-cols-4 gap-6">
        
        {/* COLUMN 1: INTEL & LEADERBOARDS (Left Panel) */}
        <div className="space-y-6 flex flex-col justify-between h-full">
          {/* Top Outbreak districts leaderboard - Inspired by Reference 2 */}
          <div className="cyber-panel p-5 rounded-2xl relative shadow-xl flex-1">
            <div className="cyber-corner cyber-corner-tl" />
            <div className="cyber-corner cyber-corner-tr" />
            <div className="cyber-corner cyber-corner-bl" />
            <div className="cyber-corner cyber-corner-br" />

            <div className="mb-4 border-b border-blue-500/20 pb-3">
              <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-blue-500" /> [ REGIONAL HOTSPOTS ]
              </h3>
            </div>

            <div className="space-y-4">
              {predictions.slice(0, 5).map((p, idx) => {
                const percentage = Math.min(100, Math.round((p.expected_cases / 220) * 100));
                const progressColor =
                  p.risk_level === "High"
                    ? "bg-red-500 text-red-400"
                    : p.risk_level === "Medium"
                    ? "bg-amber-500 text-amber-400"
                    : "bg-cyan-500 text-cyan-400";

                return (
                  <div key={p.id || idx} className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-300 font-bold">
                      <span className="truncate uppercase max-w-[150px]">
                        NO.{idx + 1} {p.location_name ? p.location_name.split(" ")[0] : `ZONE-${idx}`}
                      </span>
                      <span>{p.expected_cases} CAS</span>
                    </div>
                    {/* Glowing Progress bar */}
                    <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-800">
                      <div
                        className={`h-full rounded-full ${progressColor.split(" ")[0]}`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Disease Distribution Doughnut - Inspired by Reference 1 & 2 */}
          <div className="cyber-panel p-5 rounded-2xl relative shadow-xl">
            <div className="cyber-corner cyber-corner-tl" />
            <div className="cyber-corner cyber-corner-tr" />
            <div className="cyber-corner cyber-corner-bl" />
            <div className="cyber-corner cyber-corner-br" />

            <div className="mb-4 border-b border-blue-500/20 pb-3">
              <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" /> [ SYSTEM METRICS ]
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-3 text-[10px] text-slate-400">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-blue-500/10 text-center">
                <span className="block text-slate-500 font-bold mb-1">TOTAL CASES</span>
                <strong className="text-base text-slate-100 font-bold text-glow-blue">{totalPredictedCases}</strong>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-blue-500/10 text-center">
                <span className="block text-slate-500 font-bold mb-1">CRIT RISKS</span>
                <strong className="text-base text-red-500 font-bold text-glow-red">{activeAlertsCount}</strong>
              </div>
            </div>
          </div>
        </div>

        {/* COLUMN 2 & 3: MAIN MATRIX DISPLAY (Center Map + Correlation chart) */}
        <div className="xl:col-span-2 space-y-6">
          {/* Main Map widget */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center px-1 font-mono text-[10px] text-slate-400">
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
                <span>GIS MATRIX SCAN_ON: ACTIVE</span>
              </span>
              <span>COORD_REF: EPSG_3857</span>
            </div>
            <Map
              predictions={predictions}
              selectedDisease={selectedDisease}
              onMapClick={handleMapClick}
              selectedPrediction={selectedPrediction}
            />
          </div>

          {/* Composed Analytics graph */}
          <TrendsChart predictions={predictions} />
        </div>

        {/* COLUMN 4: CONTROL HUB & ALERTS (Right Panel) */}
        <div className="space-y-6">
          <OutbreakCalculator
            initialLat={mapClickedCoords.lat}
            initialLon={mapClickedCoords.lon}
            onRunPrediction={handleRunPrediction}
            isPredicting={isPredicting}
          />

          {statusMessage && (
            <div className="p-3 bg-blue-950/80 border border-blue-500/35 rounded-xl text-[10px] text-blue-400 font-mono text-center tracking-widest text-glow-blue">
              &gt;&gt; {statusMessage}
            </div>
          )}

          <AlertsPanel
            predictions={predictions}
            onSelectPrediction={setSelectedPrediction}
            selectedPrediction={selectedPrediction}
          />
        </div>
      </main>

      {/* FOOTER */}
      <footer className="border-t border-blue-500/20 bg-slate-950/80 py-6 px-6 text-center text-[10px] text-slate-500 tracking-wider">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <p>[ SYSTEM MATRIX DATA STREAM: SECURE • CLIMATEHEALTH AI © 2026 ]</p>
          <div className="flex gap-4">
            <a href="https://open-meteo.com/" target="_blank" className="hover:text-blue-400 transition-colors uppercase">OPEN-METEO_API</a>
            <span>•</span>
            <a href="https://www.who.int/" target="_blank" className="hover:text-blue-400 transition-colors uppercase">WHO_GHO_PORTAL</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
