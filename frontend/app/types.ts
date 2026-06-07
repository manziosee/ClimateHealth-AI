export interface PredictRequest {
  lat: number;
  lon: number;
  disease: "malaria" | "flu" | "cholera";
  population_density?: number;
}

export interface PredictionResponse {
  id?: number;
  lat: number;
  lon: number;
  location_name?: string | null;
  disease: "malaria" | "flu" | "cholera";
  risk_level: "Low" | "Medium" | "High";
  expected_cases: number;
  confidence: number;
  temperature: number;
  rainfall: number;
  humidity: number;
  predicted_at: string;
}

export interface WeatherResponse {
  lat: number;
  lon: number;
  temperature: number;
  rainfall: number;
  humidity: number;
  wind_speed: number;
  fetched_at: string;
}
