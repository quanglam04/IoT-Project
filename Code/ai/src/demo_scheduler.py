"""
Demo Scheduler - Điều chỉnh lịch tưới từ production cho demo.

Workflow:
1. Production: scheduler.py chạy → sinh lịch → lưu lich_tuoi.json → push MQTT
2. Demo: demo_scheduler.py đọc lich_tuoi.json → sửa ngày → sửa giờ slot đầu tiên → push MQTT → in output

Script này:
1. Đọc lich_tuoi.json (đã được scheduler.py tạo)
2. Nhận input ngày giờ từ user (ví dụ: 2025-12-09 09:34)
3. Sửa ngày trong schedule (timestamp, days_detail, slots)
4. Sửa giờ slot đầu tiên của ngày đầu tiên thành giờ demo
5. Push lên MQTT topic ai/schedule/irrigation
6. In output JSON ra terminal để check

Cách dùng:
    cd D:\IoT\Code\ai
    python src\demo_scheduler.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEDULE_INPUT = DATA_DIR / "lich_tuoi.json"  # File từ scheduler.py production
SCHEDULE_OUTPUT = DATA_DIR / "lich_tuoi_demo.json"  # File demo (optional)

MQTT_BROKER = os.getenv("MQTT_BROKER_URL", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

TOPIC_SCHEDULE = "ai/schedule/irrigation"


def get_demo_datetime() -> datetime:
    """Nhận input ngày giờ từ user."""
    print("=" * 70)
    print("🎯 DEMO SCHEDULER - TẠO LỊCH TƯỚI CHO DEMO")
    print("=" * 70)
    print("\nNhập ngày giờ demo (format: YYYY-MM-DD HH:MM)")
    print("Ví dụ: 2025-12-09 09:34")
    print("Hoặc chỉ ngày: 2025-12-09 (sẽ dùng 09:00)")
    
    while True:
        user_input = input("\n👉 Nhập ngày giờ: ").strip()
        
        if not user_input:
            print("⚠️  Vui lòng nhập ngày giờ!")
            continue
        
        # Thử parse với giờ phút
        try:
            demo_dt = datetime.strptime(user_input, "%Y-%m-%d %H:%M")
            print(f"✓ Nhận được: {demo_dt.strftime('%Y-%m-%d %H:%M')}")
            return demo_dt
        except ValueError:
            pass
        
        # Thử parse chỉ ngày
        try:
            demo_dt = datetime.strptime(user_input, "%Y-%m-%d")
            demo_dt = demo_dt.replace(hour=9, minute=0)  # Mặc định 9h sáng
            print(f"✓ Nhận được: {demo_dt.strftime('%Y-%m-%d %H:%M')} (mặc định 9h)")
            return demo_dt
        except ValueError:
            print(f"⚠️  Format không đúng! Vui lòng nhập YYYY-MM-DD HH:MM hoặc YYYY-MM-DD")
            continue


def load_schedule_from_file(file_path: Path) -> Dict:
    """Đọc lịch tưới từ file JSON."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file {file_path}.\n"
            f"Hãy chạy scheduler.py trước để tạo lich_tuoi.json"
        )
    
    with open(file_path, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    
    print(f"✓ Loaded schedule from {file_path.name}")
    print(f"   Original timestamp: {schedule.get('timestamp', 'N/A')}")
    print(f"   Total slots: {len(schedule.get('slots', []))}")
    print(f"   Total days: {len(schedule.get('days_detail', []))}")
    
    return schedule


def adjust_dates_in_schedule(schedule: Dict, demo_datetime: datetime) -> Dict:
    """
    Sửa ngày trong schedule để match với demo_datetime.
    
    Logic:
    - Tính offset giữa ngày đầu tiên trong schedule và demo_datetime
    - Áp dụng offset cho tất cả dates trong schedule
    """
    print("\n" + "-" * 70)
    print("📅 Adjusting dates in schedule...")
    print("-" * 70)
    
    # Lấy ngày đầu tiên từ schedule
    first_day_detail = schedule.get("days_detail", [{}])[0]
    original_first_date_str = first_day_detail.get("date")
    
    if not original_first_date_str:
        print("⚠️  Không tìm thấy ngày đầu tiên trong schedule. Giữ nguyên.")
        return schedule
    
    original_first_date = datetime.fromisoformat(original_first_date_str).date()
    demo_date = demo_datetime.date()
    
    # Tính offset (số ngày)
    offset_days = (demo_date - original_first_date).days
    
    if offset_days == 0:
        print("✓ Ngày đã đúng, không cần điều chỉnh.")
    else:
        print(f"✓ Offset: {offset_days} ngày")
        print(f"   Từ: {original_first_date} → {demo_date}")
    
    # Cập nhật timestamp
    schedule["timestamp"] = demo_datetime.isoformat() + "Z"
    
    # Cập nhật days_detail
    for day_detail in schedule.get("days_detail", []):
        old_date_str = day_detail.get("date")
        if old_date_str:
            old_date = datetime.fromisoformat(old_date_str).date()
            new_date = old_date + timedelta(days=offset_days)
            day_detail["date"] = new_date.isoformat()
    
    # Cập nhật slots
    for slot in schedule.get("slots", []):
        # Cập nhật date
        old_date_str = slot.get("date")
        if old_date_str:
            old_date = datetime.fromisoformat(old_date_str).date()
            new_date = old_date + timedelta(days=offset_days)
            slot["date"] = new_date.isoformat()
        
        # Cập nhật start_ts và end_ts
        if slot.get("start_ts"):
            old_start = datetime.fromisoformat(slot["start_ts"].replace("Z", ""))
            new_start = old_start + timedelta(days=offset_days)
            slot["start_ts"] = new_start.isoformat() + "Z"
        
        if slot.get("end_ts"):
            old_end = datetime.fromisoformat(slot["end_ts"].replace("Z", ""))
            new_end = old_end + timedelta(days=offset_days)
            slot["end_ts"] = new_end.isoformat() + "Z"
    
    print(f"✓ Updated {len(schedule.get('days_detail', []))} days and {len(schedule.get('slots', []))} slots")
    
    return schedule


def adjust_slots_for_demo(schedule: Dict, demo_datetime: datetime) -> Dict:
    """
    Điều chỉnh thời gian tưới trong slots để phù hợp với khung demo.
    
    Logic:
    - Slot đầu tiên của ngày đầu tiên → đổi thành demo_datetime (nếu trong khung 8h-17h)
    - Tự động tính forecast_trigger_ts = start_ts - 10 phút cho TẤT CẢ slots
    - Các slot khác giữ nguyên hoặc điều chỉnh tương ứng
    """
    print("\n" + "-" * 70)
    print("🔧 Adjusting irrigation slots for demo...")
    print("-" * 70)
    
    slots = schedule.get("slots", [])
    if not slots:
        print("⚠️  Không có slot nào để điều chỉnh.")
        return schedule
    
    # Tìm slot đầu tiên của ngày đầu tiên
    first_day = demo_datetime.date()
    first_day_slots = [s for s in slots if s.get("date") == first_day.isoformat()]
    
    if not first_day_slots:
        print("⚠️  Không tìm thấy slot nào cho ngày đầu tiên.")
        # Vẫn tính forecast_trigger_ts cho tất cả slots
    else:
        # Sắp xếp theo start_ts
        first_day_slots.sort(key=lambda x: x.get("start_ts", ""))
        first_slot = first_day_slots[0]
        
        # Parse start_ts của slot đầu tiên
        original_start = datetime.fromisoformat(first_slot["start_ts"].replace("Z", ""))
        duration_min = first_slot.get("duration_min", 15)
        
        # Kiểm tra xem demo_datetime có trong khung 8h-17h không
        demo_hour = demo_datetime.hour
        if 8 <= demo_hour <= 17:
            # Điều chỉnh slot đầu tiên thành demo_datetime
            new_start = demo_datetime.replace(second=0, microsecond=0)
            new_end = new_start + timedelta(minutes=duration_min)
            
            print(f"✓ Slot đầu tiên:")
            print(f"   Từ: {original_start.strftime('%Y-%m-%d %H:%M')} → {new_start.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Đến: {(original_start + timedelta(minutes=duration_min)).strftime('%H:%M')} → {new_end.strftime('%H:%M')}")
            
            # Cập nhật slot đầu tiên
            first_slot["start_ts"] = new_start.isoformat() + "Z"
            first_slot["end_ts"] = new_end.isoformat() + "Z"
            
            # Cập nhật lại trong schedule
            for i, slot in enumerate(slots):
                if slot.get("date") == first_day.isoformat() and slot.get("start_ts") == original_start.isoformat() + "Z":
                    slots[i] = first_slot
                    break
            
            schedule["slots"] = slots
            
            # Cập nhật days_detail
            for day_detail in schedule.get("days_detail", []):
                if day_detail.get("date") == first_day.isoformat():
                    # Tính lại total_irrigation_min
                    day_slots = [s for s in slots if s.get("date") == first_day.isoformat()]
                    total_min = sum(s.get("duration_min", 0) for s in day_slots)
                    day_detail["total_irrigation_min"] = round(total_min, 1)
                    break
        else:
            print(f"⚠️  Demo datetime ({demo_hour}h) không trong khung 8h-17h. Giữ nguyên lịch.")
    
    # Tự động tính forecast_trigger_ts cho TẤT CẢ slots
    # Production: start_ts - 10 phút
    # Demo: start_ts - 1 phút (cho demo nhanh)
    is_demo = os.getenv("DEMO_MODE", "").lower() == "true"
    trigger_minutes = 1 if is_demo else 10
    
    print(f"\n✓ Tính toán forecast_trigger_ts cho tất cả slots (start_ts - {trigger_minutes} phút)...")
    for slot in slots:
        start_ts_str = slot.get("start_ts", "")
        if start_ts_str:
            start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
            trigger_ts = start_ts - timedelta(minutes=trigger_minutes)
            slot["forecast_trigger_ts"] = trigger_ts.isoformat() + "Z"
    
    schedule["slots"] = slots
    print(f"   ✓ Đã cập nhật {len(slots)} slot(s) với forecast_trigger_ts")
    
    return schedule


def save_schedule_json(schedule: Dict, output_file: Path):
    """Lưu schedule vào file JSON."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Saved schedule to {output_file}")


def publish_to_mqtt(schedule: Dict) -> bool:
    """Push schedule lên MQTT."""
    print("\n" + "-" * 70)
    print("📡 Publishing to MQTT...")
    print("-" * 70)
    
    try:
        client = mqtt.Client(client_id="demo_scheduler_" + str(int(datetime.utcnow().timestamp())))
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        
        payload = json.dumps(schedule, ensure_ascii=False)
        result = client.publish(TOPIC_SCHEDULE, payload, qos=1)
        
        # Chờ publish
        result.wait_for_publish(timeout=5)
        
        client.loop_stop()
        client.disconnect()
        
        print(f"✓ Published to {TOPIC_SCHEDULE}")
        print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Payload size: {len(payload)} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Failed to publish to MQTT: {e}")
        return False


def print_schedule_output(schedule: Dict):
    """In output JSON ra terminal để check."""
    print("\n" + "=" * 70)
    print("📋 OUTPUT JSON (Schedule) - DEMO VERSION")
    print("=" * 70)
    print(json.dumps(schedule, ensure_ascii=False, indent=2))
    print("=" * 70)


def main():
    # 1. Đọc lịch từ file production
    print("\n" + "-" * 70)
    print("📂 Loading schedule from production file...")
    print("-" * 70)
    schedule = load_schedule_from_file(SCHEDULE_INPUT)
    
    # 2. Nhận input ngày giờ từ user
    demo_datetime = get_demo_datetime()
    
    # 3. Sửa ngày trong schedule
    schedule = adjust_dates_in_schedule(schedule, demo_datetime)
    
    # 4. Sửa giờ slot đầu tiên
    schedule = adjust_slots_for_demo(schedule, demo_datetime)
    
    # 5. Lưu vào file JSON (optional)
    save_schedule_json(schedule, SCHEDULE_OUTPUT)
    
    # 6. Push lên MQTT
    publish_success = publish_to_mqtt(schedule)
    
    # 7. In output ra terminal để check
    print_schedule_output(schedule)
    
    # 8. Summary
    print("\n" + "=" * 70)
    print("✅ DEMO SCHEDULER COMPLETED")
    print("=" * 70)
    print(f"Demo datetime: {demo_datetime.strftime('%Y-%m-%d %H:%M')}")
    print(f"Input file: {SCHEDULE_INPUT.name}")
    print(f"Output file: {SCHEDULE_OUTPUT.name}")
    print(f"MQTT publish: {'✓ Success' if publish_success else '✗ Failed'}")
    print(f"Total slots: {len(schedule.get('slots', []))}")
    print(f"Days: {len(schedule.get('days_detail', []))}")
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

