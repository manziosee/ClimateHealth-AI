"""
Monitor endpoints — subscription-based alerts + bulk location monitoring

POST /api/v1/monitor/subscribe          — register a location+disease for daily push alerts
DELETE /api/v1/monitor/subscribe/{id}   — cancel a subscription
GET  /api/v1/monitor/subscriptions      — list all active subscriptions
POST /api/v1/monitor/locations          — register a location into a named group
GET  /api/v1/monitor/summary            — bulk risk scan — returns only High-risk from group
"""
import json
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.cache import get_redis
from app.core.database import get_db
from app.models.db_models import AlertSubscription, MonitoredLocation
from app.services import weather as weather_svc
from app.services import predictor
from app.services.geocoding import reverse_geocode
from app.api.v1.predictions import _resolve_population_density, _build_predict_kwargs

router = APIRouter(prefix="/monitor", tags=["monitor"])

_DISEASES = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]


# ─── Subscription CRUD ────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_E164_RE  = re.compile(r'^\+[1-9]\d{6,14}$')


_URL_RE = re.compile(r'^https?://.+')


class SubscribeRequest(BaseModel):
    lat:          float  = Field(..., ge=-90, le=90)
    lon:          float  = Field(..., ge=-180, le=180)
    disease:      str    = "malaria"
    threshold:    str    = Field(default="High", pattern="^(High|Medium)$")
    notify_email: str | None = None
    notify_phone: str | None = None
    webhook_url:  str | None = Field(None, description="HTTPS URL to POST the alert payload to")

    @field_validator("notify_email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address format")
        return v

    @field_validator("notify_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not _E164_RE.match(v):
            raise ValueError("Phone must be E.164 format, e.g. +250788123456")
        return v

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook(cls, v: str | None) -> str | None:
        if v is not None and not _URL_RE.match(v):
            raise ValueError("webhook_url must start with http:// or https://")
        return v


class SubscriptionResponse(BaseModel):
    id: int
    lat: float
    lon: float
    location_name: str | None
    disease: str
    threshold: str
    notify_email: str | None
    notify_phone: str | None
    webhook_url:  str | None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/subscribe", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    body: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    **Register a location + disease for daily push alerts.**

    When the scheduled job runs every 24 hours, it checks each active subscription
    and sends email/SMS if the predicted risk meets or exceeds the threshold.

    - `threshold`: `High` (default) or `Medium`
    - At least one of `notify_email`, `notify_phone`, or `webhook_url` must be provided.
    """
    if not body.notify_email and not body.notify_phone and not body.webhook_url:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of notify_email, notify_phone, or webhook_url.",
        )

    location_name, _ = await reverse_geocode(body.lat, body.lon)
    sub = AlertSubscription(
        lat=body.lat, lon=body.lon, location_name=location_name,
        disease=body.disease, threshold=body.threshold,
        notify_email=body.notify_email, notify_phone=body.notify_phone,
        webhook_url=body.webhook_url,
        active=True,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete("/subscribe/{sub_id}", status_code=204)
async def cancel_subscription(sub_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel an alert subscription by ID."""
    sub = await db.get(AlertSubscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    await db.execute(delete(AlertSubscription).where(AlertSubscription.id == sub_id))
    await db.commit()


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    """List all alert subscriptions."""
    q = select(AlertSubscription)
    if active_only:
        q = q.where(AlertSubscription.active == True)  # noqa: E712
    rows = (await db.execute(q.order_by(AlertSubscription.created_at.desc()))).scalars().all()
    return rows


# ─── Monitored Location Groups ────────────────────────────────────────────────

class AddLocationRequest(BaseModel):
    group_name:    str   = Field(..., min_length=1, max_length=100)
    lat:           float = Field(..., ge=-90, le=90)
    lon:           float = Field(..., ge=-180, le=180)
    location_name: str | None = None


class MonitoredLocationResponse(BaseModel):
    id: int
    group_name: str
    lat: float
    lon: float
    location_name: str | None
    added_at: datetime

    model_config = {"from_attributes": True}


@router.post("/locations", response_model=MonitoredLocationResponse, status_code=201)
async def add_monitored_location(
    body: AddLocationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    **Register a location into a named monitoring group.**

    NGOs can create groups like *"Rwanda Health Zones"* or *"Congo River Basin"*
    and then call `/monitor/summary` with that group name to get a bulk risk scan
    across all registered coordinates.
    """
    name = body.location_name
    if not name:
        name, _ = await reverse_geocode(body.lat, body.lon)

    loc = MonitoredLocation(
        group_name=body.group_name, lat=body.lat, lon=body.lon, location_name=name,
    )
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return loc


@router.delete("/locations/{loc_id}", status_code=204)
async def remove_monitored_location(loc_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a location from monitoring."""
    loc = await db.get(MonitoredLocation, loc_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Monitored location not found.")
    await db.execute(delete(MonitoredLocation).where(MonitoredLocation.id == loc_id))
    await db.commit()


# ─── Bulk Summary ─────────────────────────────────────────────────────────────

class BulkRiskItem(BaseModel):
    location_name: str | None
    lat: float
    lon: float
    disease: str
    risk_level: str
    expected_cases: int
    confidence: float


class MonitorSummaryResponse(BaseModel):
    group_name: str
    disease: str
    total_locations: int
    high_risk_count: int
    results: list[BulkRiskItem]   # only High-risk entries returned
    generated_at: datetime


@router.get("/summary", response_model=MonitorSummaryResponse)
async def monitor_summary(
    group_name: str = Query(..., description="Name of the monitored location group"),
    disease:    str = Query("malaria"),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    **Bulk High-risk scan** for a pre-registered group of locations.

    Runs disease predictions for every coordinate in the group and returns
    **only the High-risk locations** — NGOs don't need to see Low-risk noise,
    they need to know where to deploy resources.

    Results are cached 30 minutes. Register locations first via `POST /monitor/locations`.
    """
    cache_key = f"monitor_summary:{group_name}:{disease}"
    cached = await redis.get(cache_key)
    if cached:
        return MonitorSummaryResponse(**json.loads(cached))

    locations = (await db.execute(
        select(MonitoredLocation).where(MonitoredLocation.group_name == group_name)
    )).scalars().all()

    if not locations:
        raise HTTPException(status_code=404, detail=f"No locations found for group '{group_name}'.")

    high_risk_items = []
    for loc in locations:
        try:
            weather                     = await weather_svc.fetch_weather(loc.lat, loc.lon)
            location_name, country_code = await reverse_geocode(loc.lat, loc.lon)
            pop_density                 = await _resolve_population_density(None, country_code, redis)
            result                      = predictor.predict(**_build_predict_kwargs(weather, pop_density, disease))
            if result["risk_level"] == "High":
                high_risk_items.append(BulkRiskItem(
                    location_name=location_name or loc.location_name,
                    lat=loc.lat, lon=loc.lon, disease=disease,
                    risk_level=result["risk_level"],
                    expected_cases=result["expected_cases"],
                    confidence=result["confidence"],
                ))
        except Exception:
            continue

    response = MonitorSummaryResponse(
        group_name=group_name, disease=disease,
        total_locations=len(locations),
        high_risk_count=len(high_risk_items),
        results=high_risk_items,
        generated_at=datetime.now(timezone.utc),
    )
    await redis.setex(cache_key, 1800, response.model_dump_json())
    return response
