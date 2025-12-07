import os
import json
import argparse
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

# Import feature engineering mới
from feature_engineering import (
    FEATURE_NAMES,
    compute_feature_from_window,
    cyclical_encode_month,
    cyclical_encode_hour,
)

# ====== Paths ======
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Sensor data:
# - RAW_CSV: dữ liệu sensor thật (tạo từ prepare_training_data.py)
# - SYNTH_CSV: dữ liệu sensor synthetic (tạo từ generate_synthetic_sensor_from_labels.py)
RAW_CSV = DATA_DIR / "sensor_raw_60d.csv"
SYNTH_CSV = DATA_DIR / "sensor_raw_60d_synth.csv"

# Labels:
LBL_CSV = DATA_DIR / "labels_rain_final.csv"
LBL_CSV = LBL_CSV if LBL_CSV.exists() else (DATA_DIR / "labels_rain_60d.csv")

# API macro weather data (ưu tiên 3 years data)
OWM_3Y_CSV = DATA_DIR / "owm_history_3years_final.csv"  # Dữ liệu 3 năm (ưu tiên)
OWM_CSV = DATA_DIR / "owm_history.csv"  # Dữ liệu từ fetch_owm_data.py
EXT_WEATHER_CSV = DATA_DIR / "external_weather_60d.csv"  # Dữ liệu cũ (nếu có)


