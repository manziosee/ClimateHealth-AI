"""
Train XGBoost + Random Forest regression models for each disease.
Run: python -m app.ml.train
Models saved to: app/ml/saved_models/{disease}_{model}.pkl
Metrics saved to: app/ml/saved_models/metrics.json + model_metrics DB table
"""
import json
import shutil
import asyncio
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split, KFold
from xgboost import XGBRegressor

from app.ml.data_generator import generate
from app.ml.pipeline import engineer_features, FEATURE_COLUMNS

DISEASES  = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]
MODEL_DIR = Path(__file__).parent / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)

N_SAMPLES = 15000  # up from 8 000 — more data = better generalization

XGB_PARAMS = {
    "n_estimators":       600,
    "max_depth":          6,
    "learning_rate":      0.04,
    "subsample":          0.85,
    "colsample_bytree":   0.80,
    "min_child_weight":   3,
    "reg_alpha":          0.1,   # L1 — prunes low-signal features
    "reg_lambda":         1.0,   # L2 — shrinks large weights
    "early_stopping_rounds": 50,
    "random_state":       42,
    "n_jobs":             -1,
}

RF_PARAMS = {
    "n_estimators":     400,
    "max_depth":        12,
    "min_samples_leaf": 3,
    "max_features":     "sqrt",  # more variance across trees → less overfit
    "random_state":     42,
    "n_jobs":           -1,
}

# XGB params without early_stopping_rounds for CV evaluation
_XGB_CV_PARAMS = {k: v for k, v in XGB_PARAMS.items() if k != "early_stopping_rounds"}
_XGB_CV_PARAMS["n_estimators"] = 300  # fixed budget for fast CV passes


def _metrics(y_true, y_pred) -> dict:
    y_pred = np.clip(y_pred, 0, None)
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "r2":  round(float(r2_score(y_true, y_pred)), 4),
    }


def _cross_val_r2(estimator_cls, params: dict, X, y, n_splits: int = 5) -> tuple[float, float]:
    """Return mean and std of R² across n_splits folds."""
    kf     = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores = []
    for train_idx, val_idx in kf.split(X):
        X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_va = y.iloc[train_idx], y.iloc[val_idx]
        m = estimator_cls(**params)
        m.fit(X_tr, y_tr)
        preds = np.clip(m.predict(X_va), 0, None)
        scores.append(r2_score(y_va, preds))
    arr = np.array(scores)
    return round(float(arr.mean()), 4), round(float(arr.std()), 4)


def _backup(path: Path) -> None:
    """Keep one .bak copy so a bad training run is recoverable."""
    if path.exists():
        shutil.copy2(path, path.with_suffix(".pkl.bak"))


def train_disease(disease: str) -> dict:
    print(f"\n[{disease.upper()}] generating {N_SAMPLES:,} training samples...")
    df = generate(disease, n_samples=N_SAMPLES)

    X = engineer_features(df)[FEATURE_COLUMNS]
    y = df["cases"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # ── XGBoost with early stopping ──────────────────────────────────────────
    xgb_path = MODEL_DIR / f"{disease}_xgb.pkl"
    _backup(xgb_path)

    xgb = XGBRegressor(**XGB_PARAMS)
    xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    xgb_preds   = xgb.predict(X_test)
    xgb_metrics = _metrics(y_test, xgb_preds)
    joblib.dump(xgb, xgb_path)

    xgb_cv_mean, xgb_cv_std = _cross_val_r2(XGBRegressor, _XGB_CV_PARAMS, X, y)
    print(f"  XGBoost      → MAE={xgb_metrics['mae']}  R²={xgb_metrics['r2']}"
          f"  (5-fold CV R²={xgb_cv_mean} ± {xgb_cv_std})")

    # ── Random Forest ─────────────────────────────────────────────────────────
    rf_path = MODEL_DIR / f"{disease}_rf.pkl"
    _backup(rf_path)

    rf = RandomForestRegressor(**RF_PARAMS)
    rf.fit(X_train, y_train)
    rf_preds   = rf.predict(X_test)
    rf_metrics = _metrics(y_test, rf_preds)
    joblib.dump(rf, rf_path)

    rf_cv_mean, rf_cv_std = _cross_val_r2(RandomForestRegressor, RF_PARAMS, X, y)
    print(f"  RandomForest → MAE={rf_metrics['mae']}  R²={rf_metrics['r2']}"
          f"  (5-fold CV R²={rf_cv_mean} ± {rf_cv_std})")

    # ── Ensemble ──────────────────────────────────────────────────────────────
    ensemble_preds = (xgb_preds + rf_preds) / 2
    ens_metrics    = _metrics(y_test, ensemble_preds)
    print(f"  Ensemble     → MAE={ens_metrics['mae']}  R²={ens_metrics['r2']}")

    n_train = len(y_train)
    n_feat  = len(FEATURE_COLUMNS)
    return {
        "xgb":      {**xgb_metrics, "cv_r2": xgb_cv_mean, "cv_r2_std": xgb_cv_std,
                     "n_samples": n_train, "n_features": n_feat},
        "rf":       {**rf_metrics,  "cv_r2": rf_cv_mean,  "cv_r2_std": rf_cv_std,
                     "n_samples": n_train, "n_features": n_feat},
        "ensemble": {**ens_metrics, "n_samples": n_train, "n_features": n_feat},
    }


async def _save_metrics_to_db(all_metrics: dict) -> None:
    """Persist training metrics to model_metrics table."""
    try:
        from app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.models.db_models import ModelMetrics

        engine  = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
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
                        notes=f"cv_r2={m.get('cv_r2', '')} ± {m.get('cv_r2_std', '')}",
                    )
                    session.add(row)
            await session.commit()
        await engine.dispose()
        print("Metrics saved to model_metrics table.")
    except Exception as e:
        print(f"  Warning: could not save metrics to DB: {e}")


def main():
    all_metrics = {}
    for disease in DISEASES:
        all_metrics[disease] = train_disease(disease)

    metrics_path = MODEL_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(all_metrics, indent=2))
    print(f"\nAll models trained. Metrics -> {metrics_path}")

    asyncio.run(_save_metrics_to_db(all_metrics))


if __name__ == "__main__":
    main()
