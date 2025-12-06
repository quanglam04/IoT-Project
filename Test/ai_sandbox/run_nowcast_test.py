"""
Script chạy thử inference cho sandbox:

1. Sinh một buffer sensor 1 giờ (15s/bản ghi) synthetic.
2. Sinh 1 bản ghi API synthetic tương ứng.
3. Tính feature vector từ buffer sensor + api.
4. Load model XGBoost đã train trong `train_virtual_rain.py`.
5. Tính rain_prob_fusion.
6. Áp dụng decision_logic để sinh:
   - Output 1 (virtual_rain_sensor + control + ui_message + telemetry).
   - Output 2 (scheduler đơn giản 4h).
7. In ra màn hình 2 JSON để bạn so sánh với format trong báo cáo.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

# Hỗ trợ cả chạy trực tiếp và chạy như module
try:
    from .config_test import ensure_dirs, DATA_DIR, MODEL_CFG
    from .decision_logic import NowcastContext, build_output_1, build_output_2
    from .feature_engineering import compute_feature_from_window, FEATURE_NAMES
except ImportError:
    # Chạy trực tiếp từ thư mục ai_sandbox
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ai_sandbox.config_test import ensure_dirs, DATA_DIR, MODEL_CFG
    from ai_sandbox.decision_logic import NowcastContext, build_output_1, build_output_2
    from ai_sandbox.feature_engineering import compute_feature_from_window, FEATURE_NAMES


def _generate_synthetic_sensor_1h(seed: int = 123) -> pd.DataFrame:
    """
    Tạo buffer 1h sensor (15s/bản ghi) synthetic với các cột:
    ['timestamp', 'temp_c', 'rh_pct', 'soil_moist_pct', 'pressure_hpa']
    """

    rng = np.random.default_rng(seed)
    now = datetime(2025, 6, 15, 14, 30, 15)

    n_points = 240  # 1h
    rows = []
    base_temp = 34.0
    base_rh = 65.0
    base_soil = 40.0
    base_pressure = 1005.0

    for i in range(n_points):
        ts = now - timedelta(seconds=(n_points - 1 - i) * 15)
        # Giả lập xu hướng áp suất đang giảm nhẹ
        pressure = base_pressure - 0.02 * i + rng.normal(0, 0.05)
        temp = base_temp - 0.01 * i + rng.normal(0, 0.1)
        rh = base_rh + 0.03 * i + rng.normal(0, 0.3)
        soil = base_soil - 0.02 * i + rng.normal(0, 0.2)

        rows.append(
            {
                "timestamp": ts.isoformat(),
                "temp_c": float(temp),
                "rh_pct": float(np.clip(rh, 30.0, 100.0)),
                "soil_moist_pct": float(np.clip(soil, 5.0, 80.0)),
                "pressure_hpa": float(pressure),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "synthetic_sensor_live.csv", index=False)
    return df


def _generate_synthetic_api_row() -> dict:
    """
    Sinh 1 bản ghi API synthetic (mưa rào mùa Hè).
    """

    return {
        "api_pop": 0.6,
        "api_rain_1h": 4.0,
        "api_temp_c": 32.0,
        "api_rh_pct": 80.0,
        "api_uvi": 8.0,
        "api_weather_code": 201,
    }


def _load_model() -> XGBClassifier:
    model = XGBClassifier()
    model.load_model(MODEL_CFG.model_path.as_posix())
    return model


def main() -> None:
    ensure_dirs()

    # 1. Chuẩn bị dữ liệu sensor + api synthetic
    sensor_df = _generate_synthetic_sensor_1h()
    api_dict = _generate_synthetic_api_row()
    api_row = pd.Series(api_dict)

    # 2. Tính feature vector
    feat = compute_feature_from_window(sensor_df, api_row)
    X = np.array([feat.to_list()], dtype=float)

    # 3. Load model đã train
    model = _load_model()

    # 4. Tính xác suất mưa hợp nhất
    rain_prob_fusion = float(model.predict_proba(X)[0, 1])

    # 5. Build context cho decision logic
    last_ts = pd.to_datetime(sensor_df.iloc[-1]["timestamp"])
    ctx = NowcastContext(
        timestamp=last_ts,
        month=int(last_ts.month),
        soil_moisture=float(sensor_df.iloc[-1]["soil_moist_pct"]),
        pressure_trend=float(
            sensor_df.iloc[-1]["pressure_hpa"] - sensor_df.iloc[0]["pressure_hpa"]
        ),
        api_weather_code=int(api_dict["api_weather_code"]),
        api_pop=float(api_dict["api_pop"]),
        api_rain_1h=float(api_dict["api_rain_1h"]),
    )

    # 6. Sinh output JSON 1 & 2
    output1 = build_output_1(ctx, rain_prob_fusion)
    output2 = build_output_2(last_ts, "Sandbox: Lịch tưới demo cho 4 giờ tới.")

    # 7. In ra màn hình
    print("=== OUTPUT 1 (NOWCAST) ===")
    print(json.dumps(output1, ensure_ascii=False, indent=2))
    print("\n=== OUTPUT 2 (SCHEDULE) ===")
    print(json.dumps(output2, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


