"""
Train XGBoost + Random Forest regression models for each disease.
Run: python -m app.ml.train
Models saved to: app/ml/saved_models/{disease}_{model}.pkl
Metrics saved to: app/ml/saved_models/metrics.json + model_metrics DB table
"""
import json
import asyncio
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from app.ml.data_generator import generate
from app.ml.pipeline import engineer_features, FEATURE_COLUMNS

DISEASES  = ["malaria", "flu", "cholera"]
MODEL_DIR = Path(__file__).parent / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)

XGB_PARAMS = {
    "n_estimators":     400,
    "max_depth":        6,
    "learning_rate":    0.05,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "random_state":     42,
    "n_jobs":           -1,
}

RF_PARAMS = {
    "n_estimators":     300,
    "max_depth":        10,
    "min_samples_leaf": 4,
    "random_state":     42,
    "n_jobs":           -1,
}


def _metrics(y_true, y_pred) -> dict:
    y_pred = np.clip(y_pred, 0, None)
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "r2":  round(float(r2_score(y_true, y_pred)), 4),
    }


def train_disease(disease: str) -> dict:
    print(f"\n[{disease.upper()}] generating training data...")
    df = generate(disease, n_samples=8000)

    X = engineer_features(df)[FEATURE_COLUMNS]
    y = df["cases"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    xgb = XGBRegressor(**XGB_PARAMS)
    xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    xgb_preds   = xgb.predict(X_test)
    xgb_metrics = _metrics(y_test, xgb_preds)
    joblib.dump(xgb, MODEL_DIR / f"{disease}_xgb.pkl")
    print(f"  XGBoost      → MAE={xgb_metrics['mae']}  R²={xgb_metrics['r2']}")

    rf = RandomForestRegressor(**RF_PARAMS)
    rf.fit(X_train, y_train)
    rf_preds   = rf.predict(X_test)
    rf_metrics = _metrics(y_test, rf_preds)
    joblib.dump(rf, MODEL_DIR / f"{disease}_rf.pkl")
    print(f"  RandomForest → MAE={rf_metrics['mae']}  R²={rf_metrics['r2']}")

    ensemble_preds = (xgb_preds + rf_preds) / 2
    ens_metrics = _metrics(y_test, ensemble_preds)
    print(f"  Ensemble     → MAE={ens_metrics['mae']}  R²={ens_metrics['r2']}")

    return {
        "xgb":      {**xgb_metrics, "n_samples": len(y_train), "n_features": len(FEATURE_COLUMNS)},
        "rf":       {**rf_metrics,  "n_samples": len(y_train), "n_features": len(FEATURE_COLUMNS)},
        "ensemble": {**ens_metrics, "n_samples": len(y_train), "n_features": len(FEATURE_COLUMNS)},
    }


async def _save_metrics_to_db(all_metrics: dict) -> None:
    """Persist training metrics to model_metrics table."""
    try:
        from app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.models.db_models import ModelMetrics

        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        Session = async_sessionmaker(engine, expire_on_commit=False)

        async with Session() as session:
            for disease, metrics in all_metrics.items():
                for model_type, m in metrics.items():
                    row = ModelMetrics(
                        disease=disease,
                        model_type=model_type,
                        mae=m["mae"],
                        r2=m["r2"],
                        n_samples=m["n_samples"],
                        n_features=m["n_features"],
                        notes=f"Trained by app.ml.train",
                    )
                    session.add(row)
            await session.commit()
        await engine.dispose()
        print("✓ Metrics saved to model_metrics table.")
    except Exception as e:
        print(f"  Warning: could not save metrics to DB: {e}")


def main():
    all_metrics = {}
    for disease in DISEASES:
        all_metrics[disease] = train_disease(disease)

    metrics_path = MODEL_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(all_metrics, indent=2))
    print(f"\n✓ All models trained. Metrics → {metrics_path}")

    # Try to persist metrics to DB (non-fatal if DB unavailable)
    asyncio.run(_save_metrics_to_db(all_metrics))


if __name__ == "__main__":
    main()
