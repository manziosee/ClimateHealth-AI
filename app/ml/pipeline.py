import numpy as np
import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input columns: temperature, rainfall, humidity, wind_speed, population_density,
                   month, uv_index, et0_evapotranspiration, precipitation_probability,
                   apparent_temperature (all optional except core 5)
    Returns enriched feature dataframe ready for model input.
    """
    df = df.copy()

    # Fill optional columns with sensible defaults if absent
    if "uv_index" not in df.columns:
        df["uv_index"] = 0.0
    if "et0_evapotranspiration" not in df.columns:
        df["et0_evapotranspiration"] = 0.0
    if "precipitation_probability" not in df.columns:
        df["precipitation_probability"] = 0.0
    if "apparent_temperature" not in df.columns:
        df["apparent_temperature"] = df["temperature"]

    # Cyclical month encoding
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # Core interaction features
    df["rain_humidity"]  = df["rainfall"] * df["humidity"] / 100
    df["temp_humidity"]  = df["temperature"] * df["humidity"] / 100
    df["rain_temp"]      = df["rainfall"] * df["temperature"]
    df["pop_rain"]       = df["population_density"] * df["rainfall"]

    # Risk proxies
    df["heat_index"]     = df["temperature"] + 0.33 * (df["humidity"] / 100 * 6.105) - 4.0
    df["flood_risk"]     = (df["rainfall"] > 100).astype(int)
    df["high_humidity"]  = (df["humidity"] > 75).astype(int)

    # New environmental features
    df["high_uv"]        = (df["uv_index"] > 7).astype(int)      # malaria: mosquito activity
    df["uv_temp"]        = df["uv_index"] * df["temperature"]     # heat + UV interaction
    df["drought_stress"] = (df["et0_evapotranspiration"] > 5).astype(int)  # cholera: water scarcity
    df["rain_prob_rain"] = df["precipitation_probability"] * df["rainfall"] / 100
    df["feels_like_diff"] = df["apparent_temperature"] - df["temperature"]  # wind chill proxy

    df.drop(columns=["month"], inplace=True)
    return df


FEATURE_COLUMNS = [
    # Core
    "temperature", "rainfall", "humidity", "wind_speed", "population_density",
    # Cyclical
    "month_sin", "month_cos",
    # Interactions
    "rain_humidity", "temp_humidity", "rain_temp", "pop_rain",
    # Risk proxies
    "heat_index", "flood_risk", "high_humidity",
    # New weather features
    "uv_index", "high_uv", "uv_temp",
    "et0_evapotranspiration", "drought_stress",
    "precipitation_probability", "rain_prob_rain",
    "apparent_temperature", "feels_like_diff",
]


def prepare_input(
    temperature: float,
    rainfall: float,
    humidity: float,
    wind_speed: float,
    population_density: float,
    month: int,
    uv_index: float = 0.0,
    et0_evapotranspiration: float = 0.0,
    precipitation_probability: float = 0.0,
    apparent_temperature: float | None = None,
) -> pd.DataFrame:
    """Prepare a single prediction row with all available features."""
    df = pd.DataFrame([{
        "temperature":              temperature,
        "rainfall":                 rainfall,
        "humidity":                 humidity,
        "wind_speed":               wind_speed,
        "population_density":       population_density,
        "month":                    month,
        "uv_index":                 uv_index,
        "et0_evapotranspiration":   et0_evapotranspiration,
        "precipitation_probability": precipitation_probability,
        "apparent_temperature":     apparent_temperature if apparent_temperature is not None else temperature,
    }])
    return engineer_features(df)[FEATURE_COLUMNS]
