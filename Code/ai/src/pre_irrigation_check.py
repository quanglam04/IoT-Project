"""
Pre-Irrigation Check - Kiểm tra dự báo mưa trước khi tưới.

Workflow:
1. Đọc lịch tưới từ lich_tuoi.json hoặc lich_tuoi_demo.json
2. Tìm các slot sắp tới (trong vòng 15 phút)
3. Với mỗi slot có forecast_trigger_ts sắp đến → chạy inference
4. Dựa vào kết quả dự báo → quyết định có tưới hay hoãn
5. Cập nhật slot (thêm field "forecast_result" và "status")
6. Publish kết quả lên MQTT (nếu cần)

Chạy:
    python src/pre_irrigation_check.py [--schedule-file lich_tuoi_demo.json]
"""

import json
import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Import inference logic
from inference_decision import (
    load_api_row,
    load_models,
    decide_irrigation,
)
from feature_engineering import compute_feature_from_window, FEATURE_NAMES
import numpy as np
import pandas as pd

load_dotenv()

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"

# Sensor files
SENSOR_REAL = DATA_DIR / "sensor_raw_60d.csv"
SENSOR_SYNTH = DATA_DIR / "sensor_raw_60d_synth.csv"

# API files (for load_api_row)
OWM_CSV = DATA_DIR / "owm_history.csv"
EXT_WEATHER_CSV = DATA_DIR / "external_weather_60d.csv"

