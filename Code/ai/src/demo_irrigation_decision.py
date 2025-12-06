"""
Demo Irrigation Decision - Cho phép chọn quyết định tưới cho demo.

Workflow:
1. Load lịch tưới từ lich_tuoi_demo.json (hoặc lich_tuoi.json)
2. Hiển thị các slots sắp tới
3. Cho phép user chọn quyết định cho từng slot:
   - CONFIRM: Xác nhận tưới (chạy inference thật hoặc skip)
   - POSTPONE: Hoãn tưới (có thể nhập lý do)
   - AUTO: Tự động chạy inference và quyết định
4. Cập nhật schedule với quyết định đã chọn
5. Push lên MQTT

Cách dùng:
    cd D:\IoT\Code\ai
    python src\demo_irrigation_decision.py [--schedule-file lich_tuoi_demo.json] [--auto]
"""

import json
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Import inference logic (optional - có thể skip nếu --skip-inference)
INFERENCE_AVAILABLE = False
try:
    from pre_irrigation_check import (
        load_schedule as load_schedule_from_file,
        find_upcoming_slots,
        run_forecast_for_slot,
    )
    INFERENCE_AVAILABLE = True
    
    # Define update_slot_with_forecast locally if not imported
    def update_slot_with_forecast(slot: Dict, forecast_result: Dict) -> Dict:
        """Cập nhật slot với forecast result."""
        slot = slot.copy()
        slot["forecast_result"] = forecast_result
        recommendation = forecast_result.get("recommendation", {})
        slot["pre_irrigation_recommendation"] = recommendation
        if recommendation.get("should_irrigate", False):
            slot["status"] = "confirmed"
        else:
            slot["status"] = "postponed"
        return slot
