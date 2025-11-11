"""
AI Service - Real-time MQTT Integration for Rain Nowcasting
============================================================
Service này:
1. Subscribe MQTT topic 'sensor/data/push' để nhận data từ ESP32
2. Lưu buffer 120 phút data (cần cho feature engineering)
3. Chạy inference mỗi khi có data mới (5 phút)
4. Publish kết quả dự báo lên topic 'ai/forecast/rain'
5. Publish lịch tưới lên topic 'ai/schedule/irrigation'

Run: python src/ai_service.py
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
import pandas as pd
import numpy as np
import joblib
from dotenv import load_dotenv

# ===== Load environment =====
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER_URL", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"

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
    FEATURES = META["features"]
    THRESHOLD = float(META.get("threshold_default", 0.5))
    
    model_nowcast = joblib.load(MODEL_DIR / "xgb_nowcast.pkl")
    model_amount = joblib.load(MODEL_DIR / "xgb_amount.pkl") if (MODEL_DIR / "xgb_amount.pkl").exists() else None
    
    logger.info(f"✓ Loaded models | Features: {len(FEATURES)} | Threshold: {THRESHOLD}")
except Exception as e:
    logger.error(f"Failed to load models: {e}")
    raise

# ===== Data buffer (120 phút = 24 bản ghi × 5 phút) =====
class SensorBuffer:
    """Buffer lưu trữ 120 phút dữ liệu cảm biến để tính features"""
    
    def __init__(self, max_size: int = 24):
        self.buffer = deque(maxlen=max_size)  # rolling window
        self.max_size = max_size
    
    def add(self, data: Dict):
        """Thêm bản ghi mới"""
        self.buffer.append(data)
        logger.debug(f"Buffer size: {len(self.buffer)}/{self.max_size}")
    
    def is_ready(self) -> bool:
        """Kiểm tra đủ data để chạy inference (cần ít nhất 12 bản ghi = 60 phút)"""
        return len(self.buffer) >= 12
    
    def to_dataframe(self) -> pd.DataFrame:
        """Chuyển buffer thành DataFrame"""
        return pd.DataFrame(list(self.buffer))
    
    def clear(self):
        """Xóa buffer"""
        self.buffer.clear()

# ===== Feature engineering =====
def compute_features(df: pd.DataFrame) -> Optional[np.ndarray]:
    """
    Tính toán features từ buffer data
    Trả về vector [1, n_features] hoặc None nếu không đủ data
    """
    if len(df) < 12:
        return None
    
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Lấy bản ghi cuối (hiện tại)
    last = df.iloc[-1]
    
    # Helper functions
    def lag(series, k):
        return series.iloc[-1 - k] if len(series) > k else series.iloc[0]
    
    def mean_last(series, k):
        return series.iloc[-k:].mean()
    
    try:
        feats = {
            "temp_c": last["temperature"],
            "rh_pct": last["humidity"],
            "pressure_hpa": last["pressure"],
            "soil_moist_pct": last["soilMoisture"],
            "rain_mm_5min": last["rain_mm_5min"],
            
            # Deltas (15 phút = 3 bước)
            "pressure_delta15": last["pressure"] - lag(df["pressure"], 3),
            "rh_delta15": last["humidity"] - lag(df["humidity"], 3),
            "temp_delta15": last["temperature"] - lag(df["temperature"], 3),
            
            # Lags 15 phút
            "temp_c_lag15": lag(df["temperature"], 3),
            "rh_pct_lag15": lag(df["humidity"], 3),
            "pressure_hpa_lag15": lag(df["pressure"], 3),
            "soil_moist_pct_lag15": lag(df["soilMoisture"], 3),
            
            # Rolling means 30 phút (6 bước)
            "temp_c_mean30": mean_last(df["temperature"], 6),
            "rh_pct_mean30": mean_last(df["humidity"], 6),
            "pressure_hpa_mean30": mean_last(df["pressure"], 6),
            "soil_moist_pct_mean30": mean_last(df["soilMoisture"], 6),
            
            # Flags
            "rain_in_last_15m": 1 if df["rain_mm_5min"].iloc[-3:].sum() > 0 else 0,
            
            # Time features
            "hour_of_day": last["timestamp"].hour,
            "day_of_week": last["timestamp"].dayofweek,
        }
        
        # Đảm bảo đúng thứ tự features
        x = np.array([feats.get(k, 0.0) for k in FEATURES], dtype="float32").reshape(1, -1)
        return x
    
    except Exception as e:
        logger.error(f"Feature computation error: {e}")
        return None

# ===== Inference =====
def run_inference(buffer: SensorBuffer) -> Optional[Dict]:
    """Chạy inference với buffer hiện tại"""
    
    if not buffer.is_ready():
        logger.warning("Buffer not ready for inference (need 12+ records)")
        return None
    
    df = buffer.to_dataframe()
    x = compute_features(df)
    
    if x is None:
        return None
    
    # Get latest sensor data
    latest = df.iloc[-1]
    
    try:
        # Classification (có/không mưa)
        proba = model_nowcast.predict_proba(x)[0, 1]
        label = 1 if proba >= THRESHOLD else 0
        
        # Regression (lượng mưa)
        amount = 0.0
        if model_amount is not None:
            import xgboost as xgb
            if isinstance(model_amount, xgb.Booster):
                amount = float(max(0.0, model_amount.predict(xgb.DMatrix(x))[0]))
            else:
                amount = float(max(0.0, model_amount.predict(x)[0]))
        
        # Decision logic
        soil_moisture = float(latest["soilMoisture"])
        should_irrigate, reason = decide_irrigation(soil_moisture, proba, label)
        
        result = {
            "timestamp": latest["timestamp"],
            "device_id": latest.get("device_id", "unknown"),
            "predictions": {
                "rain_60min": {
                    "probability": round(float(proba), 4),
                    "label": int(label),
                    "amount_mm": round(amount, 2)
                }
            },
            "sensor_data": {
                "temperature": round(float(latest["temperature"]), 2),
                "humidity": round(float(latest["humidity"]), 2),
                "pressure": round(float(latest["pressure"]), 2),
                "soilMoisture": round(soil_moisture, 2),
                "rain_mm_5min": round(float(latest["rain_mm_5min"]), 2)
            },
            "recommendation": {
                "should_irrigate": should_irrigate,
                "reason": reason,
                "confidence": round(float(0.9 if label == 1 else 0.85), 2)
            }
        }
        
        logger.info(f"✓ Inference: Rain prob={proba:.2%} | Irrigate={should_irrigate} | {reason}")
        return result
    
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        return None

def decide_irrigation(soil_moisture: float, rain_prob: float, rain_label: int) -> tuple:
    """
    Quyết định có nên tưới hay không
    Returns: (should_irrigate: bool, reason: str)
    """
    CRITICAL_MOISTURE = 30.0
    LOW_MOISTURE = 40.0
    HIGH_RAIN_PROB = 0.6
    
    # Case 1: Độ ẩm nguy hiểm → TƯỚI NGAY
    if soil_moisture < CRITICAL_MOISTURE:
        return True, f"Critical moisture ({soil_moisture:.1f}% < {CRITICAL_MOISTURE}%)"
    
    # Case 2: Độ ẩm thấp + ít mưa → TƯỚI
    if soil_moisture < LOW_MOISTURE and rain_prob < 0.4:
        return True, f"Low moisture ({soil_moisture:.1f}%), low rain chance ({rain_prob:.0%})"
    
    # Case 3: Khả năng mưa cao → HOÃN
    if rain_prob > HIGH_RAIN_PROB:
        return False, f"High rain probability ({rain_prob:.0%})"
    
    # Case 4: Độ ẩm OK
    return False, f"Moisture OK ({soil_moisture:.1f}%)"

# ===== MQTT Client =====
class AIService:
    """AI Service với MQTT integration"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id="ai_service_" + str(int(time.time())))
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.buffer = SensorBuffer(max_size=24)  # 120 phút
        
        # Topics
        self.TOPIC_SENSOR = "sensor/data/push"
        self.TOPIC_FORECAST = "ai/forecast/rain"
        self.TOPIC_SCHEDULE = "ai/schedule/irrigation"
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"✓ Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(self.TOPIC_SENSOR)
            logger.info(f"✓ Subscribed to topic: {self.TOPIC_SENSOR}")
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")
        if rc != 0:
            logger.info("Attempting to reconnect...")
    
    def on_message(self, client, userdata, msg):
        """Xử lý message từ sensor/data/push"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            logger.info(f"← Received message from {topic}")
            
            if topic == self.TOPIC_SENSOR:
                self.handle_sensor_data(payload)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    def handle_sensor_data(self, payload: str):
        """Xử lý dữ liệu sensor"""
        try:
            data = json.loads(payload)
            
            # Validate data
            required_fields = ["temperature", "humidity", "pressure", "soilMoisture", "rain_mm_5min", "timestamp"]
            if not all(k in data for k in required_fields):
                logger.warning(f"Missing required fields in sensor data: {data.keys()}")
                return
            
            # Add to buffer
            self.buffer.add(data)
            logger.info(f"✓ Added to buffer | Size: {len(self.buffer.buffer)}/{self.buffer.max_size}")
            
            # Run inference (nếu đủ data)
            if self.buffer.is_ready():
                result = run_inference(self.buffer)
                if result:
                    self.publish_forecast(result)
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}", exc_info=True)
    
    def publish_forecast(self, result: Dict):
        """Publish kết quả dự báo lên MQTT"""
        try:
            payload = json.dumps(result, ensure_ascii=False)
            self.client.publish(self.TOPIC_FORECAST, payload, qos=1)
            logger.info(f"→ Published forecast to {self.TOPIC_FORECAST}")
        
        except Exception as e:
            logger.error(f"Error publishing forecast: {e}")
    
    def start(self):
        """Khởi động service"""
        logger.info("Starting AI Service...")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Subscribe: {self.TOPIC_SENSOR}")
        logger.info(f"Publish: {self.TOPIC_FORECAST}, {self.TOPIC_SCHEDULE}")
        
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_forever()
        
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
        finally:
            self.client.disconnect()
            logger.info("Service shutdown")

# ===== Main =====
if __name__ == "__main__":
    service = AIService()
    service.start()

