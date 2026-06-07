"use client";

import { ShieldAlert, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { PredictionResponse } from "../app/types";

interface AlertsPanelProps {
  predictions: PredictionResponse[];
  onSelectPrediction: (p: PredictionResponse) => void;
  selectedPrediction?: PredictionResponse | null;
}

export default function AlertsPanel({
  predictions,
  onSelectPrediction,
  selectedPrediction
}: AlertsPanelProps) {
  return (
    <div className="cyber-panel p-5 rounded-2xl relative shadow-xl flex flex-col h-full font-mono">
      {/* Cyber Corners */}
      <div className="cyber-corner cyber-corner-tl" />
      <div className="cyber-corner cyber-corner-tr" />
      <div className="cyber-corner cyber-corner-bl" />
      <div className="cyber-corner cyber-corner-br" />

      <div className="mb-4 border-b border-blue-500/20 pb-3">
        <h3 className="text-xs font-bold text-red-400 uppercase tracking-widest flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-500 animate-pulse" /> [ SENSOR ALARMS FEED ]
        </h3>
        <p className="text-[10px] text-slate-500 mt-1">
          Active alarms generated globally by pathogen risk.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto max-h-[380px] pr-1 space-y-2.5 custom-scrollbar text-[10px]">
        {predictions.length === 0 ? (
          <div className="text-center text-slate-500 py-8">
            SYSTEM STANDBY - NO ALERTS RECORDED
          </div>
        ) : (
          predictions.map((p, idx) => {
            const isSelected = selectedPrediction?.id === p.id || (!selectedPrediction && idx === 0);
            const isHigh = p.risk_level === "High";
            const isMedium = p.risk_level === "Medium";

            const riskBorder = isHigh
              ? "border-red-500/45 text-red-200 bg-red-950/20"
              : isMedium
              ? "border-amber-500/40 text-amber-200 bg-amber-950/20"
              : "border-cyan-500/40 text-cyan-200 bg-cyan-950/15";

            const riskPulse = isHigh
              ? "text-red-500 animate-pulse text-glow-red"
              : isMedium
              ? "text-amber-500 text-glow-amber"
              : "text-cyan-400 text-glow-cyan";

            return (
              <div
                key={p.id || idx}
                onClick={() => onSelectPrediction(p)}
                className={`p-3 rounded-xl border transition-all duration-200 cursor-pointer flex gap-3 ${riskBorder} ${
                  isSelected ? "ring-1 ring-blue-500 scale-[1.01]" : "hover:border-slate-700/60"
                }`}
              >
                {/* Outbreak Indicator Icon */}
                <div className="flex items-start justify-center pt-0.5">
                  {isHigh ? (
                    <ShieldAlert className="w-3.5 h-3.5 text-red-500 shrink-0" />
                  ) : isMedium ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  ) : (
                    <CheckCircle className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  )}
                </div>

                {/* Log Text */}
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start gap-1">
                    <span className="font-extrabold truncate uppercase tracking-wider">
                      {p.location_name || `SEC-LOC [${p.lat.toFixed(1)}, ${p.lon.toFixed(1)}]`}
                    </span>
                    <span className="text-slate-500 shrink-0 flex items-center gap-1 text-[9px]">
                      <Clock className="w-3 h-3" />
                      {new Date(p.predicted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mt-1">
                    Risk Assessment: <span className={`font-bold ${riskPulse}`}>{p.risk_level.toUpperCase()}</span>
                  </p>
                  <p className="text-slate-400 mt-0.5 leading-relaxed">
                    Forecast: <span className="font-bold text-white">{p.expected_cases}</span> cases of{" "}
                    <span className="font-bold text-blue-400 uppercase">{p.disease}</span> ({Math.round(p.confidence * 100)}% reliability).
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
