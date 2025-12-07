# src/train_xgb_amount.py
import json
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from feature_engineering import FEATURE_NAMES, compute_dew_point

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Data files
RAW_CSV = DATA_DIR / "sensor_raw_60d.csv"
SYNTH_CSV = DATA_DIR / "sensor_raw_60d_synth.csv"
# Labels: Ưu tiên labels_rain_final.csv (3 năm data, có đầy đủ rain_amount_next_60_mm)
LBL_CSV = DATA_DIR / "labels_rain_final.csv"
LBL_CSV = LBL_CSV if LBL_CSV.exists() else (DATA_DIR / "labels_rain_60d_fixed.csv")
LBL_CSV = LBL_CSV if LBL_CSV.exists() else (DATA_DIR / "labels_rain_60d.csv")
# API macro weather data (ưu tiên 3 years data)
OWM_3Y_CSV = DATA_DIR / "owm_history_3years_final.csv"  # Dữ liệu 3 năm (ưu tiên)
OWM_CSV = DATA_DIR / "owm_history.csv"  # Dữ liệu từ fetch_owm_data.py
EXT_WEATHER_CSV = DATA_DIR / "external_weather_60d.csv"  # Dữ liệu cũ (nếu có)


def _load_sensor() -> pd.DataFrame:
    if RAW_CSV.exists():
        df = pd.read_csv(RAW_CSV, parse_dates=["ts"])
        src = RAW_CSV
    elif SYNTH_CSV.exists():
        df = pd.read_csv(SYNTH_CSV, parse_dates=["ts"])
        src = SYNTH_CSV
    else:
        raise FileNotFoundError(f"No sensor data: {RAW_CSV.name} or {SYNTH_CSV.name}")
    # Ensure tz-naive for consistent merge
    df["ts"] = pd.to_datetime(df["ts"]).dt.tz_localize(None)
    df = df.sort_values(["device_id", "ts"]).reset_index(drop=True)
    print(f"   ✓ Sensor data: {len(df)} records (from {src.name})")
    return df


def _load_labels() -> pd.DataFrame:
    if not LBL_CSV.exists():
        raise FileNotFoundError(f"Labels not found: {LBL_CSV}")
    df = pd.read_csv(LBL_CSV, parse_dates=["ts"])
    df["ts"] = pd.to_datetime(df["ts"]).dt.tz_localize(None)
    if "rain_amount_next_60_mm" not in df.columns:
        raise ValueError("Labels missing 'rain_amount_next_60_mm'.")
    print(f"   ✓ Labels: {len(df)} records")
    return df


def _load_api() -> pd.DataFrame:
    api_df = None
    if OWM_3Y_CSV.exists():
        api_df = pd.read_csv(OWM_3Y_CSV, parse_dates=["ts"])
        api_df["ts"] = pd.to_datetime(api_df["ts"]).dt.tz_localize(None)
        print(f"   ✓ OWM 3Y API data: {len(api_df)} records (from {OWM_3Y_CSV.name})")
        print(f"      Time range: {api_df['ts'].min()} → {api_df['ts'].max()}")
    elif OWM_CSV.exists():
        api_df = pd.read_csv(OWM_CSV, parse_dates=["ts"])
        api_df["ts"] = pd.to_datetime(api_df["ts"]).dt.tz_localize(None)
        print(f"   ✓ OWM API data: {len(api_df)} records (from {OWM_CSV.name})")
    elif EXT_WEATHER_CSV.exists():
        api_df = pd.read_csv(EXT_WEATHER_CSV, parse_dates=["ts"])
        api_df["ts"] = pd.to_datetime(api_df["ts"]).dt.tz_localize(None)
        if "api_rain_prob_60" in api_df.columns:
            api_df = api_df.rename(
                columns={"api_rain_prob_60": "api_pop", "api_rain_mm_60": "api_rain_1h"}
            )
        for col, default in [
            ("api_temp_c", 25.0),
            ("api_rh_pct", 70.0),
            ("api_uvi", 5.0),
        ]:
            if col not in api_df.columns:
                api_df[col] = default
        print(f"   ✓ External weather data: {len(api_df)} records (from {EXT_WEATHER_CSV.name})")
    else:
        raise FileNotFoundError("No API data (owm_history_3years_final.csv, owm_history.csv or external_weather_60d.csv)")
    return api_df


