from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.db_models import Prediction
from app.models.schemas import StatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(Prediction))).scalar_one()

    # Risk level counts
    risk_rows = (await db.execute(
        select(Prediction.risk_level, func.count().label("cnt"))
        .group_by(Prediction.risk_level)
    )).all()
    risk_map = {row.risk_level: row.cnt for row in risk_rows}

    # Disease breakdown
    disease_rows = (await db.execute(
        select(Prediction.disease, func.count().label("cnt"))
        .group_by(Prediction.disease)
    )).all()
    by_disease = {row.disease: row.cnt for row in disease_rows}

    # Average confidence
    avg_conf = (await db.execute(select(func.avg(Prediction.confidence)))).scalar_one() or 0.0

    # Most predicted disease
    most_predicted = max(by_disease, key=by_disease.get) if by_disease else None

    return StatsResponse(
        total_predictions=total,
        high_risk_count=risk_map.get("High", 0),
        medium_risk_count=risk_map.get("Medium", 0),
        low_risk_count=risk_map.get("Low", 0),
        by_disease=by_disease,
        avg_confidence=round(float(avg_conf), 4),
        most_predicted_disease=most_predicted,
    )
