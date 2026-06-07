import httpx

BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "population_density":  "EN.POP.DNST",
    "urban_population_pct": "SP.URB.TOTL.IN.ZS",
    "clean_water_access":  "SH.H2O.BASW.ZS",   # % with basic drinking water
    "sanitation_access":   "SH.STA.BASS.ZS",    # % with basic sanitation — key for cholera
}


async def fetch_indicator(country_code: str, indicator: str) -> float | None:
    """Fetch latest available value for a World Bank indicator."""
    url = f"{BASE}/country/{country_code}/indicator/{indicator}"
    params = {"format": "json", "mrv": 1, "per_page": 1}  # mrv=1 → most recent value

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return None

    data = resp.json()
    if not isinstance(data, list) or len(data) < 2:
        return None

    records = data[1]
    if records and records[0].get("value") is not None:
        return float(records[0]["value"])
    return None


async def fetch_country_features(country_code: str) -> dict:
    """
    Fetch all relevant World Bank features for a country.
    Returns dict with available indicators, None for unavailable ones.
    """
    results = {}
    for name, code in INDICATORS.items():
        results[name] = await fetch_indicator(country_code, code)
    return results
