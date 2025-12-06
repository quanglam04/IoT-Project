"""
Chạy suy luận offline: dự báo mưa (prob + nhãn) + lượng mưa 60 phút tới và ra quyết định tưới.

Nguồn dữ liệu:
- Sensor: data/sensor_raw_60d.csv (hoặc sensor_raw_60d_synth.csv)
- API:    data/owm_history.csv (hoặc external_weather_60d.csv)

Run:
  python src/inference_decision.py
"""

import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from feature_engineering import FEATURE_NAMES, compute_feature_from_window

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"

# Files
SENSOR_REAL = DATA_DIR / "sensor_raw_60d.csv"
SENSOR_SYNTH = DATA_DIR / "sensor_raw_60d_synth.csv"
OWM_CSV = DATA_DIR / "owm_history.csv"
EXT_WEATHER_CSV = DATA_DIR / "external_weather_60d.csv"


def _choose_sensor_path() -> Path:
    if SENSOR_REAL.exists():
        return SENSOR_REAL
    if SENSOR_SYNTH.exists():
        return SENSOR_SYNTH
    raise FileNotFoundError("No sensor file found (sensor_raw_60d*.csv)")


def load_sensor_buffer() -> pd.DataFrame:
    path = _choose_sensor_path()
    df = pd.read_csv(path, parse_dates=["ts"]).sort_values("ts")
    # Lấy 12 bản ghi gần nhất (tương đương 60 phút với dữ liệu 5 phút)
    df = df.tail(12).copy()
    df = df.rename(
        columns={
            "ts": "ts",
            "temp_c": "temp_c",
            "rh_pct": "rh_pct",
            "pressure_hpa": "pressure_hpa",
            "soil_moist_pct": "soil_moist_pct",
        }
    )
    if len(df) < 2:
        raise ValueError("Not enough sensor data to compute features (need >=2 rows).")
    return df


def load_api_row(ts_ref: pd.Timestamp) -> pd.Series:
    api_df = None
    if OWM_CSV.exists():
        api_df = pd.read_csv(OWM_CSV, parse_dates=["ts"])
    elif EXT_WEATHER_CSV.exists():
        api_df = pd.read_csv(EXT_WEATHER_CSV, parse_dates=["ts"])
        if "api_rain_prob_60" in api_df.columns:
            api_df = api_df.rename(
                columns={
                    "api_rain_prob_60": "api_pop",
                    "api_rain_mm_60": "api_rain_1h",
                }
            )
        for col, default in [
            ("api_temp_c", 25.0),
            ("api_rh_pct", 70.0),
            ("api_uvi", 5.0),
        ]:
            if col not in api_df.columns:
                api_df[col] = default
    else:
        return pd.Series(
            {
                "api_pop": 0.2,
                "api_rain_1h": 0.0,
                "api_temp_c": 25.0,
                "api_rh_pct": 70.0,
                "api_uvi": 5.0,
            }
        )

    api_df = api_df.sort_values("ts")
    diff = (api_df["ts"] - ts_ref).abs()
    idx = diff.idxmin()
    row = api_df.loc[idx]
    # Giới hạn tối đa lệch 1h, nếu xa hơn dùng default
    if diff.loc[idx] > pd.Timedelta(hours=1):
        return pd.Series(
            {
                "api_pop": 0.2,
                "api_rain_1h": 0.0,
                "api_temp_c": 25.0,
                "api_rh_pct": 70.0,
                "api_uvi": 5.0,
            }
        )
    return row


def load_models():
    nowcast = joblib.load(MODEL_DIR / "xgb_nowcast.pkl")
    meta = {}
    try:
        with open(MODEL_DIR / "metadata.json", "r") as f:
            meta = json.load(f)
    except Exception:
        pass
    amount = None
    if (MODEL_DIR / "xgb_amount.pkl").exists():
        amount = joblib.load(MODEL_DIR / "xgb_amount.pkl")
    return nowcast, amount, meta


def decide_irrigation(soil_moist: float, rain_prob: float) -> tuple[bool, str]:
    # đơn giản: ưu tiên an toàn tưới khi đất rất khô và mưa thấp
    if soil_moist < 30:
        return True, "Đất rất khô (<30%)"
    if soil_moist < 40 and rain_prob < 0.4:
        return True, "Đất khô (<40%) và khả năng mưa thấp"
    if rain_prob > 0.6:
        return False, "Khả năng mưa cao (>60%)"
    return False, "Đất đủ ẩm hoặc mưa trung bình"


def main():
    sensor_df = load_sensor_buffer()
    api_row = load_api_row(sensor_df["ts"].iloc[-1])

    fv = compute_feature_from_window(sensor_df, api_row, interval_seconds=300)
    x = np.array(fv.to_list(), dtype="float32").reshape(1, -1)

    nowcast_model, amount_model, meta = load_models()
    threshold = float(meta.get("threshold_default", 0.5)) if meta else 0.5

    prob = float(nowcast_model.predict_proba(x)[0, 1])
    label = int(prob >= threshold)

    amount_mm = None
    if amount_model is not None:
        try:
            import xgboost as xgb

            if isinstance(amount_model, xgb.Booster):
                amount_mm = float(amount_model.predict(xgb.DMatrix(x))[0])
            else:
                amount_mm = float(amount_model.predict(x)[0])
        except Exception:
            amount_mm = None

    soil_m = float(sensor_df.iloc[-1]["soil_moist_pct"])
    should_irrigate, reason = decide_irrigation(soil_m, prob)

    output = {
        "timestamp": sensor_df.iloc[-1]["ts"].isoformat(),
        "features_used": FEATURE_NAMES,
        "predictions": {
            "rain_60min": {"probability": round(prob, 4), "label": label},
            "rain_amount_60min_mm": round(amount_mm, 2) if amount_mm is not None else None,
        },
        "sensor_ref": {
            "temp_c": round(float(sensor_df.iloc[-1]["temp_c"]), 2),
            "rh_pct": round(float(sensor_df.iloc[-1]["rh_pct"]), 2),
            "pressure_hpa": round(float(sensor_df.iloc[-1]["pressure_hpa"]), 2),
            "soil_moist_pct": round(soil_m, 2),
        },
        "api_ref": {
            "api_pop": round(float(api_row.get("api_pop", 0.2)), 3),
            "api_rain_1h": round(float(api_row.get("api_rain_1h", 0.0)), 2),
            "api_temp_c": round(float(api_row.get("api_temp_c", 25.0)), 2),
            "api_rh_pct": round(float(api_row.get("api_rh_pct", 70.0)), 2),
            "api_uvi": round(float(api_row.get("api_uvi", 5.0)), 2),
        },
        "recommendation": {
            "should_irrigate": should_irrigate,
            "reason": reason,
            "threshold_used": threshold,
        },
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

