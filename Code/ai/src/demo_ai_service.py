"""
Demo AI Service - Cho phép demo với thời điểm và quyết định tưới tùy chọn.

Workflow:
1. User chọn thời điểm demo
2. User chọn trạng thái bơm cho các slots (confirm/postpone)
3. Tự động đẩy lịch lên MQTT
4. Tự động check và đẩy kết quả trước 1 phút (cho demo)
5. Hiển thị tất cả ở terminal

Cách dùng:
    cd D:\IoT\Code\ai
    python src\demo_ai_service.py
"""

import os
import json
import time
import logging
import threading
import ssl
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Import từ các module khác
from demo_scheduler import (
    get_demo_datetime,
    load_schedule_from_file,
    adjust_dates_in_schedule,
    adjust_slots_for_demo,
    publish_to_mqtt as publish_schedule_to_mqtt,
)
from demo_irrigation_decision import (
    display_slots,
    get_decision_for_slot,
    update_slot_with_decision,
    publish_decision_to_mqtt,
)

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEDULE_INPUT = DATA_DIR / "lich_tuoi.json"
SCHEDULE_DEMO = DATA_DIR / "lich_tuoi_demo.json"

# Parse MQTT broker URL (có thể có prefix mqtts:// hoặc mqtt://)
# Default giống mẫu đã kết nối thành công
MQTT_BROKER_URL = os.getenv("MQTT_BROKER_URL", "mqtts://c35f82397d674292948a051226f10fa6.s1.eu.hivemq.cloud")

# Bỏ prefix mqtts:// hoặc mqtt:// nếu có
if MQTT_BROKER_URL.startswith("mqtts://"):
    MQTT_BROKER = MQTT_BROKER_URL.replace("mqtts://", "")
    USE_TLS = True
elif MQTT_BROKER_URL.startswith("mqtt://"):
    MQTT_BROKER = MQTT_BROKER_URL.replace("mqtt://", "")
    USE_TLS = False
else:
    MQTT_BROKER = MQTT_BROKER_URL
    USE_TLS = None  # Chưa xác định, sẽ dựa vào port

# Port: 8883 (TLS) hoặc 8884 (TLS) cho HiveMQ Cloud, 1883 (plain) cho local
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "server")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "Server123456")

# Nếu chưa xác định TLS, dựa vào port (8883, 8884 thường là TLS)
if USE_TLS is None:
    USE_TLS = MQTT_PORT in [8883, 8884]

