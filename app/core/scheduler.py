"""
Background scheduler — APScheduler (AsyncIOScheduler).

Jobs run while the Fly.io machine is alive. On Fly.io free tier the machine
auto-stops after ~7 min of no traffic, so scheduled jobs are best-effort;
they run during active periods and resume when the next request wakes the app.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

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


def setup_scheduler() -> None:
    """Register all background jobs. Call once at startup."""
    scheduler.add_job(
        _refresh_who_cache,
        trigger=IntervalTrigger(hours=6),
        id="who_data_refresh",
        replace_existing=True,
        misfire_grace_time=300,       # allow up to 5 min late start after machine wake
    )
    logger.info("Scheduler configured — WHO cache refresh every 6 hours")
