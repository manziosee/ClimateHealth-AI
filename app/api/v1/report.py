"""
Country risk report — GET /api/v1/report/{country_code}

Returns an all-diseases risk snapshot for a country using its capital city
as the reference coordinate. Runs 6 disease predictions in one call.
Cached 1 hour per country.
"""
import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.core.database import get_db
from app.services import weather as weather_svc
from app.services import predictor
from app.api.v1.predictions import _resolve_population_density, _build_predict_kwargs
from app.api.v1.alerts import _action

router = APIRouter(prefix="/report", tags=["report"])

_DISEASES = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]

# ISO 3166-1 alpha-3 → (country_name, capital, lat, lon)
_COUNTRIES: dict[str, tuple[str, str, float, float]] = {
    "AFG": ("Afghanistan",              "Kabul",            34.53,   69.17),
    "AGO": ("Angola",                   "Luanda",           -8.84,   13.23),
    "ARG": ("Argentina",                "Buenos Aires",    -34.61,  -58.37),
    "AUS": ("Australia",                "Canberra",        -35.28,  149.13),
    "BDI": ("Burundi",                  "Gitega",           -3.43,   29.93),
    "BEN": ("Benin",                    "Porto-Novo",        6.37,    2.42),
    "BFA": ("Burkina Faso",             "Ouagadougou",      12.37,   -1.53),
    "BGD": ("Bangladesh",               "Dhaka",            23.72,   90.41),
    "BOL": ("Bolivia",                  "La Paz",          -16.50,  -68.15),
    "BRA": ("Brazil",                   "Brasilia",        -15.79,  -47.89),
    "CAF": ("Central African Republic", "Bangui",            4.36,   18.55),
    "CIV": ("Cote d'Ivoire",            "Yamoussoukro",      6.82,   -5.28),
    "CMR": ("Cameroon",                 "Yaounde",           3.87,   11.52),
    "COD": ("DR Congo",                 "Kinshasa",         -4.32,   15.32),
    "COG": ("Republic of Congo",        "Brazzaville",      -4.27,   15.28),
    "COL": ("Colombia",                 "Bogota",            4.71,  -74.07),
    "DEU": ("Germany",                  "Berlin",           52.52,   13.41),
    "EGY": ("Egypt",                    "Cairo",            30.06,   31.25),
    "ETH": ("Ethiopia",                 "Addis Ababa",       9.03,   38.74),
    "FRA": ("France",                   "Paris",            48.85,    2.35),
    "GBR": ("United Kingdom",           "London",           51.51,   -0.13),
    "GHA": ("Ghana",                    "Accra",             5.56,   -0.20),
    "GIN": ("Guinea",                   "Conakry",           9.54,  -13.68),
    "GTM": ("Guatemala",                "Guatemala City",   14.64,  -90.51),
    "HND": ("Honduras",                 "Tegucigalpa",      14.10,  -87.20),
    "HTI": ("Haiti",                    "Port-au-Prince",   18.54,  -72.34),
    "IDN": ("Indonesia",                "Jakarta",          -6.21,  106.85),
    "IND": ("India",                    "New Delhi",        28.61,   77.21),
    "IRN": ("Iran",                     "Tehran",           35.69,   51.42),
    "IRQ": ("Iraq",                     "Baghdad",          33.34,   44.40),
    "KEN": ("Kenya",                    "Nairobi",          -1.29,   36.82),
    "KHM": ("Cambodia",                 "Phnom Penh",       11.57,  104.92),
    "LAO": ("Laos",                     "Vientiane",        17.97,  102.60),
    "LBR": ("Liberia",                  "Monrovia",          6.30,  -10.80),
    "LKA": ("Sri Lanka",                "Colombo",           6.93,   79.85),
    "MDG": ("Madagascar",               "Antananarivo",    -18.91,   47.54),
    "MEX": ("Mexico",                   "Mexico City",      19.43,  -99.13),
    "MLI": ("Mali",                     "Bamako",           12.65,   -8.00),
    "MOZ": ("Mozambique",               "Maputo",          -25.97,   32.59),
    "MRT": ("Mauritania",               "Nouakchott",       18.08,  -15.97),
    "MWI": ("Malawi",                   "Lilongwe",        -13.97,   33.79),
    "MYS": ("Malaysia",                 "Kuala Lumpur",      3.15,  101.70),
    "NER": ("Niger",                    "Niamey",           13.51,    2.12),
    "NGA": ("Nigeria",                  "Abuja",             9.08,    7.40),
    "NPL": ("Nepal",                    "Kathmandu",        27.72,   85.32),
    "PAK": ("Pakistan",                 "Islamabad",        33.69,   73.06),
    "PER": ("Peru",                     "Lima",            -12.05,  -77.05),
    "PHL": ("Philippines",              "Manila",           14.60,  120.98),
    "PNG": ("Papua New Guinea",         "Port Moresby",     -9.44,  147.18),
    "PRY": ("Paraguay",                 "Asuncion",        -25.29,  -57.65),
    "RWA": ("Rwanda",                   "Kigali",           -1.95,   30.06),
    "SDN": ("Sudan",                    "Khartoum",         15.55,   32.53),
    "SEN": ("Senegal",                  "Dakar",            14.69,  -17.45),
    "SLE": ("Sierra Leone",             "Freetown",          8.49,  -13.23),
    "SOM": ("Somalia",                  "Mogadishu",         2.05,   45.34),
    "SSD": ("South Sudan",              "Juba",              4.86,   31.57),
    "TCD": ("Chad",                     "N'Djamena",        12.11,   15.04),
    "TGO": ("Togo",                     "Lome",              6.14,    1.22),
    "THA": ("Thailand",                 "Bangkok",          13.75,  100.52),
    "TZA": ("Tanzania",                 "Dodoma",           -6.18,   35.74),
    "UGA": ("Uganda",                   "Kampala",           0.32,   32.58),
    "USA": ("United States",            "Washington D.C.",  38.91,  -77.04),
    "VEN": ("Venezuela",                "Caracas",          10.49,  -66.88),
    "VNM": ("Vietnam",                  "Hanoi",            21.03,  105.85),
    "YEM": ("Yemen",                    "Sana'a",           15.35,   44.21),
    "ZAF": ("South Africa",             "Pretoria",        -25.73,   28.22),
    "ZMB": ("Zambia",                   "Lusaka",          -15.42,   28.28),
    "ZWE": ("Zimbabwe",                 "Harare",          -17.83,   31.05),
}

