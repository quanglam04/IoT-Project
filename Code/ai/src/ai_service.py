"""
AI Service - Real-time MQTT Integration for Rain Nowcasting (Production)
========================================================================
Service này:
1. Subscribe MQTT topic 'sensor/data/push' để nhận data từ ESP32
2. Lưu data vào sensor_live.csv (theo collect_data_mqtt.py)
3. Lưu buffer 120 phút data (cần cho feature engineering)
4. Tự động sinh lịch tưới 7 ngày từ scheduler.py khi start
5. Tự động check và chạy inference 10 phút trước mỗi slot tưới (production)
6. Publish kết quả dự báo + quyết định tưới lên topic 'ai/forecast/rain'
7. Publish lịch tưới lên topic 'ai/schedule/irrigation'

Run: python src/ai_service.py
"""

import os
import json
import time
import logging
import csv
import ssl
import threading
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
import pandas as pd
import numpy as np
import joblib
from dotenv import load_dotenv

# Feature engineering
from feature_engineering import (
    FEATURE_NAMES,
    compute_feature_from_window,
    FeatureVector,
)

# Scheduler imports (7-day irrigation plan)
from scheduler import (
    load_sensor as sched_load_sensor,
    load_forecast_daily as sched_load_forecast_daily,
    compute_soil_reference as sched_compute_soil_reference,
    build_day_plans as sched_build_day_plans,
    build_output_json as sched_build_output_json,
)

# Pre-irrigation check imports
try:
    from pre_irrigation_check import (
        load_schedule,
        find_upcoming_slots,
        run_forecast_for_slot,
        update_slot_with_forecast,
    )
    PRE_IRRIGATION_AVAILABLE = True
except ImportError:
    PRE_IRRIGATION_AVAILABLE = False

# ===== Load environment =====
load_dotenv()

# Parse MQTT broker URL (có thể có prefix mqtts:// hoặc mqtt://)
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
    USE_TLS = None

MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "server")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "Server123456")

# Nếu chưa xác định TLS, dựa vào port (8883, 8884 thường là TLS)
if USE_TLS is None:
    USE_TLS = MQTT_PORT in [8883, 8884]

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"

# API data files (CSV giả lập)
OWM_CSV = DATA_DIR / "owm_history.csv"
EXT_WEATHER_CSV = DATA_DIR / "external_weather_60d.csv"

# Sensor live CSV (lưu data từ MQTT - theo collect_data_mqtt.py)
SENSOR_LIVE_CSV = DATA_DIR / "sensor_live.csv"
SENSOR_LIVE_FIELDNAMES = ['ts', 'device_id', 'temp_c', 'rh_pct', 'pressure_hpa', 'soil_moist_pct']

# Schedule file
SCHEDULE_FILE = DATA_DIR / "lich_tuoi.json"

# ===== Setup logging =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== Load models =====
logger.info("Loading AI models...")
try:
    with open(MODEL_DIR / "metadata.json", "r") as f:
        META = json.load(f)
    
    MODEL_NOWCAST = joblib.load(MODEL_DIR / "xgb_nowcast.pkl")
    MODEL_AMOUNT = joblib.load(MODEL_DIR / "xgb_amount.pkl")
    
    logger.info("✓ Models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load models: {e}")
    MODEL_NOWCAST = None
    MODEL_AMOUNT = None
    META = {}

