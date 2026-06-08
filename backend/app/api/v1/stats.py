from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.db_models import Prediction
from app.models.schemas import StatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    now   = datetime.now(timezone.utc)
    day   = now - timedelta(hours=24)
    week  = now - timedelta(days=7)
    month = now - timedelta(days=30)

    # Total
    total = (await db.execute(select(func.count()).select_from(Prediction))).scalar_one()

    # Risk breakdown
    risk_rows = (await db.execute(
        select(Prediction.risk_level, func.count().label("cnt")).group_by(Prediction.risk_level)
    )).all()
    risk_map = {r.risk_level: r.cnt for r in risk_rows}

    # Disease breakdown
    disease_rows = (await db.execute(
        select(Prediction.disease, func.count().label("cnt")).group_by(Prediction.disease)
    )).all()
    by_disease = {r.disease: r.cnt for r in disease_rows}

    # Average confidence
    avg_conf = (await db.execute(select(func.avg(Prediction.confidence)))).scalar_one() or 0.0

    # Time-based counts
    last_24h = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= day)
    )).scalar_one()

    last_7d = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= week)
    )).scalar_one()

    last_30d = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= month)
    )).scalar_one()

    # Most recent high-risk prediction
    latest_high = (await db.execute(
        select(Prediction)
        .where(Prediction.risk_level == "High")
        .order_by(Prediction.predicted_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    # Trend: compare last 7 days vs previous 7 days
    prev_week = now - timedelta(days=14)
    prev_week_count = (await db.execute(
        select(func.count()).select_from(Prediction)
        .where(Prediction.predicted_at >= prev_week)
        .where(Prediction.predicted_at < week)
    )).scalar_one()

    trend = "up" if last_7d > prev_week_count else ("down" if last_7d < prev_week_count else "stable")

    return StatsResponse(
        total_predictions=total,
        high_risk_count=risk_map.get("High", 0),
        medium_risk_count=risk_map.get("Medium", 0),
        low_risk_count=risk_map.get("Low", 0),
        by_disease=by_disease,
        avg_confidence=round(float(avg_conf), 4),
        most_predicted_disease=max(by_disease, key=by_disease.get) if by_disease else None,
        last_24h=last_24h,
        last_7d=last_7d,
        last_30d=last_30d,
        trend=trend,
        latest_high_risk_location=latest_high.location_name if latest_high else None,
    )
