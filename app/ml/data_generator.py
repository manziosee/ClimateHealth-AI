import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)


def _base_cases(disease, temp, rain, humidity, pop_density, month, uv, et0) -> np.ndarray:
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

    cases = _base_cases(disease, temperature, rainfall, humidity, pop_density, month, uv_index, et0)

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
