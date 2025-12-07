"""
Script train mô hình XGBoost đơn giản cho Virtual Rain (sandbox).

Pipeline:
1. Sinh dữ liệu synthetic mô phỏng 3 năm (nhưng số lượng nhỏ để train nhanh).
2. Xây dựng label Rain = 1/0 dựa trên rule:
   - API pop cao, áp suất giảm, temp_drop_15m > 0, rh_rise_15m > 0 -> Rain = 1.
3. Train XGBoost binary:logistic.
4. Lưu model + feature_schema.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Hỗ trợ cả chạy trực tiếp và chạy như module
try:
    from .config_test import ensure_dirs, DATA_DIR, MODEL_CFG
    from .feature_engineering import FEATURE_NAMES
except ImportError:
    # Chạy trực tiếp từ thư mục ai_sandbox
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ai_sandbox.config_test import ensure_dirs, DATA_DIR, MODEL_CFG
    from ai_sandbox.feature_engineering import FEATURE_NAMES


def generate_synthetic_train_data(
    n_days: int = 60,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Sinh dữ liệu synthetic mức "giờ" (1h/bản ghi) cho train.

    Lý do: báo cáo dùng dữ liệu lịch sử theo giờ, model học trên các feature
    rolling 1h. Ở đây ta fake các feature đó luôn, không cần raw 15s.
    """

    rng = np.random.default_rng(seed)

    start = datetime(2024, 1, 1, 0, 0, 0)
    rows = []

    for i in range(n_days * 24):
        ts = start + timedelta(hours=i)
        month = ts.month
        hour = ts.hour

        # API features
        # Mùa Hè: pop & rain_1h cao hơn
        base_pop = 0.2
        if 5 <= month <= 9:
            base_pop = 0.35

        api_pop = float(np.clip(rng.normal(loc=base_pop, scale=0.25), 0.0, 1.0))
        api_rain_1h = float(max(0.0, rng.normal(loc=api_pop * 5.0, scale=3.0)))
        api_uvi = float(np.clip(rng.normal(loc=6.0 if 5 <= month <= 9 else 2.0, scale=2.0), 0.0, 11.0))

        # Sensor trend features synthetic
        pressure_slope_1h = float(rng.normal(loc=0.0, scale=1.2))
        temp_drop_15m = float(max(0.0, rng.normal(loc=api_pop * 2.0, scale=1.0)))
        rh_rise_15m = float(max(0.0, rng.normal(loc=api_pop * 15.0, scale=10.0)))

        # Fusion features
        dew_point_diff = float(rng.normal(loc=0.0, scale=1.0))
        temp_bias = float(rng.normal(loc=0.0, scale=2.0))

        soil_moist_smooth = float(np.clip(rng.normal(loc=45.0, scale=15.0), 5.0, 95.0))

        rows.append(
            {
                "timestamp": ts.isoformat(),
                "month": month,
                "hour": hour,
                "api_pop": api_pop,
                "api_rain_1h": api_rain_1h,
                "pressure_slope_1h": pressure_slope_1h,
                "temp_drop_15m": temp_drop_15m,
                "rh_rise_15m": rh_rise_15m,
                "dew_point_diff": dew_point_diff,
                "temp_bias": temp_bias,
                "soil_moist_smooth": soil_moist_smooth,
                "uvi_index": api_uvi,
            }
        )

    df = pd.DataFrame(rows)

    # Tính cyclical encoding
    month_rad = 2 * np.pi * (df["month"] % 12) / 12.0
    hour_rad = 2 * np.pi * (df["hour"] % 24) / 24.0
    df["month_sin"] = np.sin(month_rad)
    df["month_cos"] = np.cos(month_rad)
    df["hour_sin"] = np.sin(hour_rad)
    df["hour_cos"] = np.cos(hour_rad)

    # Rule tạo label Rain
    # - Nếu pop cao & áp suất giảm & temp_drop_15m > 0 & rh_rise_15m > 0 -> Rain
    score = (
        2.0 * df["api_pop"]
        - 0.2 * df["pressure_slope_1h"]
        + 0.1 * df["temp_drop_15m"]
        + 0.02 * df["rh_rise_15m"]
    )
    # Ngưỡng phụ thuộc mùa (mùa Hè dễ mưa hơn)
    thresh = np.where(df["month"].between(5, 9), 0.9, 1.1)
    df["rain_label"] = (score > thresh).astype(int)

    return df


def split_and_train(
    df: pd.DataFrame,
) -> Tuple[XGBClassifier, float]:
    X = df[FEATURE_NAMES].to_numpy(dtype=float)
    y = df["rain_label"].to_numpy(dtype=int)

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="auc",
        max_depth=5,
        learning_rate=0.05,
        n_estimators=200,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=3.0,  # synthetic data ít mưa
        n_jobs=2,
    )

    model.fit(X_train, y_train)
    val_probs = model.predict_proba(X_val)[:, 1]
    # AUC đơn giản tự tính (không import roc_auc trong sandbox cho gọn)
    # Dùng thước đo gần đúng: correlation giữa y và prob
    corr = np.corrcoef(y_val, val_probs)[0, 1]

    return model, float(corr)


def main() -> None:
    ensure_dirs()

    synthetic_path = DATA_DIR / "synthetic_train.csv"
    if synthetic_path.exists():
        df = pd.read_csv(synthetic_path)
    else:
        df = generate_synthetic_train_data()
        df.to_csv(synthetic_path, index=False)

    model, corr = split_and_train(df)

    # Lưu model
    MODEL_CFG.model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(MODEL_CFG.model_path.as_posix())

    # Lưu feature schema
    with MODEL_CFG.feature_schema_path.open("w", encoding="utf-8") as f:
        json.dump({"feature_names": FEATURE_NAMES}, f, ensure_ascii=False, indent=2)

    print(f"[TRAIN] Synthetic data shape: {df.shape}")
    print(f"[TRAIN] Correlation(y, prob) ~ {corr:.3f}")
    print(f"[TRAIN] Model saved to: {MODEL_CFG.model_path}")
    print(f"[TRAIN] Feature schema saved to: {MODEL_CFG.feature_schema_path}")


if __name__ == "__main__":
    main()