def load_and_merge() -> pd.DataFrame:
    print("📂 Loading data...")
    sensor = _load_sensor()
    labels = _load_labels()
    api = _load_api()

    # Merge sensor + labels - Cải thiện để có nhiều mẫu hơn
    if "device_id" in labels.columns:
        # Labels có device_id → merge theo ts + device_id
        df = sensor.merge(
            labels[["ts", "device_id", "rain_amount_next_60_mm"]],
            on=["ts", "device_id"],
            how="inner",
        )
    else:
        # Labels không có device_id → merge theo timestamp gần nhất
        print("   ⚠️  Labels không có device_id. Merge theo timestamp gần nhất (tolerance 5min).")
        sensor_sorted = sensor.sort_values("ts").reset_index(drop=True)
        labels_sorted = labels.sort_values("ts").reset_index(drop=True)
        
        df = pd.merge_asof(
            sensor_sorted,
            labels_sorted[["ts", "rain_amount_next_60_mm"]],
            on="ts",
            direction="nearest",
            tolerance=pd.Timedelta("5min"),  # Cho phép sai lệch tối đa 5 phút
        )
        # device_id đã có từ sensor
    
    matched_count = len(df)
    print(f"   ✓ Merged sensor + labels: {matched_count} records")
    if matched_count < len(sensor) * 0.5:
        print(f"   ⚠️  Warning: Only {matched_count/len(sensor)*100:.1f}% of sensor data matched with labels.")
    
    # Merge API data - Cải thiện merge để có nhiều mẫu hơn
    api_sorted = api.sort_values("ts").reset_index(drop=True)
    df_sorted = df.sort_values("ts").reset_index(drop=True)
    
    # Chuẩn bị columns để merge
    api_cols_to_merge = ["ts"]
    for col in ["api_pop", "api_rain_1h", "api_temp_c", "api_rh_pct", "api_uvi", "api_weather_code"]:
        if col in api_sorted.columns:
            api_cols_to_merge.append(col)
    
    # Merge_asof: tìm API record gần nhất trong vòng 1 giờ
    merged = pd.merge_asof(
        df_sorted,
        api_sorted[api_cols_to_merge],
        on="ts",
        direction="nearest",
        tolerance=pd.Timedelta("1h"),  # Cho phép sai lệch tối đa 1 giờ
    )
    
    # Fill missing API values với giá trị hợp lý
    merged["api_pop"] = merged["api_pop"].fillna(0.2) if "api_pop" in merged.columns else 0.2
    merged["api_rain_1h"] = merged["api_rain_1h"].fillna(0.0) if "api_rain_1h" in merged.columns else 0.0
    merged["api_temp_c"] = merged["api_temp_c"].fillna(merged["temp_c"]) if "api_temp_c" in merged.columns else merged["temp_c"]
    merged["api_rh_pct"] = merged["api_rh_pct"].fillna(merged["rh_pct"]) if "api_rh_pct" in merged.columns else merged["rh_pct"]
    merged["api_uvi"] = merged["api_uvi"].fillna(5.0) if "api_uvi" in merged.columns else 5.0
    if "api_weather_code" not in merged.columns:
        merged["api_weather_code"] = 800
    
    df = merged.sort_values(["device_id", "ts"]).reset_index(drop=True)
    
    api_matched = df["api_pop"].notna().sum()
    print(f"   ✓ Merged API data: {api_matched} / {len(df)} records have API data ({api_matched/len(df)*100:.1f}%)")
    
    return df


