import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)


def _base_cases(disease: str, temp, rain, humidity, pop_density, month) -> np.ndarray:
    n = len(temp)
    noise = RNG.normal(0, 1, n)

    if disease == "malaria":
        # Peaks in warm, rainy, humid months (typical tropical pattern)
        cases = (
            0.35 * rain
            + 0.25 * humidity
            + 0.20 * temp
            + 0.008 * pop_density
            + 15 * np.sin(2 * np.pi * month / 12)   # seasonal peak ~month 4-6
            + 5 * noise
        )

    elif disease == "flu":
        # Peaks in cold, dry months
        cold_factor = np.clip(30 - temp, 0, 20)
        cases = (
            0.50 * cold_factor
            + 0.15 * (100 - humidity)
            + 0.005 * pop_density
            + 10 * np.cos(2 * np.pi * month / 12)   # seasonal peak ~month 1 & 12
            + 3 * noise
        )

    elif disease == "cholera":
        # Peaks after heavy rainfall + high density (flooding + poor sanitation)
        flood = np.where(rain > 100, 1.8, 1.0)
        cases = (
            0.45 * rain * flood
            + 0.012 * pop_density
            + 0.10 * humidity
            + 4 * noise
        )

    else:
        cases = np.zeros(n)

    return np.clip(cases, 0, None).astype(int)


def generate(disease: str, n_samples: int = 5000) -> pd.DataFrame:
    month        = RNG.integers(1, 13, n_samples)
    temperature  = RNG.uniform(10, 40, n_samples)
    rainfall     = RNG.uniform(0, 350, n_samples)
    humidity     = RNG.uniform(20, 100, n_samples)
    wind_speed   = RNG.uniform(0, 30, n_samples)
    pop_density  = RNG.uniform(50, 2000, n_samples)

    cases = _base_cases(disease, temperature, rainfall, humidity, pop_density, month)

    return pd.DataFrame({
        "temperature":      temperature,
        "rainfall":         rainfall,
        "humidity":         humidity,
        "wind_speed":       wind_speed,
        "population_density": pop_density,
        "month":            month,
        "cases":            cases,
    })
