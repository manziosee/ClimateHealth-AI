"""
Admin endpoints — GET /api/v1/admin/status
                  POST/GET/DELETE /api/v1/admin/keys
                  POST/GET        /api/v1/admin/retrain

All write operations require the ADMIN_API_KEY header (master key).
Read-only endpoints (status, retrain/status) accept any valid API key.
"""
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, delete

from app.core.cache import get_redis
from app.core.config import settings
from app.core.database import get_db
from app.core.auth import generate_api_key, hash_key
from app.models.db_models import (
    Prediction, AlertSubscription, MonitoredLocation,
    ModelMetrics, DiseaseRecord, ApiKey,
)

router = APIRouter(prefix="/admin", tags=["admin"])

_MODEL_DIR = Path(__file__).parent.parent.parent / "ml" / "saved_models"
_DISEASES  = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]

# In-process retrain state (reset on app restart)
_retrain: dict = {
    "running":         False,
    "diseases":        [],
    "last_started":    None,
    "last_completed":  None,
    "error":           None,
}


# ─── Admin key guard ──────────────────────────────────────────────────────────

def _require_admin(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """Dependency — only the ADMIN_API_KEY may call write endpoints."""
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_API_KEY is not configured on this server.",
        )
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin key required for this operation.")


# ─── Operational status ───────────────────────────────────────────────────────

class ModelInfo(BaseModel):
    disease:    str
    xgb_r2:    float | None
    rf_r2:     float | None
    cv_r2:     float | None
    n_samples: int | None
    trained_at: datetime | None


class AdminStatusResponse(BaseModel):
    predictions_total:      int
    predictions_today:      int
    predictions_this_week:  int
    predictions_by_disease: dict[str, int]
    predictions_by_risk:    dict[str, int]
    active_subscriptions:   int
    monitored_groups:       int
    monitored_locations_total: int
    active_api_keys:        int
    models:              list[ModelInfo]
    metrics_file_exists: bool
    who_data_countries:  int
    who_data_records:    int
    redis_connected:     bool
    generated_at:        datetime


