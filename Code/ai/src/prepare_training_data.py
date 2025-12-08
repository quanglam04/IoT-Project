"""
Script chuẩn hóa dữ liệu training theo báo cáo IoT.

Chức năng:
1. Convert sensor_live.csv → sensor_raw_60d.csv (15s, 4 fields: temp, rh, pressure, soil_moist)
2. Tạo labels_rain_60d.csv từ dữ liệu thật (từ owm_history_3years hoặc API)
3. Tạo irrigation_events_60d.csv giả lập dựa trên sensor + labels
4. Kiểm tra external_weather_60d.csv (có thể không cần nữa)

Chạy: python src/prepare_training_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

# Input files
SENSOR_LIVE = DATA_DIR / "sensor_live.csv"
OWM_HISTORY_3Y = DATA_DIR / "owm_history_3years.csv"
OWM_HISTORY = DATA_DIR / "owm_history.csv"

# Output files
SENSOR_RAW_60D = DATA_DIR / "sensor_raw_60d.csv"
LABELS_RAIN_60D = DATA_DIR / "labels_rain_60d.csv"
IRRIGATION_EVENTS_60D = DATA_DIR / "irrigation_events_60d.csv"


def convert_sensor_live_to_raw_60d() -> None:
    """
    Convert sensor_live.csv → sensor_raw_60d.csv
    
    Yêu cầu:
    - Format: 15 giây/bản ghi (hoặc giữ nguyên nếu đã đúng)
    - Fields: ts, device_id, temp_c, rh_pct, pressure_hpa, soil_moist_pct
    - Bỏ: light, rain_mm_5min (nếu có)
    - Lấy 60 ngày gần nhất
    """
    print("=" * 70)
    print("1️⃣  Converting sensor_live.csv → sensor_raw_60d.csv")
    print("=" * 70)
    
    if not SENSOR_LIVE.exists():
        print(f"❌ File not found: {SENSOR_LIVE}")
        print("   → Tạo file sensor_raw_60d.csv rỗng (bạn cần collect data từ MQTT trước)")
        # Tạo file rỗng với đúng format
        df_empty = pd.DataFrame(columns=[
            "ts", "device_id", "temp_c", "rh_pct", "pressure_hpa", "soil_moist_pct"
        ])
        df_empty.to_csv(SENSOR_RAW_60D, index=False)
        return
    
    # Load sensor_live
    df = pd.read_csv(SENSOR_LIVE, parse_dates=["ts"])
    print(f"   ✓ Loaded {len(df)} records from sensor_live.csv")
    
    # Kiểm tra columns
    required_cols = ["ts", "device_id", "temp_c", "rh_pct", "soil_moist_pct"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"   ❌ Missing columns: {missing_cols}")
        return
    
    # Kiểm tra pressure_hpa
    if "pressure_hpa" not in df.columns:
        if "pressure" in df.columns:
            df["pressure_hpa"] = df["pressure"]
            print("   ✓ Mapped 'pressure' → 'pressure_hpa'")
        else:
            print("   ⚠️  No pressure column found. Adding default value 1013.25")
            df["pressure_hpa"] = 1013.25  # Standard atmospheric pressure
    
    # Bỏ các cột không cần
    cols_to_drop = ["light"] if "light" in df.columns else []
    if "rain_mm_5min" in df.columns:
        cols_to_drop.append("rain_mm_5min")
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        print(f"   ✓ Dropped columns: {cols_to_drop}")
    
    # Chọn columns cần thiết
    df = df[["ts", "device_id", "temp_c", "rh_pct", "pressure_hpa", "soil_moist_pct"]]
    
    # Chuẩn hóa timezone: Convert về naive (UTC)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    if df["ts"].dt.tz is not None:
        df["ts"] = df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    # Sort theo thời gian
    df = df.sort_values(["device_id", "ts"]).reset_index(drop=True)
    
    # Lấy 60 ngày gần nhất
    if len(df) > 0:
        latest_ts = df["ts"].max()
        cutoff_ts = latest_ts - timedelta(days=60)
        df = df[df["ts"] >= cutoff_ts].reset_index(drop=True)
        print(f"   ✓ Filtered to last 60 days: {len(df)} records")
        print(f"   Time range: {df['ts'].min()} → {df['ts'].max()}")
    
    # Kiểm tra tần suất
    if len(df) > 1:
        time_diffs = df["ts"].diff().dt.total_seconds()
        avg_interval = time_diffs[time_diffs > 0].median()
        print(f"   ✓ Average interval: {avg_interval:.1f} seconds")
        
        if avg_interval > 20:  # Nếu > 20s, có thể là 5 phút
            print(f"   ⚠️  Warning: Interval is {avg_interval:.1f}s, expected ~15s")
            print(f"      (Báo cáo yêu cầu 15s, nhưng code sẽ xử lý được)")
    
    # Lưu (đảm bảo format ISO không có timezone)
    df["ts"] = df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df.to_csv(SENSOR_RAW_60D, index=False)
    print(f"   ✅ Saved to {SENSOR_RAW_60D} (timezone removed from CSV)")
    print(f"   ✅ Saved to {SENSOR_RAW_60D}")
    print(f"   Columns: {list(df.columns)}")


def create_labels_from_api_history() -> None:
    """
    Tạo labels_rain_60d.csv từ dữ liệu API lịch sử.
    
    Logic:
    - Nếu có owm_history_3years.csv → Dùng api_rain_1h để tạo labels
    - Nếu api_rain_1h > 0 trong 60 phút tới → rain_next_60 = 1
    - rain_amount_next_60_mm = tổng api_rain_1h trong 60 phút tới
    """
    print("\n" + "=" * 70)
    print("2️⃣  Creating labels_rain_60d.csv from API history")
    print("=" * 70)
    
    # Load sensor_raw_60d để lấy timestamps
    if not SENSOR_RAW_60D.exists():
        print(f"   ❌ sensor_raw_60d.csv not found. Run step 1 first.")
        return
    
    sensor_df = pd.read_csv(SENSOR_RAW_60D, parse_dates=["ts"])
    print(f"   ✓ Loaded {len(sensor_df)} sensor records")
    
    # Load API history
    api_df = None
    if OWM_HISTORY_3Y.exists():
        api_df = pd.read_csv(OWM_HISTORY_3Y, parse_dates=["ts"])
        print(f"   ✓ Loaded {len(api_df)} records from owm_history_3years.csv")
    elif OWM_HISTORY.exists():
        api_df = pd.read_csv(OWM_HISTORY, parse_dates=["ts"])
        print(f"   ✓ Loaded {len(api_df)} records from owm_history.csv")
    else:
        print(f"   ❌ No API history found. Cannot create labels.")
        print(f"      Need: owm_history_3years.csv or owm_history.csv")
        return
    
    if "api_rain_1h" not in api_df.columns:
        print(f"   ❌ api_rain_1h column not found in API data")
        return
    
    # Chuẩn hóa timezone: Convert tất cả về naive (UTC)
    # Đảm bảo sensor_df và api_df có cùng timezone để so sánh được
    
    # Convert sensor_df["ts"] về datetime64[ns] naive
    # Nếu string có timezone info (như "+00:00"), parse với utc=True rồi remove tz
    sensor_df["ts"] = pd.to_datetime(sensor_df["ts"], utc=True)
    if sensor_df["ts"].dt.tz is not None:
        sensor_df["ts"] = sensor_df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    # Convert api_df["ts"] về datetime64[ns] naive
    api_df["ts"] = pd.to_datetime(api_df["ts"], utc=True)
    if api_df["ts"].dt.tz is not None:
        api_df["ts"] = api_df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    print(f"   ✓ Normalized timezones (all naive UTC)")
    
    # Tạo labels: rain_next_60 = 1 nếu trong 60 phút tới có mưa
    # Logic: Với mỗi timestamp sensor, tìm API data trong 60 phút tới
    
    # Sort API data theo thời gian
    api_df = api_df.sort_values("ts").reset_index(drop=True)
    
    labels = []
    
    # Tối ưu: Dùng merge_asof để tìm API data gần nhất cho mỗi sensor timestamp
    for idx, row in sensor_df.iterrows():
        ts = row["ts"]
        device_id = row["device_id"]
        
        # Đảm bảo ts là pd.Timestamp naive (không có timezone)
        if isinstance(ts, pd.Timestamp):
            if ts.tz is not None:
                ts = ts.tz_convert("UTC").tz_localize(None)
        else:
            ts = pd.to_datetime(ts, utc=True)
            if ts.tz is not None:
                ts = ts.tz_localize(None)
        
        # Tìm API data trong 60 phút tới (từ ts đến ts+60min)
        ts_end = ts + timedelta(minutes=60)
        api_future = api_df[
            (api_df["ts"] > ts) & (api_df["ts"] <= ts_end)
        ]
        
        if len(api_future) > 0:
            # rain_next_60 = 1 nếu có bất kỳ mưa nào trong 60 phút
            rain_amount = float(api_future["api_rain_1h"].sum())
            rain_next_60 = 1 if rain_amount > 0.1 else 0  # Ngưỡng 0.1mm
            
            # rain_next_30 = 1 nếu có mưa trong 30 phút đầu
            ts_30min = ts + timedelta(minutes=30)
            api_30min = api_df[
                (api_df["ts"] > ts) & (api_df["ts"] <= ts_30min)
            ]
            rain_30min_amount = float(api_30min["api_rain_1h"].sum()) if len(api_30min) > 0 else 0.0
            rain_next_30 = 1 if rain_30min_amount > 0.1 else 0
        else:
            # Không có dữ liệu API trong 60 phút tới → Tìm API data gần nhất
            api_nearest = api_df[api_df["ts"] > ts]
            if len(api_nearest) > 0:
                nearest = api_nearest.iloc[0]
                rain_amount = float(nearest["api_rain_1h"]) if pd.notna(nearest["api_rain_1h"]) else 0.0
            else:
                rain_amount = 0.0
            
            rain_next_60 = 1 if rain_amount > 0.1 else 0
            rain_next_30 = 1 if rain_amount > 0.1 else 0
        
        labels.append({
            "ts": ts,
            "device_id": device_id,
            "rain_next_30": rain_next_30,
            "rain_next_60": rain_next_60,
            "rain_amount_next_60_mm": rain_amount,
        })
    
    labels_df = pd.DataFrame(labels)
    labels_df = labels_df.sort_values(["device_id", "ts"]).reset_index(drop=True)
    
    # Đảm bảo labels_df["ts"] cũng là naive (giống sensor_df)
    labels_df["ts"] = pd.to_datetime(labels_df["ts"], utc=True)
    if labels_df["ts"].dt.tz is not None:
        labels_df["ts"] = labels_df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    # Lưu (format ISO không có timezone để tránh lỗi khi đọc lại)
    labels_df["ts"] = labels_df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    labels_df.to_csv(LABELS_RAIN_60D, index=False)
    print(f"   ✅ Saved to {LABELS_RAIN_60D}")
    print(f"   Records: {len(labels_df)}")
    print(f"   Rain events (rain_next_60=1): {(labels_df['rain_next_60']==1).sum()} ({(labels_df['rain_next_60']==1).mean()*100:.1f}%)")


def create_irrigation_events_synthetic() -> None:
    """
    Tạo irrigation_events_60d.csv giả lập dựa trên sensor + labels.
    
    Logic:
    - Tưới khi: soil_moisture < 35% và không có mưa trong 60 phút tới
    - Thời gian tưới: 10-20 phút (tùy độ khô)
    - Thời điểm: 7:00 hoặc 17:00 (sáng/chiều)
    """
    print("\n" + "=" * 70)
    print("3️⃣  Creating irrigation_events_60d.csv (synthetic)")
    print("=" * 70)
    
    # Load sensor + labels
    if not SENSOR_RAW_60D.exists() or not LABELS_RAIN_60D.exists():
        print(f"   ❌ Need sensor_raw_60d.csv and labels_rain_60d.csv first")
        return
    
    sensor_df = pd.read_csv(SENSOR_RAW_60D, parse_dates=["ts"])
    labels_df = pd.read_csv(LABELS_RAIN_60D, parse_dates=["ts"])
    
    # Chuẩn hóa timezone trước khi merge
    sensor_df["ts"] = pd.to_datetime(sensor_df["ts"], utc=True)
    if sensor_df["ts"].dt.tz is not None:
        sensor_df["ts"] = sensor_df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    labels_df["ts"] = pd.to_datetime(labels_df["ts"], utc=True)
    if labels_df["ts"].dt.tz is not None:
        labels_df["ts"] = labels_df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
    
    # Merge
    df = sensor_df.merge(
        labels_df[["ts", "device_id", "rain_next_60"]],
        on=["ts", "device_id"],
        how="inner"
    )
    
    # Tạo irrigation events
    events = []
    last_irrigation_ts = None
    MIN_INTERVAL_HOURS = 6  # Tối thiểu 6 giờ giữa các lần tưới
    
    for idx, row in df.iterrows():
        ts = row["ts"]
        device_id = row["device_id"]
        soil_moist = row["soil_moist_pct"]
        rain_next_60 = row["rain_next_60"]
        hour = ts.hour
        
        # Điều kiện tưới:
        # 1. Đất khô (< 35%)
        # 2. Không có mưa trong 60 phút tới
        # 3. Thời điểm phù hợp (7:00 hoặc 17:00)
        # 4. Đã đủ thời gian từ lần tưới trước
        
        should_irrigate = (
            soil_moist < 35.0 and
            rain_next_60 == 0 and
            hour in [7, 17] and
            (last_irrigation_ts is None or (ts - last_irrigation_ts).total_seconds() >= MIN_INTERVAL_HOURS * 3600)
        )
        
        if should_irrigate:
            # Tính duration dựa trên độ khô
            if soil_moist < 25.0:
                duration_min = 3
            elif soil_moist < 30.0:
                duration_min = 2
            else:
                duration_min = 1
            
            start_ts = ts.replace(minute=0, second=0, microsecond=0)
            end_ts = start_ts + timedelta(minutes=duration_min)
            
            events.append({
                "start_ts": start_ts,
                "end_ts": end_ts,
                "device_id": device_id,
                "duration_min": duration_min,
            })
            
            last_irrigation_ts = ts
    
    if events:
        events_df = pd.DataFrame(events)
        events_df = events_df.sort_values("start_ts").reset_index(drop=True)
        
        # Lưu
        events_df.to_csv(IRRIGATION_EVENTS_60D, index=False)
        print(f"   ✅ Saved to {IRRIGATION_EVENTS_60D}")
        print(f"   Events: {len(events_df)}")
        print(f"   Time range: {events_df['start_ts'].min()} → {events_df['start_ts'].max()}")
    else:
        print(f"   ⚠️  No irrigation events generated (check conditions)")


def check_external_weather() -> None:
    """
    Kiểm tra external_weather_60d.csv có cần thiết không.
    
    Lưu ý: File này có vẻ là dữ liệu API cũ, không cần nữa vì đã có owm_history.
    """
    print("\n" + "=" * 70)
    print("4️⃣  Checking external_weather_60d.csv")
    print("=" * 70)
    
    ext_weather = DATA_DIR / "external_weather_60d.csv"
    
    if not ext_weather.exists():
        print(f"   ✓ File không tồn tại → Không cần")
        return
    
    df = pd.read_csv(ext_weather, parse_dates=["ts"])
    print(f"   File exists: {len(df)} records")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Time range: {df['ts'].min()} → {df['ts'].max()}")
    
    print(f"\n   💡 Đánh giá:")
    print(f"      - File này có vẻ là dữ liệu API cũ (format khác)")
    print(f"      - Hiện đã có owm_history_3years.csv và owm_history.csv")
    print(f"      - File này KHÔNG CẦN THIẾT nữa (có thể xóa hoặc giữ làm backup)")
    print(f"      - train_xgb_nowcast_v2.py sẽ ưu tiên owm_history.csv")


def main():
    """Main function."""
    print("=" * 70)
    print("🔧 CHUẨN HÓA DỮ LIỆU TRAINING THEO BÁO CÁO")
    print("=" * 70)
    
    # Step 1: Convert sensor_live → sensor_raw_60d
    convert_sensor_live_to_raw_60d()
    
    # Step 2: Tạo labels từ API history
    create_labels_from_api_history()
    
    # Step 3: Tạo irrigation events giả lập
    create_irrigation_events_synthetic()
    
    # Step 4: Kiểm tra external_weather
    check_external_weather()
    
    print("\n" + "=" * 70)
    print("✅ HOÀN THÀNH")
    print("=" * 70)
    print("\n📋 Files đã tạo/cập nhật:")
    print(f"   1. {SENSOR_RAW_60D.name} - Sensor data (15s, 4 fields)")
    print(f"   2. {LABELS_RAIN_60D.name} - Labels mưa từ API")
    print(f"   3. {IRRIGATION_EVENTS_60D.name} - Irrigation events (synthetic)")
    print(f"\n💡 Lưu ý:")
    print(f"   - external_weather_60d.csv không cần thiết nữa (có thể xóa)")
    print(f"   - Đảm bảo sensor_live.csv đã có pressure_hpa (không có light)")


if __name__ == "__main__":
    main()

