"use client";

import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";
import { PredictionResponse } from "../app/types";

interface TrendsChartProps {
  predictions: PredictionResponse[];
}

export default function TrendsChart({ predictions }: TrendsChartProps) {
  // Take last 8 predictions sorted chronologically to draw the correlation trend
  const chartData = [...predictions]
    .sort((a, b) => new Date(a.predicted_at).getTime() - new Date(b.predicted_at).getTime())
    .slice(-8)
    .map((p, idx) => ({
      name: p.location_name ? p.location_name.split(" ")[0] : `Point ${idx + 1}`,
      cases: p.expected_cases,
      temp: p.temperature,
      rain: p.rainfall,
      humidity: p.humidity
    }));

  return (
    <div className="w-full h-[320px] bg-slate-950/40 border border-slate-800/80 p-5 rounded-2xl shadow-xl">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
          Climate-Disease Correlation Analyzer
        </h3>
        <span className="text-xs text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-full border border-slate-700/50">
          Last 8 Data Runs
        </span>
      </div>

      <div className="w-full h-[240px]">
        {chartData.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
            No forecasting data runs available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
              <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
              <YAxis yAxisId="left" stroke="#3b82f6" fontSize={10} tickLine={false} label={{ value: 'Expected Cases', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10, offset: 0 }} />
              <YAxis yAxisId="right" orientation="right" stroke="#ef4444" fontSize={10} tickLine={false} label={{ value: 'Temp (°C) / Rain (mm)', angle: 90, position: 'insideRight', fill: '#64748b', fontSize: 10, offset: 0 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(15, 23, 42, 0.95)",
                  borderColor: "rgba(51, 65, 85, 0.8)",
                  borderRadius: "12px",
                  fontSize: "12px"
                }}
                itemStyle={{ color: "#e2e8f0" }}
              />
              <Legend verticalAlign="top" height={36} iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Bar yAxisId="left" dataKey="rain" name="Rainfall (mm)" fill="#06b6d4" radius={[4, 4, 0, 0]} opacity={0.4} barSize={24} />
              <Line yAxisId="right" type="monotone" dataKey="temp" name="Temperature (°C)" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
              <Line yAxisId="left" type="monotone" dataKey="cases" name="Outbreak Cases" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
