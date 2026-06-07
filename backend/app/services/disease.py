import httpx
from app.core.config import settings

# Verified WHO GHO OData indicator codes
# Browse all: https://ghoapi.azureedge.net/api/Indicator
DISEASE_INDICATORS = {
    "malaria": "MALARIA_CASES",
    "cholera": "CHOLERA_0000000001",
    # Flu uses WHO FluNet — separate endpoint
}

FLUNET_URL = "https://services.who.int/flumart/Default?ReportNo=12"


async def fetch_disease_data(disease: str, country_code: str | None = None) -> list[dict]:
    """Fetch annual disease case data from WHO GHO API."""
    if disease == "flu":
        return await _fetch_flunet(country_code)

    indicator = DISEASE_INDICATORS.get(disease)
    if not indicator:
        return []

    url = f"{settings.WHO_BASE_URL}/{indicator}"
    params = {"$top": 500, "$orderby": "TimeDim desc"}
    if country_code:
        params["$filter"] = f"SpatialDim eq '{country_code}'"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    return [
        {
            "country": item.get("SpatialDim"),
            "year":    item.get("TimeDim"),
            "cases":   item.get("NumericValue"),
        }
        for item in resp.json().get("value", [])
        if item.get("NumericValue") is not None
    ]


async def _fetch_flunet(country_code: str | None) -> list[dict]:
    """
    Fetch influenza surveillance data from WHO FluNet.
    Returns weekly positive specimen counts by country.
    """
    params = {
        "outtype": "json",
        "ReportNo": 12,
    }
    if country_code:
        params["Abb"] = country_code

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                "https://services.who.int/flumart/Default",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    records = []
    for item in data.get("data", []):
        total = (item.get("ALL_INF") or 0)
        if total > 0:
            records.append({
                "country": item.get("COUNTRY_CODE"),
                "year":    item.get("ISO_YEAR"),
                "week":    item.get("ISO_WEEK"),
                "cases":   total,
            })
    return records
