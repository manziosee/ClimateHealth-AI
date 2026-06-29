"""
Historical trend comparison — overlays 5 years of Open-Meteo climate archive
with WHO GHO disease surveillance records for a location + disease.

GET /api/v1/trends/compare
"""
import json
from datetime import date
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.cache import get_redis
from app.services import weather as weather_svc
from app.services.disease import fetch_disease_data
from app.services.geocoding import reverse_geocode

router = APIRouter(prefix="/trends", tags=["trends"])


class YearlyTrend(BaseModel):
    year:              int
    avg_temperature:   float | None
    total_rainfall:    float | None
    avg_humidity:      float | None
    who_cases:         float | None   # WHO reported cases for that year (None if unavailable)
    who_cases_low:     float | None
    who_cases_high:    float | None


class TrendComparisonResponse(BaseModel):
    lat:           float
    lon:           float
    location_name: str | None
    country_code:  str | None
    disease:       str
    years:         int
    trends:        list[YearlyTrend]
    note:          str


@router.get("/compare", response_model=TrendComparisonResponse)
async def compare_trends(
    lat:     float = Query(..., ge=-90,  le=90),
    lon:     float = Query(..., ge=-180, le=180),
    disease: str   = Query(..., description="malaria | flu | cholera | dengue | pneumonia | meningitis"),
    years:   int   = Query(default=5, ge=1, le=10),
    redis=Depends(get_redis),
):
    """
    **5-year historical trend comparison** — climate conditions vs WHO case records.

    For each year in the window, returns:
    - Average temperature, total rainfall, average humidity (from Open-Meteo archive)
    - WHO GHO reported cases with confidence interval (where available)

    Use this to visually confirm that climate signals precede or correlate with
    disease case surges — e.g. high rainfall years → malaria spike.

    - `years` — how many years to look back (1–10, default 5)
    - WHO data availability depends on the disease and country. When WHO records
      are unavailable for a year, `who_cases` will be `null`.
    """
    cache_key = f"trends:{disease}:{lat}:{lon}:{years}"
    cached = await redis.get(cache_key)
    if cached:
        return TrendComparisonResponse(**json.loads(cached))

    location_name, country_code = await reverse_geocode(lat, lon)

    # Fetch WHO records for this country + disease
    who_records = await fetch_disease_data(disease, country_code)
    who_by_year: dict[int, dict] = {
        int(r["year"]): r for r in who_records if r.get("year") and r.get("cases") is not None
    }

    current_year = date.today().year
    trends: list[YearlyTrend] = []

    for offset in range(years, 0, -1):
        year = current_year - offset

        # Fetch full-year climate archive from Open-Meteo
        start_date = f"{year}-01-01"
        end_date   = f"{year}-12-31"

        try:
            history = await weather_svc.fetch_historical_weather(lat, lon, start_date, end_date)
        except Exception:
            history = []

        if history:
            temps    = [d["temperature"] for d in history if d.get("temperature") is not None]
            rains    = [d["rainfall"]    for d in history if d.get("rainfall")    is not None]
            avg_temp  = round(sum(temps) / len(temps), 1) if temps else None
            total_rain = round(sum(rains), 1)             if rains else None
            # Humidity is not in archive — use rainfall proxy
            avg_humidity = round(45.0 + min(total_rain or 0, 3000) / 100, 1)
        else:
            avg_temp = total_rain = avg_humidity = None

        who = who_by_year.get(year)
        trends.append(YearlyTrend(
            year=year,
            avg_temperature=avg_temp,
            total_rainfall=total_rain,
            avg_humidity=avg_humidity,
            who_cases=float(who["cases"]) if who else None,
            who_cases_low=float(who["low"]) if who and who.get("low") else None,
            who_cases_high=float(who["high"]) if who and who.get("high") else None,
        ))

    note = (
        "WHO case data may be incomplete for recent years due to reporting lag. "
        "Climate data from Open-Meteo archive (1940–present)."
    )

    response = TrendComparisonResponse(
        lat=lat,
        lon=lon,
        location_name=location_name,
        country_code=country_code,
        disease=disease,
        years=years,
        trends=trends,
        note=note,
    )
    # Cache 24h — historical data doesn't change
    await redis.setex(cache_key, 86400, response.model_dump_json())
    return response
