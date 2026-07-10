"""
Background scheduler — APScheduler (AsyncIOScheduler).

Jobs run while the Fly.io machine is alive. On Fly.io free tier the machine
auto-stops after ~7 min of no traffic, so scheduled jobs are best-effort;
they run during active periods and resume when the next request wakes the app.
"""
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")

_PREFETCH_DISEASES  = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]
_PREFETCH_COUNTRIES = ["RWA", "KEN", "NGA", "IND", "BRA", "USA", "ZAF", "EGY", "BGD", "PAK"]


async def _refresh_who_cache() -> None:
    """Prefetch WHO data for popular diseases + countries into Redis cache."""
    from app.services.disease import fetch_disease_data

    refreshed = 0
    for disease in _PREFETCH_DISEASES:
        for country in _PREFETCH_COUNTRIES[:5]:    # limit to 5 countries to stay within rate limits
            try:
                await fetch_disease_data(disease, country)
                refreshed += 1
            except Exception as e:
                logger.debug("WHO prefetch %s/%s skipped: %s", disease, country, e)

    logger.info("WHO cache refresh complete — %d entries updated", refreshed)


async def _run_subscription_alerts() -> None:
    """
    Daily job: check every active AlertSubscription, run a live prediction,
    and send email/SMS if risk meets or exceeds the subscriber's threshold.
    Skips subscriptions notified in the last 20 hours to prevent spam.
    """
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.core.cache import get_redis
    from app.models.db_models import AlertSubscription
    from app.services import weather as weather_svc
    from app.services import predictor
    from app.services.geocoding import reverse_geocode
    from app.services.notifications import send_email_alert, send_sms_alert, send_webhook_alert, AlertPayload
    from app.api.v1.alerts import _action

    _THRESHOLD_ORDER = {"Low": 0, "Medium": 1, "High": 2}

    async with AsyncSessionLocal() as db:
        subs = (await db.execute(
            select(AlertSubscription).where(AlertSubscription.active == True)  # noqa: E712
        )).scalars().all()

    notified = 0
    for sub in subs:
        # Skip if notified recently
        if sub.last_notified_at and (datetime.now(timezone.utc) - sub.last_notified_at.replace(tzinfo=timezone.utc)) < timedelta(hours=20):
            continue
        try:
            redis = await _get_redis_client()
            weather     = await weather_svc.fetch_weather(sub.lat, sub.lon)
            _, cc       = await reverse_geocode(sub.lat, sub.lon)
            pop_density = 500.0
            if cc:
                cached = await redis.get(f"wb:pop:{cc}")
                pop_density = float(cached) if cached else 500.0

            from app.api.v1.predictions import _build_predict_kwargs
            result = predictor.predict(**_build_predict_kwargs(weather, pop_density, sub.disease))

            if _THRESHOLD_ORDER.get(result["risk_level"], 0) >= _THRESHOLD_ORDER.get(sub.threshold, 2):
                action  = _action(sub.disease, result["risk_level"])
                payload = AlertPayload(
                    disease=sub.disease,
                    risk_level=result["risk_level"],
                    expected_cases=result["expected_cases"],
                    location_name=sub.location_name,
                    lat=sub.lat, lon=sub.lon,
                    recommended_action=action,
                )
                if sub.notify_email:
                    await send_email_alert(sub.notify_email, payload)
                if sub.notify_phone:
                    await send_sms_alert(sub.notify_phone, payload)
                if sub.webhook_url:
                    await send_webhook_alert(sub.webhook_url, payload)

                # Update last_notified_at
                async with AsyncSessionLocal() as db:
                    record = await db.get(AlertSubscription, sub.id)
                    if record:
                        record.last_notified_at = datetime.now(timezone.utc)
                        await db.commit()
                notified += 1
        except Exception as e:
            logger.error("Subscription alert failed for sub %d: %s", sub.id, e)

    logger.info("Subscription alerts complete — %d notifications sent", notified)


async def _get_redis_client():
    """Get a Redis client for scheduler jobs — falls back to _NoopRedis when unavailable."""
    from app.core.cache import get_redis
    return await get_redis()


def setup_scheduler() -> None:
    """Register all background jobs. Call once at startup."""
    scheduler.add_job(
        _refresh_who_cache,
        trigger=IntervalTrigger(hours=6),
        id="who_data_refresh",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        _run_subscription_alerts,
        trigger=CronTrigger(hour=6, minute=0, timezone="UTC"),  # 06:00 UTC daily
        id="subscription_alerts",
        replace_existing=True,
        misfire_grace_time=600,
    )
    logger.info("Scheduler configured — WHO refresh every 6h, subscription alerts daily at 06:00 UTC")