# ISO 3166-1 alpha-3 → alpha-2 (World Bank API uses alpha-2)
_ALPHA2: dict[str, str] = {
    "AFG": "AF", "AGO": "AO", "ARG": "AR", "AUS": "AU",
    "BDI": "BI", "BEN": "BJ", "BFA": "BF", "BGD": "BD",
    "BOL": "BO", "BRA": "BR", "CAF": "CF", "CIV": "CI",
    "CMR": "CM", "COD": "CD", "COG": "CG", "COL": "CO",
    "DEU": "DE", "EGY": "EG", "ETH": "ET", "FRA": "FR",
    "GBR": "GB", "GHA": "GH", "GIN": "GN", "GTM": "GT",
    "HND": "HN", "HTI": "HT", "IDN": "ID", "IND": "IN",
    "IRN": "IR", "IRQ": "IQ", "KEN": "KE", "KHM": "KH",
    "LAO": "LA", "LBR": "LR", "LKA": "LK", "MDG": "MG",
    "MEX": "MX", "MLI": "ML", "MOZ": "MZ", "MRT": "MR",
    "MWI": "MW", "MYS": "MY", "NER": "NE", "NGA": "NG",
    "NPL": "NP", "PAK": "PK", "PER": "PE", "PHL": "PH",
    "PNG": "PG", "PRY": "PY", "RWA": "RW", "SDN": "SD",
    "SEN": "SN", "SLE": "SL", "SOM": "SO", "SSD": "SS",
    "TCD": "TD", "TGO": "TG", "THA": "TH", "TZA": "TZ",
    "UGA": "UG", "USA": "US", "VEN": "VE", "VNM": "VN",
    "YEM": "YE", "ZAF": "ZA", "ZMB": "ZM", "ZWE": "ZW",
}


class DiseaseRisk(BaseModel):
    disease: str
    risk_level: str
    expected_cases: int
    confidence: float
    recommended_action: str
    top_driver: str | None


class CountryReportResponse(BaseModel):
    country_code: str
    country_name: str
    capital: str
    lat: float
    lon: float
    temperature: float
    rainfall: float
    humidity: float
    diseases: list[DiseaseRisk]
    high_risk_count: int
    medium_risk_count: int
    overall_alert: bool
    supported_countries: int
    generated_at: datetime


