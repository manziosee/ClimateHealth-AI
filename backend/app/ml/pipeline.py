import numpy as np
import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input columns: temperature, rainfall, humidity, wind_speed, population_density, month
    Returns enriched feature dataframe ready for model input.
    """
    df = df.copy()

    # Cyclical month encoding to capture seasonality
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # Interaction features
    df["rain_humidity"]   = df["rainfall"] * df["humidity"] / 100
    df["temp_humidity"]   = df["temperature"] * df["humidity"] / 100
    df["rain_temp"]       = df["rainfall"] * df["temperature"]
    df["pop_rain"]        = df["population_density"] * df["rainfall"]

    # Risk proxies
    df["heat_index"]      = df["temperature"] + 0.33 * (df["humidity"] / 100 * 6.105) - 4.0
    df["flood_risk"]      = (df["rainfall"] > 100).astype(int)
    df["high_humidity"]   = (df["humidity"] > 75).astype(int)

    df.drop(columns=["month"], inplace=True)
    return df


FEATURE_COLUMNS = [
    "temperature", "rainfall", "humidity", "wind_speed", "population_density",
    "month_sin", "month_cos",
    "rain_humidity", "temp_humidity", "rain_temp", "pop_rain",
    "heat_index", "flood_risk", "high_humidity",
]


def prepare_input(temperature: float, rainfall: float, humidity: float,
                  wind_speed: float, population_density: float, month: int) -> pd.DataFrame:
    """Prepare a single prediction row."""
    df = pd.DataFrame([{
        "temperature": temperature,
        "rainfall": rainfall,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "population_density": population_density,
        "month": month,
    }])
    return engineer_features(df)[FEATURE_COLUMNS]
