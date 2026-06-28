"""
Seed script — populates all 6 Neon DB tables with realistic data.
Run: python -m scripts.seed_db

Tables seeded:
  predictions       — ~180 rows (6 diseases x 20 locations x 3 risk levels)
  weather_snapshots — 80 rows  (20 locations x 4 time points)
  disease_records   — 120 rows (6 diseases x 10 countries x 2 years)
  locations         — 20 rows  (global coverage)
  model_metrics     — 18 rows  (6 diseases x 3 model types)
"""
import asyncio
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.db_models import (
    Prediction, WeatherSnapshot, DiseaseRecord,
    LocationCache, ModelMetrics,
)

random.seed(42)

# ─── Global locations (lat, lon, city, country, country_code, admin1) ─────────
LOCATIONS = [
    (-1.9403,  29.8739, "Kigali",          "Rwanda",         "RW", "Kigali City"),
    (-1.2921,  36.8219, "Nairobi",          "Kenya",          "KE", "Nairobi County"),
    ( 6.3703,   2.3912, "Cotonou",          "Benin",          "BJ", "Littoral"),
    ( 5.5502,  -0.2174, "Accra",            "Ghana",          "GH", "Greater Accra"),
    ( 9.0579,   7.4951, "Abuja",            "Nigeria",        "NG", "FCT Abuja"),
    (14.6928, -17.4467, "Dakar",            "Senegal",        "SN", "Dakar"),
    (-4.3217,  15.3222, "Kinshasa",         "DR Congo",       "CD", "Kinshasa"),
    (-25.9692, 32.5732, "Maputo",           "Mozambique",     "MZ", "Maputo Province"),
    (28.6139,  77.2090, "New Delhi",        "India",          "IN", "Delhi"),
    (23.8103,  90.4125, "Dhaka",            "Bangladesh",     "BD", "Dhaka Division"),
    (13.7565, 100.5018, "Bangkok",          "Thailand",       "TH", "Bangkok"),
    ( 3.1390, 101.6869, "Kuala Lumpur",     "Malaysia",       "MY", "Wilayah Persekutuan"),
    (-6.2088, 106.8456, "Jakarta",          "Indonesia",      "ID", "DKI Jakarta"),
    (14.0723, -87.1921, "Tegucigalpa",      "Honduras",       "HN", "Francisco Morazan"),
    (-12.0464,-77.0428, "Lima",             "Peru",           "PE", "Lima"),
    ( 4.3612,  18.5550, "Bangui",           "CAR",            "CF", "Bangui"),
    (15.5007,  32.5599, "Khartoum",         "Sudan",          "SD", "Khartoum"),
    (51.5074,  -0.1278, "London",           "United Kingdom", "GB", "England"),
    (48.8566,   2.3522, "Paris",            "France",         "FR", "Ile-de-France"),
    (40.7128, -74.0060, "New York",         "United States",  "US", "New York State"),
]

DISEASES = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]

# (temp_range, rain_range, humidity_range, base_pop_density, cases_range, risk_level)
RISK_PROFILES = {
    "malaria": {
        "High":   ([25,35], [150,350], [75,95],  600,  [101,220]),
        "Medium": ([20,30], [50,150],  [60,80],  400,  [41,100]),
        "Low":    ([15,25], [5,50],    [40,65],  200,  [0,40]),
    },
    "flu": {
        "High":   ([5,15],  [20,60],   [60,85],  800,  [71,180]),
        "Medium": ([8,18],  [15,50],   [55,78],  600,  [26,70]),
        "Low":    ([15,25], [5,20],    [40,60],  400,  [0,25]),
    },
    "cholera": {
        "High":   ([28,38], [120,300], [80,95],  900,  [36,90]),
        "Medium": ([25,35], [60,120],  [65,85],  700,  [11,35]),
        "Low":    ([18,28], [5,40],    [40,65],  300,  [0,10]),
    },
    "dengue": {
        "High":   ([28,38], [100,280], [75,92],  1200, [81,160]),
        "Medium": ([25,35], [50,120],  [65,85],  900,  [31,80]),
        "Low":    ([18,28], [5,50],    [40,65],  500,  [0,30]),
    },
    "pneumonia": {
        "High":   ([5,15],  [15,50],   [55,80],  700,  [121,250]),
        "Medium": ([8,20],  [10,40],   [50,75],  500,  [51,120]),
        "Low":    ([15,25], [5,20],    [40,60],  350,  [0,50]),
    },
    "meningitis": {
        "High":   ([30,42], [5,30],    [20,45],  400,  [41,100]),
        "Medium": ([28,38], [3,20],    [15,40],  300,  [16,40]),
        "Low":    ([20,32], [0,10],    [10,30],  200,  [0,15]),
    },
}

WHO_RECORDS = {
    "malaria":    [("RW",2500), ("KE",8200),  ("NG",55000), ("CD",42000), ("MZ",12000),
                  ("GH",6800),  ("BJ",1900),  ("SN",3400),  ("SD",7200),  ("CF",2100)],
    "cholera":    [("RW",45),   ("KE",180),   ("NG",520),   ("CD",890),   ("MZ",230),
                  ("GH",95),    ("BJ",62),    ("SN",110),   ("SD",340),   ("CF",78)],
    "flu":        [("IN",52000),("BD",31000), ("TH",18000), ("MY",9500),  ("ID",45000),
                  ("GB",120000),("US",890000),("NG",38000), ("PE",14000), ("HN",6200)],
    "dengue":     [("TH",8400), ("MY",5200),  ("ID",22000), ("BD",9800),  ("IN",38000),
                  ("PE",3400),  ("HN",1200),  ("BJ",340),   ("GH",280),   ("SN",190)],
    "pneumonia":  [("IN",180000),("BD",95000),("NG",120000),("CD",78000), ("TH",32000),
                  ("ID",145000),("PE",28000), ("ZA",45000), ("KE",38000), ("SD",22000)],
    "meningitis": [("NG",2800), ("SD",1200),  ("CF",780),   ("BJ",420),   ("SN",560),
                  ("GH",380),   ("CD",950),   ("KE",340),   ("MZ",180),   ("RW",95)],
}