@router.get("/status", response_model=AdminStatusResponse)
async def admin_status(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    **Operational overview** — prediction volumes, subscriptions, model health,
    and data freshness. Accepts any valid API key (not admin-only).
    """
    now        = datetime.now(timezone.utc)
    today      = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=7)

    total = (await db.execute(select(func.count()).select_from(Prediction))).scalar_one()
    today_count = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= today)
    )).scalar_one()
    week_count = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= week_start)
    )).scalar_one()

    by_disease = {r.disease: r.n for r in (await db.execute(
        select(Prediction.disease, func.count().label("n")).group_by(Prediction.disease)
    )).all()}
    by_risk = {r.risk_level: r.n for r in (await db.execute(
        select(Prediction.risk_level, func.count().label("n")).group_by(Prediction.risk_level)
    )).all()}

    active_subs = (await db.execute(
        select(func.count()).select_from(AlertSubscription)
        .where(AlertSubscription.active == True)  # noqa: E712
    )).scalar_one()
    total_locs = (await db.execute(select(func.count()).select_from(MonitoredLocation))).scalar_one()
    groups     = (await db.execute(
        select(func.count(distinct(MonitoredLocation.group_name)))
    )).scalar_one()
    active_keys = (await db.execute(
        select(func.count()).select_from(ApiKey).where(ApiKey.is_active == True)  # noqa: E712
    )).scalar_one()

    # Model metrics — latest entry per (disease, model_type)
    metric_rows = (await db.execute(
        select(ModelMetrics).order_by(ModelMetrics.trained_at.desc())
    )).scalars().all()
    seen: set[tuple[str, str]] = set()
    latest: dict[str, dict]   = {}
    for row in metric_rows:
        key = (row.disease, row.model_type)
        if key in seen:
            continue
        seen.add(key)
        d = latest.setdefault(row.disease, {"trained_at": row.trained_at, "n_samples": row.n_samples})
        if row.model_type == "xgb":
            d["xgb_r2"] = row.r2
            if row.notes and "cv_r2=" in row.notes:
                try:
                    d["cv_r2"] = float(row.notes.split("cv_r2=")[1].split(" ")[0])
                except Exception:
                    pass
        elif row.model_type == "rf":
            d["rf_r2"] = row.r2

    models = [
        ModelInfo(
            disease=disease,
            xgb_r2=latest.get(disease, {}).get("xgb_r2"),
            rf_r2=latest.get(disease, {}).get("rf_r2"),
            cv_r2=latest.get(disease, {}).get("cv_r2"),
            n_samples=latest.get(disease, {}).get("n_samples"),
            trained_at=latest.get(disease, {}).get("trained_at"),
        )
        for disease in _DISEASES
    ]

    who_countries = (await db.execute(
        select(func.count(distinct(DiseaseRecord.country_code)))
    )).scalar_one()
    who_records = (await db.execute(select(func.count()).select_from(DiseaseRecord))).scalar_one()

    redis_ok = False
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        pass

    return AdminStatusResponse(
        predictions_total=total,
        predictions_today=today_count,
        predictions_this_week=week_count,
        predictions_by_disease=by_disease,
        predictions_by_risk=by_risk,
        active_subscriptions=active_subs,
        monitored_groups=groups,
        monitored_locations_total=total_locs,
        active_api_keys=active_keys,
        models=models,
        metrics_file_exists=(_MODEL_DIR / "metrics.json").exists(),
        who_data_countries=who_countries,
        who_data_records=who_records,
        redis_connected=redis_ok,
        generated_at=now,
    )


# ─── API key management ───────────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id:             int
    name:           str
    key_prefix:     str
    is_active:      bool
    requests_total: int
    last_used_at:   datetime | None
    created_at:     datetime

    model_config = {"from_attributes": True}


class CreateKeyResponse(ApiKeyResponse):
    raw_key: str  # shown exactly once — not stored


@router.post("/keys", response_model=CreateKeyResponse, status_code=201,
             dependencies=[Depends(_require_admin)])
async def create_api_key(
    body: CreateKeyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    **Create a new API key** (admin only — requires `X-API-Key: <ADMIN_API_KEY>`).

    The `raw_key` in the response is shown **exactly once** and never stored.
    Save it immediately. If lost, revoke this key and create a new one.
    """
    raw, prefix, hashed = generate_api_key()
    row = ApiKey(name=body.name, key_prefix=prefix, key_hash=hashed)
    db.add(row)
    await db.commit()
    await db.refresh(row)

    data = ApiKeyResponse.model_validate(row).model_dump()
    data["raw_key"] = raw
    return CreateKeyResponse.model_validate(data)


@router.get("/keys", response_model=list[ApiKeyResponse],
            dependencies=[Depends(_require_admin)])
async def list_api_keys(
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    """List API keys (admin only). Raw keys are never returned — only prefix and metadata."""
    q = select(ApiKey)
    if active_only:
        q = q.where(ApiKey.is_active == True)  # noqa: E712
    rows = (await db.execute(q.order_by(ApiKey.created_at.desc()))).scalars().all()
    return rows


@router.delete("/keys/{key_id}", status_code=204,
               dependencies=[Depends(_require_admin)])
async def revoke_api_key(key_id: int, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Revoke an API key (admin only). Invalidates the Redis cache entry immediately."""
    row = await db.get(ApiKey, key_id)
    if not row:
        raise HTTPException(status_code=404, detail="API key not found.")
    # Purge cache so the key is rejected immediately (before the 60 s TTL expires)
    await redis.delete(f"apikey:{row.key_hash[:20]}")
    await db.execute(delete(ApiKey).where(ApiKey.id == key_id))
    await db.commit()


# ─── Model retraining ─────────────────────────────────────────────────────────

@router.post("/retrain", status_code=202, dependencies=[Depends(_require_admin)])
async def trigger_retrain(
    disease: str | None = Query(None, description="One disease to retrain, or omit to retrain all 6"),
):
    """
    **Trigger ML model retraining** in a background thread (admin only).

    Returns `202 Accepted` immediately. Check `GET /api/v1/admin/retrain/status`
    for progress. Retrained models are available for inference as soon as the
    thread finishes — no restart required.

    **Note:** models are saved to the container filesystem and will be lost on
    the next deploy (Docker image rebuilds them at build time). Use this for
    on-demand retraining within the current running instance.
    """
    if _retrain["running"]:
        raise HTTPException(status_code=409, detail="Retraining already in progress.")

    targets = [disease] if disease else list(_DISEASES)

    def _run() -> None:
        _retrain["running"]      = True
        _retrain["error"]        = None
        _retrain["last_started"] = datetime.now(timezone.utc).isoformat()
        try:
            from app.ml.train import train_disease
            for d in targets:
                train_disease(d)
            _retrain["diseases"]       = targets
            _retrain["last_completed"] = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            _retrain["error"] = str(exc)
        finally:
            _retrain["running"] = False
            # Clear model cache so predictor picks up the freshly trained files
            from app.services import predictor
            predictor._cache.clear()

    threading.Thread(target=_run, daemon=True).start()
    return {
        "accepted":  True,
        "diseases":  targets,
        "message":   "Retraining started. Poll GET /api/v1/admin/retrain/status for progress.",
    }


@router.get("/retrain/status")
async def retrain_status():
    """Current status of the background retraining job. Accepts any valid API key."""
    return _retrain
