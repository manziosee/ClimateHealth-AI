import httpx
from app.core.config import settings

# World Bank V2 API — https://api.worldbank.org/v2/
# All calls require format=json, returns [metadata, [records]] list

INDICATORS = {
    "population_density":    "EN.POP.DNST",     # people per km²
    "urban_population_pct":  "SP.URB.TOTL.IN.ZS", # % urban
    "clean_water_access":    "SH.H2O.BASW.ZS",   # % basic drinking water
    "sanitation_access":     "SH.STA.BASS.ZS",   # % basic sanitation (cholera proxy)
    "age_dependency_ratio":  "SP.POP.DPND",      # age dependency (flu vulnerability)
    "hospital_beds":         "SH.MED.BEDS.ZS",   # hospital beds per 1000 (health capacity)
}


def _base_url() -> str:
    return settings.WORLD_BANK_BASE_URL


async def fetch_indicator(country_code: str, indicator: str) -> float | None:
    """
    Fetch latest available value for a World Bank indicator for a country.
    Uses mrv=1 (most recent value) to always get the latest data point.
    Docs: https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&mrv=1
    """
    url = f"{_base_url()}/country/{country_code}/indicator/{indicator}"
    params = {
        "format":   "json",
        "mrv":      1,          # most recent value only
        "per_page": 1,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
        except Exception:
            return None

    data = resp.json()
    # V2 returns [metadata_dict, [records_list]]
    if not isinstance(data, list) or len(data) < 2 or not data[1]:
        return None

    value = data[1][0].get("value")
    return float(value) if value is not None else None


async def fetch_country_features(country_code: str) -> dict:
    """
    Fetch all epidemiologically relevant World Bank indicators for a country.
    Returns dict — None for any indicator that's unavailable.
    Cached at the call site (predictions.py) for 24h per country.
    """
    results = {}
    for name, code in INDICATORS.items():
        results[name] = await fetch_indicator(country_code, code)
    return results


async def fetch_country_metadata(country_code: str) -> dict | None:
    """
    Fetch country metadata (name, region, income level, capital, coordinates).
    Docs: https://api.worldbank.org/v2/country/{code}?format=json
    """
    url = f"{_base_url()}/country/{country_code}"
    params = {"format": "json"}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
        except Exception:
            return None

    data = resp.json()
    if not isinstance(data, list) or len(data) < 2 or not data[1]:
        return None

    c = data[1][0]
    return {
        "name":         c.get("name"),
        "iso2":         c.get("iso2Code"),
        "iso3":         c.get("id"),
        "region":       c.get("region", {}).get("value"),
        "income_level": c.get("incomeLevel", {}).get("value"),
        "capital":      c.get("capitalCity"),
        "lat":          c.get("latitude"),
        "lon":          c.get("longitude"),
    }