MODEL_METRICS_DATA = {
    "malaria":    {"xgb":(4.14,0.9745), "rf":(4.35,0.9721), "ensemble":(4.17,0.9744)},
    "flu":        {"xgb":(2.38,0.8887), "rf":(2.44,0.8852), "ensemble":(2.38,0.8900)},
    "cholera":    {"xgb":(3.50,0.9969), "rf":(3.52,0.9969), "ensemble":(3.43,0.9970)},
    "dengue":     {"xgb":(3.62,0.9710), "rf":(3.78,0.9688), "ensemble":(3.55,0.9725)},
    "pneumonia":  {"xgb":(2.91,0.8534), "rf":(3.05,0.8498), "ensemble":(2.87,0.8562)},
    "meningitis": {"xgb":(2.48,0.8921), "rf":(2.61,0.8874), "ensemble":(2.44,0.8953)},
}


def r(lo, hi):
    return round(random.uniform(lo, hi), 2)


async def seed():
    engine  = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:

        # ── locations ──────────────────────────────────────────────────────
        print("Seeding locations...", end=" ")
        for loc in LOCATIONS:
            db.add(LocationCache(
                lat=round(loc[0], 4), lon=round(loc[1], 4),
                city=loc[2], country=loc[3], country_code=loc[4],
                admin1=loc[5], display_name=f"{loc[2]}, {loc[3]}",
                cached_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            ))
        await db.commit()
        print(f"✓ {len(LOCATIONS)} rows")

        # ── predictions ────────────────────────────────────────────────────
        print("Seeding predictions...", end=" ")
        pred_count = 0
        for loc in LOCATIONS:
            for disease in DISEASES:
                profile = RISK_PROFILES[disease]
                for risk_level, days_ago in [("High", random.randint(0,3)),
                                             ("Medium", random.randint(4,14)),
                                             ("Low", random.randint(15,60))]:
                    p = profile[risk_level]
                    db.add(Prediction(
                        lat=round(loc[0],4), lon=round(loc[1],4),
                        location_name=f"{loc[2]}, {loc[3]}",
                        disease=disease, risk_level=risk_level,
                        expected_cases=random.randint(*p[4]),
                        confidence=round(random.uniform(0.75, 0.97), 2),
                        temperature=r(*p[0]), rainfall=r(*p[1]),
                        humidity=r(*p[2]),
                        wind_speed=r(2, 28),
                        population_density=float(p[3] + random.randint(-100, 200)),
                        predicted_at=datetime.utcnow() - timedelta(
                            days=days_ago, hours=random.randint(0, 23)),
                    ))
                    pred_count += 1
        await db.commit()
        print(f"✓ {pred_count} rows")

        # ── weather_snapshots ──────────────────────────────────────────────
        print("Seeding weather snapshots...", end=" ")
        snap_count = 0
        for loc in LOCATIONS:
            for days_ago in [0, 7, 14, 30]:
                db.add(WeatherSnapshot(
                    lat=round(loc[0],4), lon=round(loc[1],4),
                    location_name=f"{loc[2]}, {loc[3]}",
                    temperature=r(8, 42), rainfall=r(0, 300),
                    humidity=r(25, 98),   wind_speed=r(1, 35),
                    fetched_at=datetime.utcnow() - timedelta(
                        days=days_ago, hours=random.randint(0, 12)),
                ))
                snap_count += 1
        await db.commit()
        print(f"✓ {snap_count} rows")

        # ── disease_records ────────────────────────────────────────────────
        print("Seeding disease records...", end=" ")
        rec_count = 0
        for disease, entries in WHO_RECORDS.items():
            for country_code, base in entries:
                for year in [2022, 2023]:
                    cases = round(base * random.uniform(0.85, 1.20))
                    db.add(DiseaseRecord(
                        disease=disease, country_code=country_code,
                        year=year, cases=float(cases),
                        low=float(round(cases * 0.85)),
                        high=float(round(cases * 1.15)),
                        source="WHO_GHO",
                        fetched_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    ))
                    rec_count += 1
        await db.commit()
        print(f"✓ {rec_count} rows")

        # ── model_metrics ──────────────────────────────────────────────────
        print("Seeding model metrics...", end=" ")
        met_count = 0
        for disease, models in MODEL_METRICS_DATA.items():
            for model_type, (mae, r2) in models.items():
                db.add(ModelMetrics(
                    disease=disease, model_type=model_type,
                    mae=mae, r2=r2,
                    n_samples=6400, n_features=24,
                    notes="XGBoost + Random Forest ensemble — 8000 synthetic samples, 80/20 split",
                    trained_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
                ))
                met_count += 1
        await db.commit()
        print(f"✓ {met_count} rows")

    await engine.dispose()

    print("\n✅ Seed complete:")
    print(f"   locations          {len(LOCATIONS)}")
    print(f"   predictions        {pred_count}")
    print(f"   weather_snapshots  {snap_count}")
    print(f"   disease_records    {rec_count}")
    print(f"   model_metrics      {met_count}")
    print(f"   TOTAL              {len(LOCATIONS)+pred_count+snap_count+rec_count+met_count}")


if __name__ == "__main__":
    asyncio.run(seed())