def build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    print("\n🔧 Computing features...")
    df = df.copy()
    df = df.sort_values(["device_id", "ts"]).reset_index(drop=True)

    def per_device(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values("ts").reset_index(drop=True)
        # Windows based on 5-min data (12 for 1h, 3 for 15m)
        g["pressure_slope_1h"] = g["pressure_hpa"].diff(12).fillna(0.0)
        g["temp_drop_15m"] = (g["temp_c"].shift(3) - g["temp_c"]).fillna(0.0)
        g["rh_rise_15m"] = (g["rh_pct"] - g["rh_pct"].shift(3)).fillna(0.0)
        g["soil_moist_smooth"] = (
            g["soil_moist_pct"].rolling(window=1, min_periods=1).mean()
        )
        # Dew points
        g["dew_sensor"] = g.apply(
            lambda r: compute_dew_point(r["temp_c"], r["rh_pct"]), axis=1
        )
        g["dew_api"] = g.apply(
            lambda r: compute_dew_point(r["api_temp_c"], r["api_rh_pct"]), axis=1
        )
        g["dew_point_diff"] = g["dew_sensor"] - g["dew_api"]
        g["temp_bias"] = g["api_temp_c"] - g["temp_c"]
        # Time encodings
        g["month"] = g["ts"].dt.month
        g["hour"] = g["ts"].dt.hour
        from feature_engineering import cyclical_encode_month, cyclical_encode_hour

        g["month_sin"] = g["month"].apply(lambda m: cyclical_encode_month(m)["month_sin"])
        g["month_cos"] = g["month"].apply(lambda m: cyclical_encode_month(m)["month_cos"])
        g["hour_sin"] = g["hour"].apply(lambda h: cyclical_encode_hour(h)["hour_sin"])
        g["hour_cos"] = g["hour"].apply(lambda h: cyclical_encode_hour(h)["hour_cos"])
        
        # Đảm bảo uvi_index = api_uvi
        g["uvi_index"] = g["api_uvi"].fillna(5.0) if "api_uvi" in g.columns else 5.0
        
        return g

    df = df.groupby("device_id", group_keys=False).apply(per_device)
    df = df.dropna(subset=FEATURE_NAMES + ["rain_amount_next_60_mm"]).reset_index(drop=True)

    X = df[FEATURE_NAMES].astype("float32").values
    y = df["rain_amount_next_60_mm"].astype("float32").clip(lower=0.0).values
    
    print(f"   ✓ Features computed: {X.shape}")
    print(f"   ✓ Target stats: min={y.min():.2f}mm, max={y.max():.2f}mm, mean={y.mean():.2f}mm, median={np.median(y):.2f}mm")
    print(f"   ✓ Non-zero samples: {(y > 0).sum()} / {len(y)} ({(y > 0).mean()*100:.1f}%)")
    
    return df, X, y


def main():
    print("=" * 70)
    print("🌧️  TRAINING XGBOOST REGRESSION MODEL FOR RAIN AMOUNT PREDICTION")
    print("=" * 70)
    
    df, X, y = build_features(load_and_merge())

    # Split train/val - Dùng shuffle để đảm bảo validation có cả mưa và không mưa
    # Với regression, ta cần đảm bảo validation set có đủ samples có mưa (>0)
    # Nếu dùng time-based split (shuffle=False), validation có thể chỉ có 0mm
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.15, shuffle=True, random_state=42
    )
    
    print(f"\n📊 Train/Val Split:")
    print(f"   Train: {len(ytr)} samples (mean={ytr.mean():.2f}mm, max={ytr.max():.2f}mm, non-zero={(ytr>0).sum()} samples)")
    print(f"   Val:   {len(yte)} samples (mean={yte.mean():.2f}mm, max={yte.max():.2f}mm, non-zero={(yte>0).sum()} samples)")
    
    # Cảnh báo nếu validation set không có mưa
    if (yte > 0).sum() == 0:
        print(f"\n   ⚠️  WARNING: Validation set has NO rain samples!")
        print(f"   → Model cannot evaluate properly. Consider:")
        print(f"      - Using shuffle=True (already done)")
        print(f"      - Checking if data has enough rain samples")
        print(f"      - Reducing test_size")
    elif (yte > 0).sum() < 10:
        print(f"\n   ⚠️  Warning: Validation set has only {(yte>0).sum()} rain samples (may affect evaluation)")
    
    dtrain, dvalid = xgb.DMatrix(Xtr, label=ytr), xgb.DMatrix(Xte, label=yte)

    params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "eta": 0.05,
        "max_depth": 6,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "lambda": 1.5,  # Tăng L2 regularization
        "alpha": 0.5,   # Thêm L1 regularization
    }
    
    print(f"\n🚀 Training XGBoost...")
    print(f"   Training samples: {len(Xtr)}")
    print(f"   Validation samples: {len(Xte)}")
    print(f"   Features: {Xtr.shape[1]} ({', '.join(FEATURE_NAMES[:5])}...)")
    print(f"\n   Hyperparameters:")
    for k, v in params.items():
        print(f"      {k}: {v}")
    
    print(f"\n   Training progress (showing every 20 rounds):")
    print(f"   {'Round':<8} {'Train-RMSE':<15} {'Valid-RMSE':<15} {'Status':<15}")
    print(f"   {'-'*8} {'-'*15} {'-'*15} {'-'*15}")

    bst = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=800,
        evals=[(dtrain, "train"), (dvalid, "valid")],
        early_stopping_rounds=80,
        verbose_eval=20,  # Print mỗi 20 rounds
    )

    print(f"\n   ✓ Training completed!")
    print(f"   Best iteration: {bst.best_iteration + 1} / {bst.num_boosted_rounds()}")
    print(f"   Best RMSE: {bst.best_score:.4f}")

    pred = bst.predict(dvalid, iteration_range=(0, bst.best_iteration + 1))
    pred = np.clip(pred, 0.0, None)  # Đảm bảo không âm
    
    mae = mean_absolute_error(yte, pred)
    rmse = float(np.sqrt(mean_squared_error(yte, pred)))
    r2 = r2_score(yte, pred)
    
    print(f"\n📈 Evaluation Results:")
    print(f"   MAE:  {mae:.3f} mm (Mean Absolute Error)")
    print(f"   RMSE: {rmse:.3f} mm (Root Mean Squared Error)")
    print(f"   R²:   {r2:.3f} (Coefficient of Determination)")
    
    # Phân tích lỗi theo cường độ mưa
    print(f"\n📊 Error Analysis by Rain Intensity:")
    small_mask = yte < 2.0
    medium_mask = (yte >= 2.0) & (yte < 5.0)
    large_mask = yte >= 5.0
    
    if small_mask.sum() > 0:
        mae_small = mean_absolute_error(yte[small_mask], pred[small_mask])
        print(f"   Small rain (<2mm):   MAE={mae_small:.3f}mm ({small_mask.sum()} samples)")
    if medium_mask.sum() > 0:
        mae_medium = mean_absolute_error(yte[medium_mask], pred[medium_mask])
        print(f"   Medium rain (2-5mm):  MAE={mae_medium:.3f}mm ({medium_mask.sum()} samples)")
    if large_mask.sum() > 0:
        mae_large = mean_absolute_error(yte[large_mask], pred[large_mask])
        print(f"   Large rain (>5mm):    MAE={mae_large:.3f}mm ({large_mask.sum()} samples)")

    joblib.dump(bst, MODEL_DIR / "xgb_amount.pkl")
    meta = {
        "features": FEATURE_NAMES,
        "target": "rain_amount_next_60_mm",
        "note": "XGBoost regression for rainfall amount in next 60 minutes",
        "hyperparameters": params,
        "metrics": {
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),
        },
        "data_info": {
            "n_samples": len(X),
            "n_train": len(Xtr),
            "n_val": len(Xte),
            "target_mean": float(y.mean()),
            "target_max": float(y.max()),
        },
    }
    with open(MODEL_DIR / "metadata_amount.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved model: {MODEL_DIR / 'xgb_amount.pkl'}")
    print(f"✅ Saved metadata: {MODEL_DIR / 'metadata_amount.json'}")
    print("\nDone.")


if __name__ == "__main__":
    main()
