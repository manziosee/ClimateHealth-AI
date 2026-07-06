"""
Quick audit of all external API integrations and training data quality.
Run: python scripts/test_apis.py
"""
import asyncio
import httpx
import json


async def main():
    async with httpx.AsyncClient(timeout=15) as c:

        print("\n=== 1. Open-Meteo (current weather) ===")
        r = await c.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": -1.9403, "longitude": 29.8739,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max,et0_fao_evapotranspiration,precipitation_probability_max",
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
            "forecast_days": 1, "timezone": "auto",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"  Temp max: {d['daily']['temperature_2m_max'][0]}°C")
            print(f"  Humidity (current): {d['current']['relative_humidity_2m']}%")
            print(f"  Rainfall: {d['daily']['precipitation_sum'][0]}mm")
            print(f"  UV index: {d['daily']['uv_index_max'][0]}")
            print(f"  ET0: {d['daily']['et0_fao_evapotranspiration'][0]}mm")
        else:
            print(f"  FAIL: {r.text[:200]}")

        print("\n=== 2. Open-Meteo (7-day forecast) ===")
        r = await c.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": -1.9403, "longitude": 29.8739,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max",
            "forecast_days": 7, "timezone": "auto",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            days = r.json()["daily"]["time"]
            print(f"  Days returned: {len(days)} ({days[0]} to {days[-1]})")

        print("\n=== 3. Open-Meteo (archive) ===")
        r = await c.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": -1.9403, "longitude": 29.8739,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "start_date": "2023-01-01", "end_date": "2023-01-07", "timezone": "auto",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()["daily"]
            print(f"  Days returned: {len(d['time'])}, temps: {d['temperature_2m_max'][:3]}")

        print("\n=== 4. WHO GHO — MALARIA_CASES ===")
        r = await c.get("https://ghoapi.azureedge.net/api/MALARIA_CASES", params={
            "$top": 5, "$orderby": "TimeDim desc",
            "$select": "SpatialDim,TimeDim,NumericValue",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            vals = r.json().get("value", [])
            print(f"  Records returned: {len(vals)}")
            print(f"  Sample: {vals[:2]}")
        else:
            print(f"  FAIL body: {r.text[:300]}")

        print("\n=== 5. WHO GHO — CHOLERA_0000000001 ===")
        r = await c.get("https://ghoapi.azureedge.net/api/CHOLERA_0000000001", params={
            "$top": 5, "$orderby": "TimeDim desc",
            "$select": "SpatialDim,TimeDim,NumericValue",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            vals = r.json().get("value", [])
            print(f"  Records: {len(vals)}, sample: {vals[:2]}")
        else:
            print(f"  FAIL body: {r.text[:300]}")

        print("\n=== 6. WHO GHO — MENING_2 ===")
        r = await c.get("https://ghoapi.azureedge.net/api/MENING_2", params={
            "$top": 5, "$orderby": "TimeDim desc",
            "$select": "SpatialDim,TimeDim,NumericValue",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            vals = r.json().get("value", [])
            print(f"  Records: {len(vals)}, sample: {vals[:2]}")
        else:
            print(f"  FAIL body: {r.text[:300]}")

        print("\n=== 7. WHO GHO — RSUD_INFLUENZA (flu) ===")
        r = await c.get("https://ghoapi.azureedge.net/api/RSUD_INFLUENZA", params={
            "$top": 5, "$orderby": "TimeDim desc",
            "$select": "SpatialDim,TimeDim,NumericValue",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            vals = r.json().get("value", [])
            print(f"  Records: {len(vals)}, sample: {vals[:2]}")
        else:
            print(f"  FAIL body: {r.text[:300]}")

        print("\n=== 8. WHO GHO — find dengue indicator ===")
        r = await c.get("https://ghoapi.azureedge.net/api/Indicator", params={
            "$filter": "contains(IndicatorName,'engue')",
            "$select": "IndicatorCode,IndicatorName",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            for item in r.json().get("value", [])[:5]:
                print(f"  {item['IndicatorCode']} | {item['IndicatorName'][:80]}")

        print("\n=== 9. WHO GHO — find pneumonia indicator ===")
        r = await c.get("https://ghoapi.azureedge.net/api/Indicator", params={
            "$filter": "contains(IndicatorName,'neumonia')",
            "$select": "IndicatorCode,IndicatorName",
        })
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            for item in r.json().get("value", [])[:5]:
                print(f"  {item['IndicatorCode']} | {item['IndicatorName'][:80]}")

        print("\n=== 10. World Bank — population density (Rwanda) ===")
        r = await c.get("https://api.worldbank.org/v2/country/RW/indicator/EN.POP.DNST",
                        params={"format": "json", "mrv": 1, "per_page": 1})
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            val = d[1][0].get("value") if isinstance(d, list) and len(d) > 1 and d[1] else None
            print(f"  Pop density RW: {val} people/km²")

        print("\n=== 11. World Bank — sanitation access ===")
        r = await c.get("https://api.worldbank.org/v2/country/RW/indicator/SH.STA.BASS.ZS",
                        params={"format": "json", "mrv": 1, "per_page": 1})
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            val = d[1][0].get("value") if isinstance(d, list) and len(d) > 1 and d[1] else None
            print(f"  Sanitation access RW: {val}%")

        print("\n=== 12. Nominatim reverse geocode ===")
        r = await c.get("https://nominatim.openstreetmap.org/reverse",
                        params={"lat": -1.9403, "lon": 29.8739, "format": "json"},
                        headers={"User-Agent": "ClimateHealthAI/1.0"})
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            a = r.json().get("address", {})
            city = a.get("city") or a.get("town") or a.get("village")
            print(f"  City: {city}, country_code: {a.get('country_code')}")

        print("\n=== 13. Open-Meteo Geocoding ===")
        r = await c.get("https://geocoding-api.open-meteo.com/v1/search",
                        params={"name": "Nairobi", "count": 3, "language": "en"})
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            results = r.json().get("results", [])
            print(f"  Results: {[(x.get('name'), x.get('country')) for x in results]}")


asyncio.run(main())