# MQTT config
MQTT_BROKER = os.getenv("MQTT_BROKER_URL", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

TOPIC_FORECAST = "ai/forecast/rain"
TOPIC_SCHEDULE_UPDATE = "ai/schedule/irrigation/update"


def load_schedule(file_path: Path) -> Dict:
    """Load lịch tưới từ file JSON."""
    if not file_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    
    return schedule


def find_upcoming_slots(schedule: Dict, lookahead_minutes: int = 15, find_next: bool = True) -> List[Dict]:
    """
    Tìm các slot để check dự báo.
    
    Logic:
    1. Tìm slots có forecast_trigger_ts trong vòng lookahead_minutes (đã qua hoặc sắp đến)
    2. Nếu không có, tìm slot TIẾP THEO (next upcoming) bất kể khoảng cách
    3. Nếu find_next=False, chỉ tìm trong vòng lookahead_minutes
    
    Args:
        schedule: Lịch tưới
        lookahead_minutes: Số phút lookahead (default: 15)
        find_next: Nếu True, tìm slot tiếp theo nếu không có trong lookahead
    
    Returns:
        List of slots cần check
    """
    now = datetime.utcnow()
    slots = schedule.get("slots", [])
    upcoming = []
    all_slots_with_trigger = []
    
    # Tính forecast_trigger_ts cho tất cả slots (nếu chưa có)
    for slot in slots:
        trigger_ts_str = slot.get("forecast_trigger_ts")
        if not trigger_ts_str:
            start_ts_str = slot.get("start_ts", "")
            if start_ts_str:
                start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
                trigger_ts = start_ts - timedelta(minutes=10)
                trigger_ts_str = trigger_ts.isoformat() + "Z"
                slot["forecast_trigger_ts"] = trigger_ts_str
        
        if trigger_ts_str:
            trigger_ts = datetime.fromisoformat(trigger_ts_str.replace("Z", ""))
            time_diff = (trigger_ts - now).total_seconds() / 60  # phút
            slot["_time_to_trigger"] = time_diff
            slot["_trigger_ts"] = trigger_ts
            all_slots_with_trigger.append(slot)
    
    # 1. Tìm slots trong vòng lookahead_minutes (đã qua 5 phút hoặc sắp đến)
    for slot in all_slots_with_trigger:
        time_diff = slot.get("_time_to_trigger", 999)
        # Cho phép đã qua 5 phút hoặc sắp đến trong lookahead_minutes
        if -5 <= time_diff <= lookahead_minutes:
            upcoming.append(slot)
    
    # 2. Nếu không có slot nào trong lookahead và find_next=True → tìm slot TIẾP THEO
    if not upcoming and find_next:
        # Tìm slot có trigger_ts > now (sắp đến) và gần nhất
        future_slots = [s for s in all_slots_with_trigger if s.get("_time_to_trigger", 999) > -5]
        if future_slots:
            # Sắp xếp theo thời gian trigger (gần nhất trước)
            future_slots.sort(key=lambda x: x.get("_time_to_trigger", 999))
            # Lấy slot tiếp theo (gần nhất)
            next_slot = future_slots[0]
            upcoming.append(next_slot)
            print(f"   ℹ️  Không có slot trong vòng {lookahead_minutes} phút.")
            print(f"   → Tìm slot tiếp theo: {next_slot.get('_trigger_ts').strftime('%Y-%m-%d %H:%M')} "
                  f"({next_slot.get('_time_to_trigger', 0):.1f} phút)")
    
    # Sắp xếp theo thời gian trigger
    upcoming.sort(key=lambda x: x.get("_time_to_trigger", 999))
    return upcoming


def _choose_sensor_path() -> Path:
    """Chọn file sensor (ưu tiên real, fallback synth)."""
    if SENSOR_REAL.exists():
        return SENSOR_REAL
    if SENSOR_SYNTH.exists():
        return SENSOR_SYNTH
    raise FileNotFoundError("No sensor file found (sensor_raw_60d*.csv)")


def load_sensor_buffer_at_timestamp(target_ts: datetime) -> pd.DataFrame:
    """
    Load 12 bản ghi sensor tại thời điểm target_ts (hoặc gần nhất trước đó).
    
    Logic:
    - Tìm các bản ghi sensor có ts <= target_ts
    - Lấy 12 bản ghi gần nhất (60 phút với dữ liệu 5 phút)
    - Nếu không đủ 12 bản ghi, lấy tất cả có thể
    
    Args:
        target_ts: Thời điểm cần lấy dữ liệu (ví dụ: forecast_trigger_ts)
    
    Returns:
        DataFrame với 12 bản ghi sensor gần nhất trước target_ts
    """
    path = _choose_sensor_path()
    df = pd.read_csv(path, parse_dates=["ts"]).sort_values("ts")
    
    # Lọc các bản ghi có ts <= target_ts
    df_before = df[df["ts"] <= target_ts].copy()
    
    if len(df_before) == 0:
        # Nếu không có dữ liệu trước target_ts, dùng dữ liệu gần nhất
        print(f"   ⚠️  Không có sensor data trước {target_ts}. Dùng dữ liệu gần nhất.")
        df_before = df.tail(12).copy()
    else:
        # Lấy 12 bản ghi gần nhất trước target_ts
        df_before = df_before.tail(12).copy()
    
    # Đảm bảo có đủ columns
    df_before = df_before.rename(
        columns={
            "ts": "ts",
            "temp_c": "temp_c",
            "rh_pct": "rh_pct",
            "pressure_hpa": "pressure_hpa",
            "soil_moist_pct": "soil_moist_pct",
        }
    )
    
    if len(df_before) < 2:
        raise ValueError(f"Not enough sensor data before {target_ts} (need >=2 rows, got {len(df_before)})")
    
    return df_before


def load_sensor_buffer() -> pd.DataFrame:
    """Load 12 bản ghi sensor gần nhất (60 phút) - dùng cho backward compatibility."""
    return load_sensor_buffer_at_timestamp(datetime.utcnow())


def run_forecast_for_slot(slot: Dict) -> Dict:
    """
    Chạy dự báo mưa cho một slot.
    
    Logic:
    - Lấy sensor data TẠI THỜI ĐIỂM forecast_trigger_ts (hoặc trước đó)
    - Lấy API data gần nhất với forecast_trigger_ts
    - Tính features và chạy model
    
    Returns:
        Dict với forecast result và recommendation
    """
    try:
        # Lấy forecast_trigger_ts từ slot (hoặc tính từ start_ts - 10 phút)
        trigger_ts_str = slot.get("forecast_trigger_ts")
        if not trigger_ts_str:
            start_ts_str = slot.get("start_ts", "")
            if start_ts_str:
                start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
                trigger_ts = start_ts - timedelta(minutes=10)
            else:
                # Fallback: dùng thời điểm hiện tại
                trigger_ts = datetime.utcnow()
        else:
            trigger_ts = datetime.fromisoformat(trigger_ts_str.replace("Z", ""))
        
        print(f"   📅 Using sensor data at/before: {trigger_ts.strftime('%Y-%m-%d %H:%M')}")
        
        # Load sensor buffer TẠI THỜI ĐIỂM trigger_ts (hoặc trước đó)
        sensor_df = load_sensor_buffer_at_timestamp(trigger_ts)
        latest_ts = sensor_df.iloc[-1]["ts"]
        
        print(f"   📊 Sensor data range: {sensor_df.iloc[0]['ts']} → {latest_ts}")
        
        # Load API data gần nhất với trigger_ts
        api_row = load_api_row(pd.Timestamp(trigger_ts))
        
        # Tính features
        feature_vector = compute_feature_from_window(
            sensor_df=sensor_df,
            api_row=api_row,
            interval_seconds=300,  # 5 phút
        )
        x = np.array(feature_vector.to_list(), dtype="float32").reshape(1, -1)
        
        # Load models
        nowcast_model, amount_model, meta = load_models()
        threshold = float(meta.get("threshold_default", 0.5)) if meta else 0.5
        
        # Inference
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
        
        # Decision
        soil_m = float(sensor_df.iloc[-1]["soil_moist_pct"])
        should_irrigate, reason = decide_irrigation(soil_m, prob)
        
        return {
            "timestamp": latest_ts.isoformat() if hasattr(latest_ts, "isoformat") else str(latest_ts),
            "predictions": {
                "rain_60min": {
                    "probability": round(prob, 4),
                    "label": label,
                },
                "rain_amount_60min_mm": round(amount_mm, 2) if amount_mm is not None else None,
            },
            "sensor_ref": {
                "soil_moist_pct": round(soil_m, 2),
                "temp_c": round(float(sensor_df.iloc[-1]["temp_c"]), 2),
                "rh_pct": round(float(sensor_df.iloc[-1]["rh_pct"]), 2),
                "pressure_hpa": round(float(sensor_df.iloc[-1]["pressure_hpa"]), 2),
            },
            "recommendation": {
                "should_irrigate": should_irrigate,
                "reason": reason,
                "threshold_used": threshold,
            },
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "recommendation": {
                "should_irrigate": True,  # Default: tưới nếu lỗi
                "reason": f"Lỗi dự báo: {e}. Tưới theo lịch mặc định.",
            },
        }


def update_slot_with_forecast(slot: Dict, forecast_result: Dict) -> Dict:
    """
    Cập nhật slot với kết quả dự báo.
    
    Thêm fields:
    - forecast_result: kết quả dự báo
    - status: "confirmed" (tưới), "postponed" (hoãn), "pending" (chưa check)
    - forecast_checked_at: thời gian check
    """
    slot = slot.copy()
    slot["forecast_result"] = forecast_result
    slot["forecast_checked_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Quyết định status
    recommendation = forecast_result.get("recommendation", {})
    should_irrigate = recommendation.get("should_irrigate", True)
    
    if should_irrigate:
        slot["status"] = "confirmed"  # Xác nhận tưới
    else:
        slot["status"] = "postponed"  # Hoãn tưới
    
    return slot


def publish_forecast_to_mqtt(forecast_result: Dict, slot_id: str = None) -> bool:
    """Publish kết quả dự báo lên MQTT."""
    try:
        client = mqtt.Client(client_id="pre_irrigation_check_" + str(int(datetime.utcnow().timestamp())))
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        
        payload = json.dumps(forecast_result, ensure_ascii=False)
        result = client.publish(TOPIC_FORECAST, payload, qos=1)
        
        result.wait_for_publish(timeout=5)
        client.loop_stop()
        client.disconnect()
        
        print(f"   ✓ Published forecast to {TOPIC_FORECAST}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to publish: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Pre-irrigation forecast check")
    parser.add_argument(
        "--schedule-file",
        type=str,
        default="lich_tuoi_demo.json",
        help="File lịch tưới (default: lich_tuoi_demo.json)",
    )
    parser.add_argument(
        "--lookahead",
        type=int,
        default=15,
        help="Số phút lookahead để tìm slots (default: 15)",
    )
    parser.add_argument(
        "--find-next",
        action="store_true",
        default=True,
        help="Nếu không có slot trong lookahead, tìm slot tiếp theo (default: True)",
    )
    parser.add_argument(
        "--no-find-next",
        dest="find_next",
        action="store_false",
        help="Chỉ tìm slots trong vòng lookahead, không tìm slot tiếp theo",
    )
    parser.add_argument(
        "--publish-mqtt",
        action="store_true",
        help="Publish kết quả lên MQTT",
    )
    
    args = parser.parse_args()
    
    schedule_file = DATA_DIR / args.schedule_file
    
    print("=" * 70)
    print("🌧️  PRE-IRRIGATION FORECAST CHECK")
    print("=" * 70)
    print(f"Schedule file: {schedule_file.name}")
    print(f"Lookahead: {args.lookahead} minutes")
    print(f"Find next slot: {args.find_next}")
    print()
    
    # Load schedule
    schedule = load_schedule(schedule_file)
    
    # Tìm slots sắp tới
    upcoming_slots = find_upcoming_slots(
        schedule, 
        lookahead_minutes=args.lookahead,
        find_next=args.find_next
    )
    
    if not upcoming_slots:
        print("✓ Không có slot nào sắp tới trong vòng {} phút.".format(args.lookahead))
        return
    
    print(f"📋 Tìm thấy {len(upcoming_slots)} slot(s) sắp tới:")
    for i, slot in enumerate(upcoming_slots, 1):
        start_ts = datetime.fromisoformat(slot.get("start_ts", "").replace("Z", ""))
        trigger_ts = datetime.fromisoformat(slot.get("forecast_trigger_ts", "").replace("Z", ""))
        time_to_trigger = slot.get("_time_to_trigger", 0)
        
        print(f"\n{i}. Slot {i}:")
        print(f"   Start: {start_ts.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Trigger forecast: {trigger_ts.strftime('%Y-%m-%d %H:%M')} ({time_to_trigger:.1f} phút)")
    
    # Chạy dự báo cho từng slot
    print("\n" + "-" * 70)
    print("🔮 Running forecasts...")
    print("-" * 70)
    
    updated_slots = []
    for i, slot in enumerate(upcoming_slots, 1):
        print(f"\n[{i}/{len(upcoming_slots)}] Checking slot...")
        
        # Chạy dự báo
        forecast_result = run_forecast_for_slot(slot)
        
        # Cập nhật slot
        updated_slot = update_slot_with_forecast(slot, forecast_result)
        updated_slots.append(updated_slot)
        
        # In kết quả
        print(f"   Rain probability: {forecast_result.get('predictions', {}).get('rain_60min', {}).get('probability', 0):.2%}")
        print(f"   Rain amount: {forecast_result.get('predictions', {}).get('rain_amount_60min_mm', 0):.2f} mm")
        print(f"   Recommendation: {forecast_result.get('recommendation', {}).get('reason', 'N/A')}")
        print(f"   Status: {updated_slot.get('status', 'N/A')}")
        
        # Publish MQTT (nếu cần)
        if args.publish_mqtt:
            publish_forecast_to_mqtt(forecast_result, slot_id=f"slot_{i}")
    
    # Cập nhật schedule với slots đã check
    for updated_slot in updated_slots:
        # Tìm và cập nhật slot trong schedule
        for j, original_slot in enumerate(schedule.get("slots", [])):
            if original_slot.get("start_ts") == updated_slot.get("start_ts"):
                schedule["slots"][j] = updated_slot
                break
    
    # Lưu schedule đã cập nhật
    output_file = DATA_DIR / f"{schedule_file.stem}_checked.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("✅ PRE-IRRIGATION CHECK COMPLETED")
    print("=" * 70)
    print(f"Updated schedule saved to: {output_file.name}")
    print(f"Total slots checked: {len(updated_slots)}")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