def load_and_merge_data() -> pd.DataFrame:
    """
    Load và merge dữ liệu sensor + API + labels.
    
    Returns:
        DataFrame đã merge với đầy đủ thông tin
    """
    print("📂 Loading data...")
    
    # 1. Load sensor data
    sensor_path = None
    raw = None

    if RAW_CSV.exists():
        raw = pd.read_csv(RAW_CSV, parse_dates=["ts"])
        sensor_path = RAW_CSV
    elif SYNTH_CSV.exists():
        raw = pd.read_csv(SYNTH_CSV, parse_dates=["ts"])
        sensor_path = SYNTH_CSV
    else:
        raise FileNotFoundError(
            f"❌ No sensor data found. Need either {RAW_CSV.name} or {SYNTH_CSV.name} "
            "in the data/ folder."
        )

    # Ensure tz-naive for consistent merge
    raw["ts"] = pd.to_datetime(raw["ts"]).dt.tz_localize(None)

    raw = raw.sort_values(["device_id", "ts"]).reset_index(drop=True)
    print(f"   ✓ Sensor data: {len(raw)} records (from {sensor_path.name})")

    # Nếu dùng sensor thật mà số dòng quá ít, gợi ý dùng synthetic
    if sensor_path == RAW_CSV and len(raw) < 1000:
        warn = (
            f"⚠️  Only {len(raw)} real sensor records found. "
            f"For better training, consider generating synthetic data via:\n"
            f"      python src/generate_synthetic_sensor_from_labels.py\n"
            f"   (sau đó file {SYNTH_CSV.name} sẽ được ưu tiên nếu bạn xóa hoặc "
            f"đổi tên {RAW_CSV.name})."
        )
        print(warn)
    
    # 2. Load labels
    if not LBL_CSV.exists():
        raise FileNotFoundError(f"❌ Labels not found: {LBL_CSV}")
    lbl = pd.read_csv(LBL_CSV, parse_dates=["ts"])
    lbl["ts"] = pd.to_datetime(lbl["ts"]).dt.tz_localize(None)
    print(f"   ✓ Labels: {len(lbl)} records")
    
    # 3. Load API data (ưu tiên 3 years data, fallback owm_history.csv, cuối cùng external_weather_60d.csv)
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
        # Map columns từ external_weather format sang format chuẩn
        if "api_rain_prob_60" in api_df.columns:
            api_df = api_df.rename(columns={
                "api_rain_prob_60": "api_pop",
                "api_rain_mm_60": "api_rain_1h",
            })
        # Thêm các cột còn thiếu nếu cần
        if "api_temp_c" not in api_df.columns:
            api_df["api_temp_c"] = 25.0  # Default
        if "api_rh_pct" not in api_df.columns:
            api_df["api_rh_pct"] = 70.0  # Default
        if "api_uvi" not in api_df.columns:
            api_df["api_uvi"] = 5.0  # Default
        print(f"   ✓ External weather data: {len(api_df)} records (from {EXT_WEATHER_CSV})")
    else:
        print(f"   ⚠️  No API data found. Will use synthetic API values.")
    
    # 4. Merge sensor + labels - Cải thiện để có nhiều mẫu hơn
    # Kiểm tra xem labels có device_id không
    if "device_id" in lbl.columns:
        # Labels có device_id → merge theo ts + device_id
        df = raw.merge(
            lbl[["ts", "device_id", "rain_next_60"]],
            on=["ts", "device_id"],
            how="inner",
        )
    else:
        # Labels không có device_id → merge theo timestamp gần nhất
        # Sử dụng merge_asof để tìm label gần nhất trong vòng 5 phút
        print("   ⚠️  Labels không có device_id. Merge theo timestamp gần nhất (tolerance 5min).")
        raw_sorted = raw.sort_values("ts").reset_index(drop=True)
        lbl_sorted = lbl.sort_values("ts").reset_index(drop=True)
        
        df = pd.merge_asof(
            raw_sorted,
            lbl_sorted[["ts", "rain_next_60"]],
            on="ts",
            direction="nearest",
            tolerance=pd.Timedelta("5min"),  # Cho phép sai lệch tối đa 5 phút
        )
        # device_id đã có từ raw (sensor data)
    
    df = df.sort_values(["device_id", "ts"]).reset_index(drop=True)
    matched_count = len(df)
    print(f"   ✓ Merged sensor + labels: {matched_count} records")
    if matched_count < len(raw) * 0.5:
        print(f"   ⚠️  Warning: Only {matched_count/len(raw)*100:.1f}% of sensor data matched with labels.")
        print(f"      Consider checking timestamp alignment between sensor and labels.")
    
    # 5. Merge API data (nếu có) - Cải thiện merge để có nhiều mẫu hơn
    if api_df is not None:
        # Merge theo timestamp gần nhất (trong vòng 1 giờ để có nhiều mẫu hơn)
        # Sử dụng merge_asof để tìm timestamp gần nhất
        api_df_sorted = api_df.sort_values("ts").reset_index(drop=True)
        df_sorted = df.sort_values("ts").reset_index(drop=True)
        
        # Chuẩn bị columns để merge
        api_cols_to_merge = ["ts"]
        for col in ["api_pop", "api_rain_1h", "api_temp_c", "api_rh_pct", "api_uvi", "api_weather_code"]:
            if col in api_df_sorted.columns:
                api_cols_to_merge.append(col)
        
        # Merge_asof: tìm API record gần nhất trong vòng 1 giờ
        merged = pd.merge_asof(
            df_sorted,
            api_df_sorted[api_cols_to_merge],
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
    else:
        # Synthetic API values (nếu không có API data)
        df["api_pop"] = 0.2  # Default
        df["api_rain_1h"] = 0.0
        df["api_temp_c"] = df["temp_c"]
        df["api_rh_pct"] = df["rh_pct"]
        df["api_uvi"] = 5.0
        df["api_weather_code"] = 800
        print(f"   ⚠️  Using synthetic API values")
    
    return df


def build_features_for_training(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Tính features cho training từ DataFrame đã merge.
    
    Vì dữ liệu training là theo giờ (hoặc 5 phút), ta tính features trực tiếp
    thay vì dùng rolling window như inference.
    
    Args:
        df: DataFrame đã merge sensor + API + labels
    
    Returns:
        (df_with_features, X, y)
    """
    print("\n🔧 Computing features...")
    
    df = df.copy()
    df = df.sort_values(["device_id", "ts"]).reset_index(drop=True)
    
    # Group by device để tính features theo từng device
    def compute_features_group(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values("ts").reset_index(drop=True)
        
        # 1. pressure_slope_1h = P_t - P_(t-1h)
        # Với dữ liệu 5 phút, 1h = 12 điểm
        g["pressure_slope_1h"] = g["pressure_hpa"].diff(12).fillna(0.0)
        
        # 2. temp_drop_15m = T_(t-15m) - T_t
        # Với dữ liệu 5 phút, 15m = 3 điểm
        g["temp_drop_15m"] = (g["temp_c"].shift(3) - g["temp_c"]).fillna(0.0)
        
        # 3. rh_rise_15m = RH_t - RH_(t-15m)
        g["rh_rise_15m"] = (g["rh_pct"] - g["rh_pct"].shift(3)).fillna(0.0)
        
        # 4. soil_moist_smooth = rolling mean 5 phút (1 điểm với 5 phút interval)
        g["soil_moist_smooth"] = g["soil_moist_pct"].rolling(window=1, min_periods=1).mean()
        
        # 5. Dew point diff
        from feature_engineering import compute_dew_point
        g["dew_sensor"] = g.apply(
            lambda row: compute_dew_point(row["temp_c"], row["rh_pct"]), axis=1
        )
        g["dew_api"] = g.apply(
            lambda row: compute_dew_point(row["api_temp_c"], row["api_rh_pct"]), axis=1
        )
        g["dew_point_diff"] = g["dew_sensor"] - g["dew_api"]
        
        # 6. temp_bias
        g["temp_bias"] = g["api_temp_c"] - g["temp_c"]
        
        # 7. Cyclical encoding
        g["month"] = g["ts"].dt.month
        g["hour"] = g["ts"].dt.hour
        month_enc = g["month"].apply(lambda m: cyclical_encode_month(m))
        hour_enc = g["hour"].apply(lambda h: cyclical_encode_hour(h))
        g["month_sin"] = month_enc.apply(lambda x: x["month_sin"])
        g["month_cos"] = month_enc.apply(lambda x: x["month_cos"])
        g["hour_sin"] = hour_enc.apply(lambda x: x["hour_sin"])
        g["hour_cos"] = hour_enc.apply(lambda x: x["hour_cos"])
        
        # 8. API features (nếu có trong df)
        # api_pop, api_rain_1h, api_uvi đã có từ merge API data
        if "api_pop" not in g.columns:
            g["api_pop"] = 0.2  # Default
        if "api_rain_1h" not in g.columns:
            g["api_rain_1h"] = 0.0  # Default
        if "api_uvi" not in g.columns:
            g["api_uvi"] = 5.0  # Default
        
        # Đảm bảo uvi_index = api_uvi (theo feature_engineering.py)
        g["uvi_index"] = g["api_uvi"].fillna(5.0)
        
        return g
    
    df = df.groupby("device_id", group_keys=False).apply(compute_features_group)
    df = df.dropna(subset=FEATURE_NAMES + ["rain_next_60"]).reset_index(drop=True)
    
    # Extract features và labels
    X = df[FEATURE_NAMES].astype("float32").values
    y = df["rain_next_60"].astype(int).values
    
    print(f"   ✓ Features computed: {X.shape}")
    print(f"   ✓ Positive samples: {y.sum()} / {len(y)} ({y.mean()*100:.1f}%)")
    
    return df, X, y


def train_and_save(save_mode: str = "wrapper") -> None:
    """Train model và lưu."""
    from wrappers import XGBBoosterWithThreshold
    
    # Load và merge data
    df = load_and_merge_data()
    
    # Compute features
    df_feat, X, y = build_features_for_training(df)
    
    # Tính scale_pos_weight
    pos, neg = (y == 1).sum(), (y == 0).sum()
    scale_pos_weight = float(neg) / max(1.0, float(pos))
    print(f"\n📊 Class distribution:")
    print(f"   Positive (rain): {pos} ({pos/len(y)*100:.1f}%)")
    print(f"   Negative (no rain): {neg} ({neg/len(y)*100:.1f}%)")
    print(f"   scale_pos_weight (auto): {scale_pos_weight:.2f}")
    print(f"   scale_pos_weight (báo cáo): 8.5")
    
    # Split train/val với stratified để đảm bảo validation có positive samples
    try:
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=0.15, shuffle=True, random_state=42, stratify=y
        )
    except ValueError as e:
        # Nếu không thể stratified (quá ít positive), dùng shuffle thường
        print(f"   ⚠️  Cannot use stratified split: {e}. Using regular shuffle.")
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=0.15, shuffle=True, random_state=42
        )
    
    # Hiển thị class distribution trong train/val
    pos_tr, neg_tr = (ytr == 1).sum(), (ytr == 0).sum()
    pos_te, neg_te = (yte == 1).sum(), (yte == 0).sum()
    print(f"\n📊 Train/Val Split:")
    print(f"   Train: {len(ytr)} samples (pos={pos_tr}, neg={neg_tr}, pos%={pos_tr/len(ytr)*100:.1f}%)")
    print(f"   Val:   {len(yte)} samples (pos={pos_te}, neg={neg_te}, pos%={pos_te/len(yte)*100:.1f}%)")
    
    if pos_te == 0:
        print(f"   ⚠️  WARNING: Validation set has NO positive samples!")
        print(f"   → Model cannot evaluate properly. Consider:")
        print(f"      - Using stratified split (already tried)")
        print(f"      - Reducing test_size")
        print(f"      - Checking if data has enough positive samples")
    
    dtrain, dvalid = xgb.DMatrix(Xtr, label=ytr), xgb.DMatrix(Xte, label=yte)
    
    # Hyperparameter theo báo cáo - Điều chỉnh để cải thiện Precision
    # Tăng scale_pos_weight để giảm false positives (cải thiện Precision)
    # scale_pos_weight cao hơn → model sẽ conservative hơn khi dự đoán positive
    scale_pos_weight_adjusted = max(8.5, scale_pos_weight * 1.2)  # Tăng 20% so với auto
    
    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",  # Báo cáo: auc
        "eta": 0.05,  # Báo cáo: learning_rate = 0.05
        "max_depth": 6,  # Báo cáo: 6
        "subsample": 0.8,  # Báo cáo: 0.8
        "colsample_bytree": 0.8,  # Thêm để tăng tính tổng quát
        "lambda": 1.5,  # Tăng L2 regularization để giảm overfitting
        "alpha": 0.5,  # Thêm L1 regularization để feature selection
        "scale_pos_weight": scale_pos_weight_adjusted,  # Điều chỉnh để cải thiện Precision
    }
    print(f"   scale_pos_weight (adjusted for Precision): {scale_pos_weight_adjusted:.2f}")
    
    print(f"\n🚀 Training XGBoost...")
    print(f"   Training samples: {len(Xtr)}")
    print(f"   Validation samples: {len(Xte)}")
    print(f"   Features: {Xtr.shape[1]} ({', '.join(FEATURE_NAMES[:5])}...)")
    print(f"\n   Hyperparameters:")
    for k, v in params.items():
        print(f"      {k}: {v}")
    
    print(f"\n   Training progress (showing every 10 rounds):")
    print(f"   {'Round':<8} {'Train-AUC':<12} {'Valid-AUC':<12} {'Status':<15}")
    print(f"   {'-'*8} {'-'*12} {'-'*12} {'-'*15}")
    
    bst = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=200,  # Báo cáo: n_estimators (có early stopping)
        evals=[(dtrain, "train"), (dvalid, "valid")],
        early_stopping_rounds=50,
        verbose_eval=10,  # Print mỗi 10 rounds
    )
    
    print(f"\n   ✓ Training completed!")
    print(f"   Best iteration: {bst.best_iteration + 1} / {bst.num_boosted_rounds()}")
    print(f"   Best score: {bst.best_score:.6f}")
    
    # Evaluate
    proba = bst.predict(dvalid, iteration_range=(0, bst.best_iteration + 1))
    
    # Kiểm tra xem có positive samples trong validation không
    has_positive = (yte == 1).sum() > 0
    
    if has_positive:
        auc = roc_auc_score(yte, proba)
        prauc = average_precision_score(yte, proba)
    else:
        auc = float('nan')
        prauc = float('nan')
        print(f"\n   ⚠️  Cannot compute AUC (no positive samples in validation)")
    
    pred = (proba >= 0.5).astype(int)
    prec, rec, f1, _ = precision_recall_fscore_support(yte, pred, average="binary", zero_division=0)
    
    print(f"\n📈 Evaluation Results:")
    if has_positive:
        print(f"   AUC-ROC: {auc:.4f}")
        print(f"   PR-AUC: {prauc:.4f}")
    else:
        print(f"   AUC-ROC: N/A (no positive samples)")
        print(f"   PR-AUC: N/A (no positive samples)")
    print(f"   @0.50  Acc: {(pred==yte).mean():.4f}  Prec: {prec:.4f}  Rec: {rec:.4f}  F1: {f1:.4f}")
    print(f"\n   Confusion Matrix:")
    cm = confusion_matrix(yte, pred)
    print(cm)
    print(f"   (Rows: True labels, Cols: Predicted labels)")
    print(f"   [[TN, FP],")
    print(f"    [FN, TP]]")
    print(f"\n   Classification Report:")
    print(classification_report(yte, pred, digits=4, zero_division=0))
    
    # Tìm threshold tốt nhất (theo F1)
    thr_grid = np.linspace(0.1, 0.9, 33)
    best_thr, best_f1 = 0.5, -1
    for th in thr_grid:
        pr = (proba >= th).astype(int)
        _, _, f1_, _ = precision_recall_fscore_support(yte, pr, average="binary", zero_division=0)
        if f1_ > best_f1:
            best_f1, best_thr = f1_, float(th)
    print(f"\n   Best threshold (F1): {best_thr:.3f} (F1={best_f1:.4f})")
    
    # Save metadata
    meta = {
        "features": FEATURE_NAMES,
        "threshold_default": best_thr,
        "hyperparameters": params,
        "metrics": {
            "auc_roc": float(auc),
            "pr_auc": float(prauc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "best_threshold": best_thr,
        },
        "data_info": {
            "n_samples": len(X),
            "n_train": len(Xtr),
            "n_val": len(Xte),
            "positive_rate": float(y.mean()),
        },
    }
    with open(MODEL_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # Save model
    if save_mode == "wrapper":
        model = XGBBoosterWithThreshold(bst, threshold=best_thr)
        joblib.dump(model, MODEL_DIR / "xgb_nowcast.pkl")
        print(f"\n✅ Saved model: {MODEL_DIR / 'xgb_nowcast.pkl'}")
    elif save_mode == "raw":
        payload = {
            "booster_bytes": bst.save_raw(),
            "best_iteration": int(getattr(bst, "best_iteration", -1)),
            "threshold": best_thr,
        }
        joblib.dump(payload, MODEL_DIR / "xgb_nowcast.pkl")
        print(f"\n✅ Saved model (raw): {MODEL_DIR / 'xgb_nowcast.pkl'}")
    else:
        raise ValueError("save_mode must be 'wrapper' or 'raw'")
    
    print(f"✅ Saved metadata: {MODEL_DIR / 'metadata.json'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--save-mode",
        choices=["wrapper", "raw"],
        default="wrapper",
        help="wrapper: XGBBoosterWithThreshold | raw: booster_bytes+threshold",
    )
    args = ap.parse_args()
    
    train_and_save(args.save_mode)