@router.get("/countries", summary="List all supported country codes")
async def list_countries():
    """Return every supported ISO 3166-1 alpha-3 code and country name."""
    return {
        "count": len(_COUNTRIES),
        "countries": [
            {"code": code, "name": name, "capital": capital}
            for code, (name, capital, _, _) in sorted(_COUNTRIES.items(), key=lambda x: x[1][0])
        ],
    }


@router.get("/{country_code}", response_model=CountryReportResponse)
async def country_risk_report(
    country_code: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    **Full-country disease risk snapshot** — all 6 diseases in one call.

    Uses the country's capital city as the reference point for weather and
    population density. Returns risk levels, expected cases, and the
    recommended public health action for each disease.

    Country codes are **ISO 3166-1 alpha-3** (e.g. `RWA`, `KEN`, `NGA`, `IND`).
    Call `GET /api/v1/report/countries` for the full supported list.
    Results are cached **1 hour** per country.
    """
    cc = country_code.upper()
    if cc not in _COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Country '{cc}' not found. "
                "Use ISO 3166-1 alpha-3 codes — call /api/v1/report/countries for the full list."
            ),
        )

    cache_key = f"report:{cc}"
    cached = await redis.get(cache_key)
    if cached:
        return CountryReportResponse(**json.loads(cached))

    country_name, capital, lat, lon = _COUNTRIES[cc]

    weather     = await weather_svc.fetch_weather(lat, lon)
    pop_density = await _resolve_population_density(None, _ALPHA2.get(cc, cc), redis)

    disease_risks: list[DiseaseRisk] = []
    for disease in _DISEASES:
        result     = predictor.predict(**_build_predict_kwargs(weather, pop_density, disease))
        fi         = result.get("feature_importance") or {}
        top_driver = max(fi, key=fi.get) if fi else None

        disease_risks.append(DiseaseRisk(
            disease=disease,
            risk_level=result["risk_level"],
            expected_cases=result["expected_cases"],
            confidence=result["confidence"],
            recommended_action=_action(disease, result["risk_level"]),
            top_driver=top_driver.replace("_", " ").title() if top_driver else None,
        ))

    high_count   = sum(1 for d in disease_risks if d.risk_level == "High")
    medium_count = sum(1 for d in disease_risks if d.risk_level == "Medium")

    response = CountryReportResponse(
        country_code=cc,
        country_name=country_name,
        capital=capital,
        lat=lat,
        lon=lon,
        temperature=weather["temperature"],
        rainfall=weather["rainfall"],
        humidity=weather["humidity"],
        diseases=disease_risks,
        high_risk_count=high_count,
        medium_risk_count=medium_count,
        overall_alert=high_count > 0,
        supported_countries=len(_COUNTRIES),
        generated_at=datetime.now(timezone.utc),
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


# ─── Batch Country Report ─────────────────────────────────────────────────────

class BatchReportRequest(BaseModel):
    country_codes: list[str] = Field(..., min_length=1, max_length=10)


class BatchReportResponse(BaseModel):
    requested: int
    results: list[CountryReportResponse]
    errors: dict[str, str]
    generated_at: datetime


@router.post("/batch", response_model=BatchReportResponse)
async def batch_country_report(
    body: BatchReportRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    **Batch country risk reports** — up to 10 countries in one request.

    Runs all 6 disease predictions per country in parallel. Countries not in the
    supported list are returned in the `errors` map instead of raising 422.
    Results for valid countries are identical to `GET /report/{country_code}`.
    """
    async def _fetch_one(cc: str):
        try:
            result = await country_risk_report(cc, db=db, redis=redis)
            return cc, result, None
        except HTTPException as exc:
            return cc, None, exc.detail
        except Exception as exc:
            return cc, None, str(exc)

    tasks = [_fetch_one(code.upper()) for code in body.country_codes]
    outcomes = await asyncio.gather(*tasks)

    results, errors = [], {}
    for cc, report, err in outcomes:
        if err:
            errors[cc] = err
        else:
            results.append(report)

    return BatchReportResponse(
        requested=len(body.country_codes),
        results=results,
        errors=errors,
        generated_at=datetime.now(timezone.utc),
    )
