import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)


def _base_cases(disease, temp, rain, humidity, pop_density, month, uv, et0, wind) -> np.ndarray:
    n     = len(temp)
    noise = RNG.normal(0, 1, n)

    if disease == "malaria":
        cases = (
            0.30 * rain
            + 0.20 * humidity
            + 0.15 * temp
            + 0.007 * pop_density
            + 0.10 * uv                                         # UV drives mosquito activity
            + 15 * np.sin(2 * np.pi * month / 12)
            + 5 * noise
        )
    elif disease == "flu":
        cold_factor = np.clip(30 - temp, 0, 20)
        cases = (
            0.50 * cold_factor
            + 0.15 * (100 - humidity)
            + 0.005 * pop_density
            + 10 * np.cos(2 * np.pi * month / 12)
            + 3 * noise
        )
    elif disease == "cholera":
        flood = np.where(rain > 100, 1.8, 1.0)
        drought = np.where(et0 > 5, 1.4, 1.0)                 # drought → water scarcity
        cases = (
            0.40 * rain * flood
            + 0.012 * pop_density
            + 0.08 * humidity
            + 0.10 * et0 * drought
            + 4 * noise
        )
    elif disease == "dengue":
        # Dengue: tropical, Aedes mosquito, warm/wet/humid, strong urban amplifier
        urban = np.where(pop_density > 500, 1.5, 1.0)
        cases = (
            0.25 * rain
            + 0.25 * humidity
            + 0.20 * np.clip(temp - 20, 0, 15)                # optimal 25-35°C
            + 0.008 * pop_density * urban
            + 0.12 * uv
            + 12 * np.sin(2 * np.pi * month / 12)
            + 4 * noise
        )
    elif disease == "pneumonia":
        # Pneumonia: cold/dry conditions, peaks in winter months
        cold_factor = np.clip(25 - temp, 0, 20)
        dry_factor  = np.clip(60 - humidity, 0, 40)
        cases = (
            0.45 * cold_factor
            + 0.20 * dry_factor
            + 0.010 * pop_density
            + 10 * np.cos(2 * np.pi * month / 12)             # peaks Dec-Feb
            + 4 * noise
        )
    elif disease == "meningitis":
        # Meningitis: dry season / Sahel belt; low humidity, no rain, dusty wind
        dry_season = np.clip(70 - humidity, 0, 50)
        no_rain    = np.clip(50 - rain, 0, 50)
        cases = (
            0.35 * dry_season
            + 0.25 * no_rain
            + 0.008 * pop_density
            + 0.15 * wind                                      # dust spread
            + 8 * np.cos(2 * np.pi * month / 12)              # peaks dry season
            + 3 * noise
        )
    else:
        cases = np.zeros(n)

    return np.clip(cases, 0, None).astype(int)


def generate(disease: str, n_samples: int = 8000) -> pd.DataFrame:
    month        = RNG.integers(1, 13, n_samples)
    temperature  = RNG.uniform(10, 40, n_samples)
    rainfall     = RNG.uniform(0, 350, n_samples)
    humidity     = RNG.uniform(20, 100, n_samples)
    wind_speed   = RNG.uniform(0, 30, n_samples)
    pop_density  = RNG.uniform(50, 2000, n_samples)
    uv_index     = RNG.uniform(0, 12, n_samples)
    et0          = RNG.uniform(0, 10, n_samples)
    precip_prob  = RNG.uniform(0, 100, n_samples)
    apparent_temp = temperature + RNG.uniform(-5, 5, n_samples)

    cases = _base_cases(disease, temperature, rainfall, humidity, pop_density, month, uv_index, et0, wind_speed)

    return pd.DataFrame({
        "temperature":              temperature,
        "rainfall":                 rainfall,
        "humidity":                 humidity,
        "wind_speed":               wind_speed,
        "population_density":       pop_density,
        "month":                    month,
        "uv_index":                 uv_index,
        "et0_evapotranspiration":   et0,
        "precipitation_probability": precip_prob,
        "apparent_temperature":     apparent_temp,
        "cases":                    cases,
    })
