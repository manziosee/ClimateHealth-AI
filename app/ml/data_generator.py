import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

# Six climate profiles representing the major epidemiological zones.
# Each profile shapes the parameter distributions so that the training data
# includes the environments where each disease actually occurs.
_REGIONS = {
    # West Africa / SE Asia / Caribbean — malaria, dengue
    "tropical":  {"temp": (24, 38), "rain": (40, 350), "hum": (65, 100), "pop": (150, 2000), "uv": (8, 12),  "wind": (2, 15)},
    # Sahel / meningitis belt — meningitis, low-humidity diseases
    "sahelian":  {"temp": (18, 45), "rain": (0,  80),  "hum": (10, 55),  "pop": (20,  500),  "uv": (7, 12),  "wind": (5, 30)},
    # Europe / North America / East Asia — flu, pneumonia
    "temperate": {"temp": (-5, 28), "rain": (10, 150),  "hum": (40, 85),  "pop": (80,  1500), "uv": (1, 8),   "wind": (2, 20)},
    # South Asia / Bay of Bengal — monsoon cholera and dengue
    "monsoon":   {"temp": (22, 40), "rain": (0,  400),  "hum": (50, 100), "pop": (300, 2000), "uv": (5, 11),  "wind": (3, 20)},
    # Mediterranean / Middle East / North Africa — mixed
    "mediterr":  {"temp": (10, 38), "rain": (5,  120),  "hum": (30, 75),  "pop": (80,  1000), "uv": (4, 11),  "wind": (3, 18)},
    # Highland East Africa (Rwanda, Kenya, Ethiopia) — malaria, meningitis
    "highland":  {"temp": (10, 26), "rain": (20, 250),  "hum": (55, 95),  "pop": (40,  800),  "uv": (6, 12),  "wind": (2, 15)},
}

# How much each region contributes to training data per disease.
# Upweight regions where the disease is most prevalent.
_REGION_WEIGHTS: dict[str, list[float]] = {
    "malaria":    [0.30, 0.10, 0.05, 0.15, 0.10, 0.30],
    "flu":        [0.10, 0.05, 0.45, 0.10, 0.20, 0.10],
    "cholera":    [0.20, 0.10, 0.05, 0.40, 0.15, 0.10],
    "dengue":     [0.35, 0.05, 0.05, 0.30, 0.15, 0.10],
    "pneumonia":  [0.10, 0.10, 0.40, 0.15, 0.15, 0.10],
    "meningitis": [0.10, 0.40, 0.10, 0.10, 0.15, 0.15],
}


def _base_cases(disease, temp, rain, humidity, pop_density, month, uv, et0, wind) -> np.ndarray:
    n     = len(temp)
    noise = RNG.normal(0, 1, n)

    if disease == "malaria":
        cases = (
            0.30 * rain
            + 0.20 * humidity
            + 0.15 * temp
            + 0.007 * pop_density
            + 0.10 * uv
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
        flood   = np.where(rain > 100, 1.8, 1.0)
        drought = np.where(et0 > 5, 1.4, 1.0)
        cases = (
            0.40 * rain * flood
            + 0.012 * pop_density
            + 0.08 * humidity
            + 0.10 * et0 * drought
            + 4 * noise
        )
    elif disease == "dengue":
        urban = np.where(pop_density > 500, 1.5, 1.0)
        cases = (
            0.25 * rain
            + 0.25 * humidity
            + 0.20 * np.clip(temp - 20, 0, 15)
            + 0.008 * pop_density * urban
            + 0.12 * uv
            + 12 * np.sin(2 * np.pi * month / 12)
            + 4 * noise
        )
    elif disease == "pneumonia":
        cold_factor = np.clip(25 - temp, 0, 20)
        dry_factor  = np.clip(60 - humidity, 0, 40)
        cases = (
            0.45 * cold_factor
            + 0.20 * dry_factor
            + 0.010 * pop_density
            + 10 * np.cos(2 * np.pi * month / 12)
            + 4 * noise
        )
    elif disease == "meningitis":
        dry_season = np.clip(70 - humidity, 0, 50)
        no_rain    = np.clip(50 - rain, 0, 50)
        cases = (
            0.35 * dry_season
            + 0.25 * no_rain
            + 0.008 * pop_density
            + 0.15 * wind
            + 8 * np.cos(2 * np.pi * month / 12)
            + 3 * noise
        )
    else:
        cases = np.zeros(n)

    return np.clip(cases, 0, None).astype(int)


def generate(disease: str, n_samples: int = 15000) -> pd.DataFrame:
    regions      = list(_REGIONS.keys())
    weights      = _REGION_WEIGHTS.get(disease, [1/6]*6)
    weights_arr  = np.array(weights) / sum(weights)
    region_idx   = RNG.choice(len(regions), size=n_samples, p=weights_arr)

    temperature = np.zeros(n_samples)
    rainfall    = np.zeros(n_samples)
    humidity    = np.zeros(n_samples)
    uv_index    = np.zeros(n_samples)
    pop_density = np.zeros(n_samples)
    wind_speed  = np.zeros(n_samples)

    for i, region in enumerate(regions):
        mask = region_idx == i
        n    = int(mask.sum())
        if n == 0:
            continue
        r = _REGIONS[region]
        temperature[mask] = RNG.uniform(*r["temp"], n)
        rainfall[mask]    = RNG.uniform(*r["rain"], n)
        humidity[mask]    = RNG.uniform(*r["hum"],  n)
        uv_index[mask]    = RNG.uniform(*r["uv"],   n)
        pop_density[mask] = RNG.uniform(*r["pop"],  n)
        wind_speed[mask]  = RNG.uniform(*r["wind"], n)

    month           = RNG.integers(1, 13, n_samples)
    et0             = RNG.uniform(0, 10, n_samples)
    precip_prob     = RNG.uniform(0, 100, n_samples)
    apparent_temp   = temperature + RNG.uniform(-5, 5, n_samples)

    cases = _base_cases(disease, temperature, rainfall, humidity, pop_density,
                        month, uv_index, et0, wind_speed)

    return pd.DataFrame({
        "temperature":               temperature,
        "rainfall":                  rainfall,
        "humidity":                  humidity,
        "wind_speed":                wind_speed,
        "population_density":        pop_density,
        "month":                     month,
        "uv_index":                  uv_index,
        "et0_evapotranspiration":    et0,
        "precipitation_probability": precip_prob,
        "apparent_temperature":      apparent_temp,
        "cases":                     cases,
    })