# ===== Sensor Buffer (120 phút / 24 records) =====
class SensorBuffer:
    """Buffer lưu 120 phút data sensor (24 records @ 5 min interval)"""
    
    def __init__(self, max_size: int = 24):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
    
    def add(self, data: Dict):
        """Thêm data vào buffer"""
        self.buffer.append(data)
    
    def is_ready(self) -> bool:
        """Kiểm tra xem đã đủ data chưa (cần ít nhất 12 records = 60 phút)"""
        return len(self.buffer) >= 12
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert buffer thành DataFrame"""
        if not self.buffer:
            return pd.DataFrame()
        
        df = pd.DataFrame(list(self.buffer))
        if 'timestamp' in df.columns:
            df['ts'] = pd.to_datetime(df['timestamp'])
        else:
            df['ts'] = pd.to_datetime([datetime.utcnow()] * len(df))
        
        # Map MQTT format → CSV format
        df['temp_c'] = df.get('temperature', 0)
        df['rh_pct'] = df.get('humidity', 0)
        df['pressure_hpa'] = df.get('pressure', 0)
        df['soil_moist_pct'] = df.get('soilMoisture', 0)
        
        df = df.sort_values('ts')
        return df

# ===== MQTT Client =====
class AIService:
    """AI Service với MQTT integration (Production)"""
    
    def __init__(self):
        self.client = mqtt.Client(
            client_id="ai_service_" + str(int(time.time())),
            clean_session=True,
            protocol=mqtt.MQTTv311
        )
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Setup TLS nếu cần (theo collect_data_mqtt.py)
        if USE_TLS:
            self.client.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None
            )
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.buffer = SensorBuffer(max_size=24)  # 120 phút
        self.running = False
        
        # Topics
        self.TOPIC_SENSOR = "sensor/data/push"  # Subscribe: Nhận data từ ESP32
        self.TOPIC_FORECAST = "ai/forecast/rain"  # Publish: Dự báo mưa + lượng mưa + quyết định tưới
        self.TOPIC_SCHEDULE = "ai/schedule/irrigation"  # Publish: Lịch tưới 7 ngày
        
        # Tạo file CSV nếu chưa có (theo collect_data_mqtt.py)
        if not SENSOR_LIVE_CSV.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(SENSOR_LIVE_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=SENSOR_LIVE_FIELDNAMES)
                writer.writeheader()
            logger.info(f"✓ Created {SENSOR_LIVE_CSV.name}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback khi kết nối thành công"""
        if rc == 0:
            logger.info(f"✓ Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            logger.info(f"🔐 TLS/SSL: {'Enabled' if USE_TLS else 'Disabled'}")
            client.subscribe(self.TOPIC_SENSOR, qos=1)
            logger.info(f"✓ Subscribed to topic: {self.TOPIC_SENSOR}")
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback khi mất kết nối"""
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")
        if rc != 0:
            logger.info("Attempting to reconnect...")
    
    def on_message(self, client, userdata, msg):
        """Xử lý message từ sensor/data/push (theo collect_data_mqtt.py)"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            logger.info(f"← Received message from {topic}")
            
            if topic == self.TOPIC_SENSOR:
                self.handle_sensor_data(payload)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    def save_to_sensor_live_csv(self, data: Dict):
        """Lưu dữ liệu sensor vào sensor_live.csv (theo collect_data_mqtt.py)"""
        try:
            with open(SENSOR_LIVE_CSV, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=SENSOR_LIVE_FIELDNAMES)
                
                # Map data từ ESP32 format sang CSV format (theo collect_data_mqtt.py)
                timestamp = data.get('timestamp', datetime.utcnow().isoformat())
                row = {
                    'ts': timestamp,
                    'device_id': data.get('device_id', 'esp32-01'),
                    'temp_c': float(data.get('temperature', 0)),
                    'rh_pct': float(data.get('humidity', 0)),
                    'pressure_hpa': float(data.get('pressure', 0)),
                    'soil_moist_pct': float(data.get('soilMoisture', 0)),
                }
                writer.writerow(row)
            
            logger.debug(f"✓ Saved to {SENSOR_LIVE_CSV.name}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}", exc_info=True)
    
    def handle_sensor_data(self, payload: str):
        """Xử lý dữ liệu sensor từ MQTT"""
        try:
            data = json.loads(payload)
            
            # Validate data (chỉ cần 4 trường: temperature, humidity, pressure, soilMoisture)
            required_fields = ["temperature", "humidity", "pressure", "soilMoisture"]
            if not all(k in data for k in required_fields):
                logger.warning(f"Missing required fields in sensor data: {data.keys()}")
                return
            
            # Thêm timestamp nếu chưa có
            if "timestamp" not in data:
                data["timestamp"] = datetime.utcnow().isoformat()
            
            # Lưu vào CSV (theo collect_data_mqtt.py)
            self.save_to_sensor_live_csv(data)
            
            # Add to buffer
            self.buffer.add(data)
            logger.info(f"✓ Added to buffer | Size: {len(self.buffer.buffer)}/{self.buffer.max_size}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}", exc_info=True)
    
    # ===== Scheduler integration (7-day irrigation) =====
    def generate_schedule(self) -> Optional[Dict]:
        """
        Sinh JSON lịch tưới 7 ngày bằng scheduler.py (theo scheduler.py)
        """
        try:
            sensor_df = sched_load_sensor()
            forecast_daily = sched_load_forecast_daily()
            soil_ref_7d = sched_compute_soil_reference(sensor_df)
            plans = sched_build_day_plans(forecast_daily, soil_ref_7d)
            schedule_json = sched_build_output_json(plans)
            
            # Tính forecast_trigger_ts cho tất cả slots (start_ts - 10 phút) - PRODUCTION
            for slot in schedule_json.get("slots", []):
                start_ts_str = slot.get("start_ts", "")
                if start_ts_str and "forecast_trigger_ts" not in slot:
                    start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
                    trigger_ts = start_ts - timedelta(minutes=10)  # 10 phút trước (production)
                    slot["forecast_trigger_ts"] = trigger_ts.isoformat() + "Z"

            logger.info(
                "✓ Generated 7-day irrigation schedule "
                f"({len(schedule_json.get('days_detail', []))} days, "
                f"{len(schedule_json.get('slots', []))} slots)"
            )
            
            # Lưu vào file
            with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                json.dump(schedule_json, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Saved schedule to {SCHEDULE_FILE.name}")
            
            return schedule_json

        except FileNotFoundError as e:
            logger.warning(f"Scheduler data missing: {e}")
            return None
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            return None
    
    def check_and_run_pre_irrigation(self):
        """Tự động check slots và chạy inference trước 10 phút (production)"""
        if not PRE_IRRIGATION_AVAILABLE:
            return
        
        try:
            if not SCHEDULE_FILE.exists():
                logger.debug("No schedule file found for pre-irrigation check")
                return
            
            schedule = load_schedule(SCHEDULE_FILE)
            now = datetime.utcnow()
            
            # Tìm slots có forecast_trigger_ts trong vòng 15 phút (hoặc slot tiếp theo)
            upcoming_slots = find_upcoming_slots(schedule, lookahead_minutes=15, find_next=True)
            
            if not upcoming_slots:
                return
            
            logger.info(f"🔮 Found {len(upcoming_slots)} slot(s) for pre-irrigation check")
            
            for slot in upcoming_slots:
                start_ts_str = slot.get("start_ts", "")
                trigger_ts_str = slot.get("forecast_trigger_ts", "")
                
                if not start_ts_str or not trigger_ts_str:
                    continue
                
                start_ts = datetime.fromisoformat(start_ts_str.replace("Z", ""))
                trigger_ts = datetime.fromisoformat(trigger_ts_str.replace("Z", ""))
                
                # Kiểm tra xem đã check chưa
                if slot.get("forecast_checked_at"):
                    continue
                
                # Kiểm tra xem đã đến thời điểm trigger chưa (trong vòng 5 phút)
                time_to_trigger = (trigger_ts - now).total_seconds() / 60
                if -5 <= time_to_trigger <= 5:
                    logger.info(f"⏰ Running pre-irrigation check for slot at {start_ts.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Chạy forecast
                    forecast_result = run_forecast_for_slot(slot)
                    updated_slot = update_slot_with_forecast(slot, forecast_result)
                    
                    # Publish forecast (bao gồm dự báo mưa + lượng mưa + quyết định tưới)
                    # Gộp tất cả vào cùng 1 output: ai/forecast/rain
                    forecast_payload = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "slot_id": start_ts_str,
                        "predictions": forecast_result.get("predictions", {}),
                        "sensor_ref": forecast_result.get("sensor_ref", {}),
                        "recommendation": forecast_result.get("recommendation", {}),
                    }
                    
                    self.client.publish(self.TOPIC_FORECAST, json.dumps(forecast_payload, ensure_ascii=False), qos=1)
                    logger.info(f"→ Published forecast (with decision) to {self.TOPIC_FORECAST}")
                    logger.info(f"   Slot: {start_ts.strftime('%Y-%m-%d %H:%M')}")
                    logger.info(f"   Decision: {'✅ TƯỚI' if forecast_result.get('recommendation', {}).get('should_irrigate') else '⏸️  HOÃN'}")
                    
                    # Cập nhật schedule
                    for i, s in enumerate(schedule.get("slots", [])):
                        if s.get("start_ts") == start_ts_str:
                            schedule["slots"][i] = updated_slot
                            break
                    
                    # Lưu schedule đã cập nhật
                    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                        json.dump(schedule, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"Error in pre-irrigation check: {e}", exc_info=True)
    
    def start(self):
        """Khởi động service"""
        logger.info("=" * 70)
        logger.info("🚀 STARTING AI SERVICE (PRODUCTION MODE)")
        logger.info("=" * 70)
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"TLS/SSL: {'Enabled' if USE_TLS else 'Disabled'}")
        logger.info(f"Username: {MQTT_USERNAME}")
        logger.info(f"Subscribe: {self.TOPIC_SENSOR}")
        logger.info(f"Publish:")
        logger.info(f"  - {self.TOPIC_FORECAST} (Dự báo mưa + lượng mưa + quyết định tưới)")
        logger.info(f"  - {self.TOPIC_SCHEDULE} (Lịch tưới 7 ngày)")
        logger.info(f"Data will be saved to: {SENSOR_LIVE_CSV.name}")
        logger.info("-" * 70)
        
        # 1. Tự động generate và push schedule khi start (theo scheduler.py)
        logger.info("\n📅 Generating 7-day irrigation schedule...")
        schedule = self.generate_schedule()
        if schedule:
            schedule_payload = json.dumps(schedule, ensure_ascii=False)
            self.client.publish(self.TOPIC_SCHEDULE, schedule_payload, qos=1)
            logger.info(f"✓ Published schedule to {self.TOPIC_SCHEDULE}")
            logger.info(f"   Total slots: {len(schedule.get('slots', []))}")
        
        # 2. Kết nối MQTT
        logger.info(f"\n🔌 Connecting to MQTT broker...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            time.sleep(2)  # Đợi kết nối
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            return
        
        # 3. Bắt đầu thread để check pre-irrigation mỗi phút (production: 10 phút trước)
        self.running = True
        
        def pre_irrigation_loop():
            while self.running:
                try:
                    time.sleep(60)  # Check mỗi phút
                    self.check_and_run_pre_irrigation()
                except Exception as e:
                    logger.error(f"Error in pre-irrigation loop: {e}", exc_info=True)
        
        pre_irrigation_thread = threading.Thread(target=pre_irrigation_loop, daemon=True)
        pre_irrigation_thread.start()
        logger.info("✓ Started pre-irrigation check thread (checks every 1 minute, triggers 10 min before slots)")
        
        logger.info("\n" + "-" * 70)
        logger.info("✅ AI Service is running.")
        logger.info("   - Listening for sensor data on MQTT")
        logger.info("   - Pre-irrigation checks run 10 minutes before each slot")
        logger.info("   Press Ctrl+C to stop.")
        logger.info("-" * 70 + "\n")
        
        try:
            # Chạy cho đến khi user dừng
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Service stopped by user")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Service shutdown")


if __name__ == "__main__":
    try:
        service = AIService()
        service.start()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