except ImportError:
    def load_schedule_from_file(file_path: Path) -> Dict:
        """Load schedule từ file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"

# MQTT config
MQTT_BROKER = os.getenv("MQTT_BROKER_URL", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

TOPIC_SCHEDULE_UPDATE = "ai/schedule/irrigation/update"
TOPIC_DECISION = "ai/irrigation/decision"


def get_demo_current_time() -> datetime:
    """Nhận thời gian hiện tại cho demo (có thể là tương lai để test)."""
    print("\n" + "-" * 70)
    print("⏰ DEMO CURRENT TIME")
    print("-" * 70)
    print("Nhập thời gian hiện tại cho demo (format: YYYY-MM-DD HH:MM:SS)")
    print("Ví dụ: 2025-12-09 09:34:00")
    print("Hoặc nhấn Enter để dùng thời gian thực")
    
    user_input = input("\n👉 Nhập thời gian (hoặc Enter): ").strip()
    
    if not user_input:
        return datetime.utcnow()
    
    try:
        demo_time = datetime.strptime(user_input, "%Y-%m-%d %H:%M:%S")
        print(f"✓ Demo time: {demo_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return demo_time
    except ValueError:
        print("⚠️  Format không đúng. Dùng thời gian thực.")
        return datetime.utcnow()


def display_slots(slots: List[Dict], current_time: datetime):
    """Hiển thị danh sách slots."""
    print("\n" + "=" * 70)
    print("📋 IRRIGATION SLOTS")
    print("=" * 70)
    
    if not slots:
        print("⚠️  Không có slot nào sắp tới.")
        return
    
    for i, slot in enumerate(slots, 1):
        start_ts_str = slot.get("start_ts", "")
        trigger_ts_str = slot.get("forecast_trigger_ts", "")
        date_str = slot.get("date", "")
        duration = slot.get("duration_min", 0)
        status = slot.get("status", "pending")
        
        if start_ts_str:
            start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
            time_to_start = (start_ts - current_time).total_seconds() / 60  # phút
            
            print(f"\n[{i}] Slot {i}:")
            print(f"    📅 Date: {date_str}")
            print(f"    ⏰ Start: {start_ts.strftime('%Y-%m-%d %H:%M')} ({time_to_start:.1f} phút)")
            print(f"    ⏱️  Duration: {duration} phút")
            
            if trigger_ts_str:
                trigger_ts = datetime.fromisoformat(trigger_ts_str.replace("Z", ""))
                time_to_trigger = (trigger_ts - current_time).total_seconds() / 60
                print(f"    🔮 Forecast trigger: {trigger_ts.strftime('%Y-%m-%d %H:%M')} ({time_to_trigger:.1f} phút)")
            
            print(f"    📊 Status: {status}")
            
            # Hiển thị forecast result nếu có
            forecast_result = slot.get("forecast_result", {})
            if forecast_result:
                rain_prob = forecast_result.get("rain_60min", {}).get("probability", 0)
                rain_amount = forecast_result.get("rain_amount_60min_mm", 0)
                print(f"    🌧️  Forecast: {rain_prob:.1%} prob, {rain_amount:.2f}mm")
            
            recommendation = slot.get("pre_irrigation_recommendation", {})
            if recommendation:
                should_irrigate = recommendation.get("should_irrigate", False)
                reason = recommendation.get("reason", "")
                print(f"    💡 Recommendation: {'✅ TƯỚI' if should_irrigate else '⏸️  HOÃN'} - {reason}")


def get_decision_for_slot(slot: Dict, slot_idx: int, auto_mode: bool = False) -> Dict:
    """
    Nhận quyết định từ user cho một slot.
    
    Returns:
        Dict với decision và reason
    """
    start_ts_str = slot.get("start_ts", "")
    if not start_ts_str:
        return {"decision": "skip", "reason": "No start_ts"}
    
    start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
    
    print(f"\n" + "-" * 70)
    print(f"🎯 DECISION FOR SLOT {slot_idx}")
    print("-" * 70)
    print(f"Start time: {start_ts.strftime('%Y-%m-%d %H:%M')}")
    print(f"Duration: {slot.get('duration_min', 0)} phút")
    
    # Nếu có forecast result, hiển thị
    forecast_result = slot.get("forecast_result", {})
    if forecast_result:
        rain_prob = forecast_result.get("rain_60min", {}).get("probability", 0)
        rain_amount = forecast_result.get("rain_amount_60min_mm", 0)
        print(f"Forecast: {rain_prob:.1%} prob, {rain_amount:.2f}mm")
    
    # Auto mode: dùng recommendation từ forecast
    if auto_mode and forecast_result:
        recommendation = slot.get("pre_irrigation_recommendation", {})
        should_irrigate = recommendation.get("should_irrigate", False)
        reason = recommendation.get("reason", "Auto decision based on forecast")
        
        decision = "confirm" if should_irrigate else "postpone"
        print(f"\n🤖 AUTO MODE: {decision.upper()} - {reason}")
        return {
            "decision": decision,
            "reason": reason,
            "auto": True,
        }
    
    # Manual mode: hỏi user
    print("\nChọn quyết định:")
    print("  1. CONFIRM - Xác nhận tưới")
    print("  2. POSTPONE - Hoãn tưới")
    print("  3. SKIP - Bỏ qua slot này")
    
    if INFERENCE_AVAILABLE:
        print("  4. RUN INFERENCE - Chạy dự báo mưa và quyết định tự động")
    
    while True:
        choice = input("\n👉 Chọn (1-4): ").strip()
        
        if choice == "1":
            reason = input("   Lý do (hoặc Enter để dùng mặc định): ").strip()
            if not reason:
                reason = "User confirmed irrigation"
            return {
                "decision": "confirm",
                "reason": reason,
                "auto": False,
            }
        
        elif choice == "2":
            reason = input("   Lý do hoãn (hoặc Enter để dùng mặc định): ").strip()
            if not reason:
                reason = "User postponed irrigation"
            return {
                "decision": "postpone",
                "reason": reason,
                "auto": False,
            }
        
        elif choice == "3":
            return {
                "decision": "skip",
                "reason": "User skipped this slot",
                "auto": False,
            }
        
        elif choice == "4" and INFERENCE_AVAILABLE:
            print("\n   🔮 Running inference...")
            try:
                forecast_result = run_forecast_for_slot(slot)
                updated_slot = update_slot_with_forecast(slot, forecast_result)
                
                recommendation = updated_slot.get("pre_irrigation_recommendation", {})
                should_irrigate = recommendation.get("should_irrigate", False)
                reason = recommendation.get("reason", "Based on forecast")
                
                decision = "confirm" if should_irrigate else "postpone"
                print(f"   ✓ Inference result: {decision.upper()} - {reason}")
                
                return {
                    "decision": decision,
                    "reason": reason,
                    "auto": True,
                    "forecast_result": forecast_result,
                }
            except Exception as e:
                print(f"   ❌ Inference failed: {e}")
                print("   → Fallback to manual decision")
                continue
        
        else:
            print("⚠️  Lựa chọn không hợp lệ. Vui lòng chọn 1-4.")


def update_slot_with_decision(slot: Dict, decision: Dict) -> Dict:
    """Cập nhật slot với quyết định đã chọn."""
    slot = slot.copy()
    
    slot["decision"] = decision["decision"]
    slot["decision_reason"] = decision["reason"]
    slot["decision_auto"] = decision.get("auto", False)
    slot["decision_timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # Cập nhật status
    if decision["decision"] == "confirm":
        slot["status"] = "confirmed"
    elif decision["decision"] == "postpone":
        slot["status"] = "postponed"
    elif decision["decision"] == "skip":
        slot["status"] = "skipped"
    
    # Nếu có forecast_result từ inference, cập nhật
    if "forecast_result" in decision:
        slot["forecast_result"] = decision["forecast_result"]
        slot = update_slot_with_forecast(slot, decision["forecast_result"])
    
    return slot


def publish_decision_to_mqtt(slot: Dict, decision: Dict) -> bool:
    """Push quyết định lên MQTT."""
    try:
        client = mqtt.Client(client_id="demo_decision_" + str(int(datetime.utcnow().timestamp())))
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        
        # Payload cho quyết định
        decision_payload = {
            "slot_id": slot.get("start_ts", ""),
            "decision": decision["decision"],
            "reason": decision["reason"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "slot": slot,
        }
        
        payload_str = json.dumps(decision_payload, ensure_ascii=False)
        result = client.publish(TOPIC_DECISION, payload_str, qos=1)
        result.wait_for_publish(timeout=5)
        
        client.loop_stop()
        client.disconnect()
        
        print(f"   ✓ Published to {TOPIC_DECISION}")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to publish: {e}")
        return False


def publish_schedule_update_to_mqtt(schedule: Dict) -> bool:
    """Push schedule đã cập nhật lên MQTT."""
    try:
        client = mqtt.Client(client_id="demo_schedule_update_" + str(int(datetime.utcnow().timestamp())))
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        
        payload_str = json.dumps(schedule, ensure_ascii=False)
        result = client.publish(TOPIC_SCHEDULE_UPDATE, payload_str, qos=1)
        result.wait_for_publish(timeout=5)
        
        client.loop_stop()
        client.disconnect()
        
        print(f"✓ Published schedule update to {TOPIC_SCHEDULE_UPDATE}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to publish schedule: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Demo Irrigation Decision")
    parser.add_argument(
        "--schedule-file",
        type=str,
        default="lich_tuoi_demo.json",
        help="Schedule file path (default: lich_tuoi_demo.json)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto mode: dùng recommendation từ forecast (nếu có)",
    )
    parser.add_argument(
        "--skip-inference",
        action="store_true",
        help="Skip running inference, chỉ dùng manual decisions",
    )
    parser.add_argument(
        "--lookahead",
        type=int,
        default=60,
        help="Lookahead minutes để tìm slots (default: 60)",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎯 DEMO IRRIGATION DECISION")
    print("=" * 70)
    
    # 1. Load schedule
    schedule_file = DATA_DIR / args.schedule_file
    print(f"\n📂 Loading schedule from {schedule_file.name}...")
    
    try:
        schedule = load_schedule_from_file(schedule_file)
    except FileNotFoundError:
        print(f"❌ File không tồn tại: {schedule_file}")
        print(f"   Hãy chạy demo_scheduler.py trước để tạo lich_tuoi_demo.json")
        return
    
    # 2. Nhận thời gian hiện tại cho demo
    current_time = get_demo_current_time()
    
    # 3. Tìm slots sắp tới
    print(f"\n🔍 Finding slots within {args.lookahead} minutes...")
    
    if INFERENCE_AVAILABLE and not args.skip_inference:
        upcoming_slots = find_upcoming_slots(
            schedule,
            lookahead_minutes=args.lookahead,
            find_next=True,
        )
    else:
        # Manual: tìm slots dựa trên start_ts
        slots = schedule.get("slots", [])
        upcoming_slots = []
        for slot in slots:
            start_ts_str = slot.get("start_ts", "")
            if start_ts_str:
                start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
                time_diff = (start_ts - current_time).total_seconds() / 60
                if 0 <= time_diff <= args.lookahead:
                    upcoming_slots.append(slot)
    
    if not upcoming_slots:
        print("⚠️  Không có slot nào sắp tới.")
        return
    
    # 4. Hiển thị slots
    display_slots(upcoming_slots, current_time)
    
    # 5. Nhận quyết định cho từng slot
    print("\n" + "=" * 70)
    print("💬 GETTING DECISIONS")
    print("=" * 70)
    
    updated_slots = []
    for i, slot in enumerate(upcoming_slots, 1):
        decision = get_decision_for_slot(slot, i, auto_mode=args.auto)
        
        if decision["decision"] == "skip":
            print(f"   ⏭️  Skipped slot {i}")
            continue
        
        # Cập nhật slot với quyết định
        updated_slot = update_slot_with_decision(slot, decision)
        updated_slots.append(updated_slot)
        
        # Publish quyết định lên MQTT
        print(f"\n   📡 Publishing decision for slot {i}...")
        publish_decision_to_mqtt(updated_slot, decision)
        
        print(f"   ✓ Slot {i}: {decision['decision'].upper()} - {decision['reason']}")
    
    # 6. Cập nhật schedule
    print("\n" + "-" * 70)
    print("📝 Updating schedule...")
    print("-" * 70)
    
    for updated_slot in updated_slots:
        # Tìm và cập nhật slot trong schedule
        for j, original_slot in enumerate(schedule.get("slots", [])):
            if original_slot.get("start_ts") == updated_slot.get("start_ts"):
                schedule["slots"][j] = updated_slot
                break
    
    # 7. Lưu schedule đã cập nhật
    output_file = DATA_DIR / f"{schedule_file.stem}_decisions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved updated schedule to {output_file.name}")
    
    # 8. Publish schedule update lên MQTT
    print("\n📡 Publishing schedule update to MQTT...")
    publish_schedule_update_to_mqtt(schedule)
    
    # 9. Summary
    print("\n" + "=" * 70)
    print("✅ DEMO IRRIGATION DECISION COMPLETED")
    print("=" * 70)
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Slots processed: {len(updated_slots)}")
    print(f"Output file: {output_file.name}")
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

