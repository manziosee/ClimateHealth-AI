import httpx
from app.core.config import settings

# Verified indicator codes from https://ghoapi.azureedge.net/api/Indicator
# Search: https://ghoapi.azureedge.net/api/Indicator?$filter=contains(IndicatorName,'Malaria')
DISEASE_INDICATORS = {
    "malaria": "MALARIA_CASES",          # Reported malaria cases
    "cholera": "CHOLERA_0000000001",     # Number of reported cases of cholera
}

# GHO OData query params
_TOP = 500


async def fetch_disease_data(disease: str, country_code: str | None = None) -> list[dict]:
    """
    Fetch annual disease surveillance data from WHO GHO OData API.
    Docs: https://ghoapi.azureedge.net/api/
    For flu, falls back to GHO influenza indicator.
    """
    if disease == "flu":
        return await _fetch_gho_flu(country_code)

    indicator = DISEASE_INDICATORS.get(disease)
    if not indicator:
        return []

    url = f"{settings.WHO_BASE_URL}/{indicator}"

    # Build OData filter
    filters = []
    if country_code:
        filters.append(f"SpatialDim eq '{country_code.upper()}'")

    params: dict = {
        "$top":     _TOP,
        "$orderby": "TimeDim desc",
        "$select":  "SpatialDim,TimeDim,NumericValue,Low,High",
    }
    if filters:
        params["$filter"] = " and ".join(filters)

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    return [
        {
            "country": item.get("SpatialDim"),
            "year":    item.get("TimeDim"),
            "cases":   item.get("NumericValue"),
            "low":     item.get("Low"),
            "high":    item.get("High"),
        }
        for item in resp.json().get("value", [])
        if item.get("NumericValue") is not None
    ]


async def _fetch_gho_flu(country_code: str | None) -> list[dict]:
    """
    Fetch influenza data from WHO GHO.
    Indicator: RSUD_INFLUENZA — Influenza-like illness consultation rate
    Fallback: returns empty list gracefully if unavailable.
    """
    url = f"{settings.WHO_BASE_URL}/RSUD_INFLUENZA"
    params: dict = {
        "$top":     _TOP,
        "$orderby": "TimeDim desc",
        "$select":  "SpatialDim,TimeDim,NumericValue",
    }
    if country_code:
        params["$filter"] = f"SpatialDim eq '{country_code.upper()}'"

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
        except Exception:
            return []

    return [
        {
            "country": item.get("SpatialDim"),
            "year":    item.get("TimeDim"),
            "cases":   item.get("NumericValue"),
        }
        for item in resp.json().get("value", [])
        if item.get("NumericValue") is not None
    ]


async def search_indicators(keyword: str) -> list[dict]:
    """
    Search WHO GHO indicator catalogue by keyword.
    Useful for discovering new disease indicators.
    Example: search_indicators('malaria')
    """
    url = f"{settings.WHO_BASE_URL}/Indicator"
    params = {"$filter": f"contains(IndicatorName,'{keyword}')"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    return [
        {"code": i.get("IndicatorCode"), "name": i.get("IndicatorName")}
        for i in resp.json().get("value", [])
    ]
