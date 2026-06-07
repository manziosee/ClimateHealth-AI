"use client";

import { useState, useEffect } from "react";
import { Play, Cpu, Droplets, Thermometer, Users, Crosshair } from "lucide-react";

interface OutbreakCalculatorProps {
  initialLat: number;
  initialLon: number;
  onRunPrediction: (data: {
    lat: number;
    lon: number;
    disease: "malaria" | "flu" | "cholera";
    population_density: number;
  }) => Promise<void>;
  isPredicting: boolean;
}

export default function OutbreakCalculator({
  initialLat,
  initialLon,
  onRunPrediction,
  isPredicting
}: OutbreakCalculatorProps) {
  const [lat, setLat] = useState<number>(initialLat);
  const [lon, setLon] = useState<number>(initialLon);
  const [disease, setDisease] = useState<"malaria" | "flu" | "cholera">("malaria");
  const [density, setDensity] = useState<number>(620);

  useEffect(() => {
    setLat(initialLat);
    setLon(initialLon);
  }, [initialLat, initialLon]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunPrediction({ lat, lon, disease, population_density: density });
  };

  return (
    <div className="cyber-panel p-5 rounded-2xl relative shadow-xl flex flex-col justify-between h-full font-mono">
      {/* Cyber Corners */}
      <div className="cyber-corner cyber-corner-tl" />
      <div className="cyber-corner cyber-corner-tr" />
      <div className="cyber-corner cyber-corner-bl" />
      <div className="cyber-corner cyber-corner-br" />

      <div className="mb-4 border-b border-blue-500/20 pb-3">
        <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-400 animate-pulse" /> [ OUTBREAK RISK SIMULATOR ]
        </h3>
        <p className="text-[10px] text-slate-500 mt-1">
          Simulate pathogens under climate change conditions.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 text-[11px]">
        {/* Row 1: Coords */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-slate-500 mb-1 flex items-center gap-1">
              <Crosshair className="w-3 h-3 text-blue-400" /> LATITUDE
            </label>
            <input
              type="number"
              step="0.0001"
              value={lat}
              onChange={(e) => setLat(parseFloat(e.target.value))}
              className="w-full bg-slate-950/80 border border-blue-500/25 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-400 transition-colors"
              required
            />
          </div>
          <div>
            <label className="block text-slate-500 mb-1 flex items-center gap-1">
              <Crosshair className="w-3 h-3 text-blue-400" /> LONGITUDE
            </label>
            <input
              type="number"
              step="0.0001"
              value={lon}
              onChange={(e) => setLon(parseFloat(e.target.value))}
              className="w-full bg-slate-950/80 border border-blue-500/25 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-400 transition-colors"
              required
            />
          </div>
        </div>

        {/* Row 2: Disease & Density */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-slate-500 mb-1">TARGET DISEASE</label>
            <select
              value={disease}
              onChange={(e) => setDisease(e.target.value as "malaria" | "flu" | "cholera")}
              className="w-full bg-slate-950/80 border border-blue-500/25 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-400 transition-colors"
            >
              <option value="malaria">Malaria</option>
              <option value="flu">Influenza / Flu</option>
              <option value="cholera">Cholera</option>
            </select>
          </div>
          <div>
            <label className="block text-slate-500 mb-1 flex items-center gap-1">
              <Users className="w-3.5 h-3.5 text-blue-500" /> DENSITY (km²)
            </label>
            <input
              type="number"
              value={density}
              min="1"
              onChange={(e) => setDensity(parseInt(e.target.value) || 100)}
              className="w-full bg-slate-950/80 border border-blue-500/25 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-400 transition-colors"
              required
            />
          </div>
        </div>

        {/* Environmental Sliders Info */}
        <div className="p-3 bg-slate-950/40 rounded-xl border border-blue-500/10 text-[10px] text-slate-400 flex flex-col gap-2">
          <div className="flex justify-between items-center text-[9px] text-blue-500/80 font-bold uppercase tracking-wider mb-0.5">
            <span>Climate Parameter Variables</span>
            <span>Est. Feed Source</span>
          </div>
          <div className="flex justify-between items-center border-b border-blue-500/5 pb-1">
            <span className="flex items-center gap-1.5"><Thermometer className="w-3.5 h-3.5 text-amber-500" /> Temp Sensor</span>
            <span className="text-slate-300 font-bold text-glow-blue">Open-Meteo Live</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="flex items-center gap-1.5"><Droplets className="w-3.5 h-3.5 text-cyan-400" /> Precip & Humidity</span>
            <span className="text-slate-300 font-bold text-glow-blue">Open-Meteo Live</span>
          </div>
        </div>

        {/* Run Button */}
        <button
          type="submit"
          disabled={isPredicting}
          className="w-full bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/50 text-blue-200 hover:text-white font-bold py-2.5 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 cursor-pointer text-xs tracking-wider"
        >
          {isPredicting ? (
            <>
              <span className="animate-spin rounded-full h-4.5 w-4.5 border-2 border-blue-400 border-t-transparent" />
              <span>DIAGNOSING EPIDEMIOLOGY...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-blue-300 text-blue-300" />
              <span>RUN PREDICTION MODEL</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