# Topics (giống ai_service.py)
TOPIC_SENSOR = "sensor/data/push"  # Không subscribe trong demo, chỉ để tham khảo
TOPIC_FORECAST = "ai/forecast/rain"  # Dự báo mưa + lượng mưa + quyết định tưới (gộp chung)
TOPIC_SCHEDULE = "ai/schedule/irrigation"  # Lịch tưới 7 ngày

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DemoAIService:
    """Demo AI Service với quyết định tưới tùy chọn"""
    
    def __init__(self, demo_time: datetime, schedule: Dict):
        self.demo_time = demo_time
        self.schedule = schedule
        self.client = mqtt.Client(client_id="demo_ai_service_" + str(int(time.time())))
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.running = False
        self.connected = False
        
        # Setup TLS nếu cần
        if USE_TLS:
            self.client.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None
            )
        
        # Setup callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback khi kết nối thành công"""
        if rc == 0:
            self.connected = True
            logger.info(f"✓ Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        else:
            self.connected = False
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback khi mất kết nối"""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")
        if rc != 0:
            logger.info("Attempting to reconnect...")
            try:
                self.client.reconnect()
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")
        
    def setup_mqtt(self):
        """Setup MQTT connection"""
        try:
            logger.info(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            
            # Đợi kết nối (tối đa 5 giây)
            for _ in range(10):
                if self.connected:
                    break
                time.sleep(0.5)
            
            if not self.connected:
                raise Exception("Connection timeout - không thể kết nối sau 5 giây")
                
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            raise
    
    def ensure_connected(self, max_retries=3):
        """Đảm bảo client đã kết nối, reconnect nếu cần"""
        if self.connected:
            return True
        
        for attempt in range(max_retries):
            try:
                if not self.client.is_connected():
                    logger.warning(f"Reconnecting to MQTT (attempt {attempt + 1}/{max_retries})...")
                    self.client.reconnect()
                    time.sleep(1)
                    
                    # Đợi kết nối
                    for _ in range(5):
                        if self.connected:
                            logger.info("✓ Reconnected successfully")
                            return True
                        time.sleep(0.5)
                else:
                    self.connected = True
                    return True
            except Exception as e:
                logger.error(f"Reconnect attempt {attempt + 1} failed: {e}")
        
        return False
    
    def publish_schedule(self):
        """Đẩy lịch tưới lên MQTT"""
        try:
            # Đảm bảo đã kết nối
            if not self.ensure_connected():
                logger.error("Cannot publish schedule: MQTT not connected")
                return False
            
            payload = json.dumps(self.schedule, ensure_ascii=False)
            result = self.client.publish(TOPIC_SCHEDULE, payload, qos=1)
            
            if result.rc != 0:  # 0 = success
                logger.error(f"Publish failed with rc={result.rc}")
                return False
            
            result.wait_for_publish(timeout=5)
            logger.info(f"✓ Published schedule to {TOPIC_SCHEDULE}")
            logger.info(f"   Total slots: {len(self.schedule.get('slots', []))}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish schedule: {e}")
            return False
    
    def check_and_publish_decisions(self):
        """Tự động check slots và đẩy quyết định trước 1 phút (cho demo)"""
        if not self.running:
            return
        
        try:
            now = self.demo_time  # Dùng demo time thay vì real time
            slots = self.schedule.get("slots", [])
            
            upcoming_slots = []
            for slot in slots:
                start_ts_str = slot.get("start_ts", "")
                if not start_ts_str:
                    continue
                
                start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
                time_to_start = (start_ts - now).total_seconds() / 60  # phút
                
                # Tìm slots trong vòng 2 phút (trước 1 phút + sau 1 phút để có buffer)
                if -1 <= time_to_start <= 1:
                    # Kiểm tra xem đã publish chưa
                    if not slot.get("decision_published"):
                        upcoming_slots.append(slot)
            
            if not upcoming_slots:
                return
            
            logger.info(f"🔮 Found {len(upcoming_slots)} slot(s) ready for decision (within 1 minute)")
            
            for slot in upcoming_slots:
                start_ts_str = slot.get("start_ts", "")
                start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
                
                # Lấy quyết định từ slot (đã được user chọn trước đó)
                decision = slot.get("decision", "confirm")
                decision_reason = slot.get("decision_reason", "Demo decision")
                
                # Tạo forecast result giả lập (cho demo)
                forecast_result = slot.get("forecast_result", {
                    "predictions": {
                        "rain_60min": {
                            "probability": 0.3,
                            "label": 0,
                        },
                        "rain_amount_60min_mm": 0.5,
                    },
                    "recommendation": {
                        "should_irrigate": decision == "confirm",
                        "reason": decision_reason,
                    },
                })
                
                # Publish forecast (bao gồm dự báo mưa + lượng mưa + quyết định tưới)
                # Gộp tất cả vào cùng 1 output: ai/forecast/rain (giống ai_service.py)
                forecast_payload = {
                    "timestamp": now.isoformat() + "Z",
                    "slot_id": start_ts_str,
                    "predictions": forecast_result.get("predictions", {}),
                    "sensor_ref": slot.get("pre_irrigation_sensor_ref", {}),
                    "recommendation": forecast_result.get("recommendation", {}),
                }
                
                # Đảm bảo đã kết nối trước khi publish
                if not self.ensure_connected():
                    logger.error(f"Cannot publish forecast for slot {start_ts_str}: MQTT not connected")
                    continue
                
                payload_str = json.dumps(forecast_payload, ensure_ascii=False)
                result = self.client.publish(TOPIC_FORECAST, payload_str, qos=1)
                
                if result.rc != 0:  # 0 = success
                    logger.error(f"Publish failed with rc={result.rc} for slot {start_ts_str}")
                    continue
                
                try:
                    result.wait_for_publish(timeout=5)
                    logger.info(f"→ Published forecast (with decision) to {TOPIC_FORECAST}")
                    logger.info(f"   Slot: {start_ts.strftime('%Y-%m-%d %H:%M')}")
                    logger.info(f"   Decision: {decision.upper()} - {decision_reason}")
                except RuntimeError as e:
                    logger.error(f"Publish timeout or failed: {e}")
                    continue
                
                # Đánh dấu đã publish
                slot["decision_published"] = True
                slot["decision_published_at"] = now.isoformat() + "Z"
                
        except Exception as e:
            logger.error(f"Error in decision check: {e}", exc_info=True)
    
    def run(self):
        """Chạy demo service"""
        logger.info("=" * 70)
        logger.info("🎯 DEMO AI SERVICE")
        logger.info("=" * 70)
        logger.info(f"Demo time: {self.demo_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"TLS/SSL: {'Enabled' if USE_TLS else 'Disabled'}")
        logger.info(f"Username: {MQTT_USERNAME}")
        logger.info(f"Publish topics:")
        logger.info(f"  - {TOPIC_FORECAST} (Dự báo mưa + lượng mưa + quyết định tưới)")
        logger.info(f"  - {TOPIC_SCHEDULE} (Lịch tưới 7 ngày)")
        logger.info("-" * 70)
        
        # 1. Setup MQTT
        self.setup_mqtt()
        
        # 2. Publish schedule
        logger.info("\n📅 Publishing schedule...")
        self.publish_schedule()
        
        # 3. Bắt đầu thread để check và publish decisions
        self.running = True
        
        def decision_loop():
            while self.running:
                try:
                    time.sleep(10)  # Check mỗi 10 giây (cho demo nhanh)
                    self.check_and_publish_decisions()
                except Exception as e:
                    logger.error(f"Error in decision loop: {e}", exc_info=True)
        
        decision_thread = threading.Thread(target=decision_loop, daemon=True)
        decision_thread.start()
        logger.info("✓ Started decision check thread (checks every 10 seconds)")
        
        logger.info("\n" + "-" * 70)
        logger.info("✅ Demo AI Service is running.")
        logger.info("   Decisions will be published automatically 1 minute before each slot.")
        logger.info("   Press Ctrl+C to stop.")
        logger.info("-" * 70 + "\n")
        
        try:
            # Chạy cho đến khi user dừng
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Demo service stopped by user")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Demo service shutdown")


def main():
    """Main function"""
    print("=" * 70)
    print("🎯 DEMO AI SERVICE - SETUP")
    print("=" * 70)
    
    # 1. Load schedule từ production
    print("\n📂 Loading schedule from production...")
    if not SCHEDULE_INPUT.exists():
        print(f"❌ File không tồn tại: {SCHEDULE_INPUT}")
        print(f"   Hãy chạy scheduler.py trước để tạo lich_tuoi.json")
        return
    
    schedule = load_schedule_from_file(SCHEDULE_INPUT)
    print(f"✓ Loaded schedule: {len(schedule.get('slots', []))} slots")
    
    # 2. Lưu schedule gốc để so sánh (deep copy)
    original_schedule = json.loads(json.dumps(schedule))
    original_slots = original_schedule.get("slots", [])
    
    # 3. Nhận thời điểm demo
    print("\n⏰ Setting demo time...")
    demo_datetime = get_demo_datetime()
    
    # 4. Điều chỉnh schedule cho demo (với DEMO_MODE=true để dùng 1 phút)
    print("\n📅 Adjusting schedule for demo...")
    os.environ["DEMO_MODE"] = "true"  # Set để dùng 1 phút thay vì 10 phút
    schedule = adjust_dates_in_schedule(schedule, demo_datetime)
    schedule = adjust_slots_for_demo(schedule, demo_datetime)
    
    # 5. Tìm tất cả slots đã được điều chỉnh (so sánh thời gian trong ngày)
    print("\n💬 Getting decisions for adjusted slots...")
    slots = schedule.get("slots", [])
    demo_date = demo_datetime.date()
    
    # Tìm slots đã được điều chỉnh bằng cách so sánh thời gian trong ngày (hour, minute)
    adjusted_slots = []
    
    # Lấy slots của ngày demo (sau khi điều chỉnh)
    demo_day_slots = [s for s in slots if s.get("date") == demo_date.isoformat()]
    demo_day_slots.sort(key=lambda x: x.get("start_ts", ""))
    
    # Lấy slots gốc của ngày đầu tiên (trước khi điều chỉnh)
    if original_slots:
        first_original_date = original_slots[0].get("date", "")
        original_day_slots = [s for s in original_slots if s.get("date") == first_original_date]
        original_day_slots.sort(key=lambda x: x.get("start_ts", ""))
        
        # So sánh từng slot theo thứ tự
        for i, current_slot in enumerate(demo_day_slots):
            if i < len(original_day_slots):
                original_slot = original_day_slots[i]
                
                try:
                    current_start_ts = datetime.fromisoformat(current_slot.get("start_ts", "").replace("Z", ""))
                    original_start_ts = datetime.fromisoformat(original_slot.get("start_ts", "").replace("Z", ""))
                    
                    # So sánh thời gian trong ngày (hour, minute)
                    if (current_start_ts.hour != original_start_ts.hour or 
                        current_start_ts.minute != original_start_ts.minute):
                        # Slot đã được điều chỉnh
                        adjusted_slots.append(current_slot)
                except Exception:
                    pass
    
    if not adjusted_slots:
        print("⚠️  Không có slot nào đã được điều chỉnh thời gian.")
        return
    
    print(f"\n📋 Found {len(adjusted_slots)} adjusted slot(s) for demo:")
    display_slots(adjusted_slots, demo_datetime)
    
    # Cho user chọn quyết định cho slot đã điều chỉnh
    print("\n" + "=" * 70)
    print("💬 CHOOSE DECISIONS FOR ADJUSTED SLOTS")
    print("=" * 70)
    print("(Chỉ chọn quyết định cho slot đã được điều chỉnh thời gian)")
    print("=" * 70)
    
    for i, slot in enumerate(adjusted_slots, 1):
        decision = get_decision_for_slot(slot, i, auto_mode=False)
        
        if decision["decision"] == "skip":
            print(f"   ⏭️  Skipped slot {i}")
            continue
        
        # Cập nhật slot với quyết định
        updated_slot = update_slot_with_decision(slot, decision)
        
        # Tìm và cập nhật trong schedule
        for j, s in enumerate(schedule.get("slots", [])):
            if s.get("start_ts") == slot.get("start_ts"):
                schedule["slots"][j] = updated_slot
                break
        
        print(f"   ✓ Slot {i}: {decision['decision'].upper()} - {decision['reason']}")
    
    # 5. Lưu schedule demo
    with open(SCHEDULE_DEMO, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Saved demo schedule to {SCHEDULE_DEMO.name}")
    
    # 6. Chạy demo service
    print("\n" + "=" * 70)
    print("🚀 STARTING DEMO AI SERVICE")
    print("=" * 70)
    
    service = DemoAIService(demo_datetime, schedule)
    service.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

