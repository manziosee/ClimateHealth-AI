import { PredictionResponse } from "./types";

export const mockPredictions: PredictionResponse[] = [
  {
    id: 1,
    lat: -1.9403,
    lon: 29.8739,
    location_name: "Kigali (Rwanda)",
    disease: "malaria",
    risk_level: "High",
    expected_cases: 145,
    confidence: 0.88,
    temperature: 28.2,
    rainfall: 210,
    humidity: 85,
    predicted_at: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 2,
    lat: -1.5015,
    lon: 30.0631,
    location_name: "Musanze District",
    disease: "malaria",
    risk_level: "Medium",
    expected_cases: 68,
    confidence: 0.74,
    temperature: 24.5,
    rainfall: 155,
    humidity: 78,
    predicted_at: new Date(Date.now() - 7200000).toISOString()
  },
  {
    id: 3,
    lat: -1.7003,
    lon: 29.2625,
    location_name: "Rubavu District",
    disease: "cholera",
    risk_level: "High",
    expected_cases: 42,
    confidence: 0.91,
    temperature: 26.8,
    rainfall: 180,
    humidity: 89,
    predicted_at: new Date(Date.now() - 14400000).toISOString()
  },
  {
    id: 4,
    lat: 1.2921,
    lon: 36.8219,
    location_name: "Nairobi (Kenya)",
    disease: "malaria",
    risk_level: "Medium",
    expected_cases: 85,
    confidence: 0.82,
    temperature: 23.1,
    rainfall: 98,
    humidity: 71,
    predicted_at: new Date(Date.now() - 28800000).toISOString()
  },
  {
    id: 5,
    lat: 51.5074,
    lon: -0.1278,
    location_name: "London (UK)",
    disease: "flu",
    risk_level: "High",
    expected_cases: 195,
    confidence: 0.94,
    temperature: 9.4,
    rainfall: 45,
    humidity: 82,
    predicted_at: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: 6,
    lat: 35.6762,
    lon: 139.6503,
    location_name: "Tokyo (Japan)",
    disease: "flu",
    risk_level: "Low",
    expected_cases: 23,
    confidence: 0.85,
    temperature: 15.2,
    rainfall: 12,
    humidity: 55,
    predicted_at: new Date(Date.now() - 172800000).toISOString()
  }
];
