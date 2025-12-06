"""
Script thu thập data từ HiveMQ và lưu vào CSV
Chạy: python collect_data_mqtt.py

Data sẽ được lưu vào: ai/data/sensor_live.csv
"""

import paho.mqtt.client as mqtt
import json
import csv
import os
from datetime import datetime
from pathlib import Path
import ssl

# ===================== CẤU HÌNH =====================
# Điền thông tin từ HiveMQ của bạn
MQTT_BROKER = "6737c5bbe1cd42bc9fe23790f95a7e72.s1.eu.hivemq.cloud"
MQTT_PORT = 8883  # SSL port
MQTT_USERNAME = "server"
MQTT_PASSWORD = "Server123456"  
MQTT_TOPIC = "sensor/data/push"

# File output
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "sensor_live.csv"

# Tạo folder nếu chưa có
DATA_DIR.mkdir(exist_ok=True)

# ===================== CẤU TRÚC DỮ LIỆU =====================
# Data từ ESP32 sensor (theo báo cáo: 4 giá trị)
# Bỏ light, chỉ giữ: temp, rh, pressure, soil_moisture
FIELDNAMES = [
    'ts',                # timestamp
    'device_id',         # device ID
    'temp_c',           # nhiệt độ
    'rh_pct',           # độ ẩm không khí
    'pressure_hpa',     # áp suất không khí (BME280)
    'soil_moist_pct',   # độ ẩm đất
]

# Counter
message_count = 0

# ===================== CALLBACK FUNCTIONS =====================

def on_connect(client, userdata, flags, rc):
    """Callback khi kết nối thành công"""
    print("=" * 70)
    if rc == 0:
        print("✅ CONNECTED to HiveMQ Cloud!")
        print(f"📡 Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"🔐 SSL/TLS: Enabled")
        print(f"📨 Subscribing to: {MQTT_TOPIC}")
        print("=" * 70)
        
        # Subscribe topic
        client.subscribe(MQTT_TOPIC, qos=1)
        
        print(f"\n💾 Data will be saved to: {OUTPUT_FILE}")
        print("⏳ Waiting for messages... (Press Ctrl+C to stop)\n")
        
        # Tạo file CSV nếu chưa có (với header)
        if not OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
            print(f"📝 Created new CSV file: {OUTPUT_FILE}\n")
    else:
        print(f"❌ Connection FAILED with code {rc}")
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        print(f"   Error: {error_messages.get(rc, 'Unknown error')}")

def on_message(client, userdata, msg):
    """Callback khi nhận message"""
    global message_count
    
    try:
        # Parse JSON
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)
        
        # Timestamp hiện tại nếu không có trong payload
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Map data từ ESP32 format sang CSV format (theo báo cáo: 4 fields)
        row = {
            'ts': timestamp,
            'device_id': data.get('device_id', 'esp32-01'),
            'temp_c': data.get('temperature', 0),
            'rh_pct': data.get('humidity', 0),
            'pressure_hpa': data.get('pressure', 0),  # BME280 pressure
            'soil_moist_pct': data.get('soilMoisture', 0),
        }
        
        # Validate: Kiểm tra có đủ data không
        if row['temp_c'] == 0 and row['rh_pct'] == 0 and row['soil_moist_pct'] == 0:
            print(f"⚠️  Warning: Received empty data, skipping...")
            return
        
        # Ghi vào CSV
        with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerow(row)
        
        message_count += 1
        
        # Hiển thị thông tin
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{message_count:04d}] {now} | "
              f"Temp: {row['temp_c']:6.2f}°C | "
              f"Humidity: {row['rh_pct']:6.2f}% | "
              f"Pressure: {row['pressure_hpa']:7.2f}hPa | "
              f"Soil: {row['soil_moist_pct']:5.1f}%")
        
        # Thông báo mỗi 10 messages
        if message_count % 10 == 0:
            print(f"\n💾 Saved {message_count} records to {OUTPUT_FILE}\n")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"   Raw payload: {payload_str}")
    except Exception as e:
        print(f"❌ Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    """Callback khi disconnect"""
    if rc != 0:
        print(f"\n⚠️  Unexpected disconnect (code {rc})")
        print("   Trying to reconnect...")

def on_log(client, userdata, level, buf):
    """Callback for logging (optional, for debugging)"""
    # Uncomment để debug
    # print(f"LOG: {buf}")
    pass

# ===================== MAIN =====================

def main():
    print("\n" + "=" * 70)
    print("📡 MQTT DATA COLLECTOR - HiveMQ Cloud")
    print("=" * 70)
    
    # Tạo MQTT client
    client = mqtt.Client(
        client_id=f"collector_{datetime.now().timestamp()}",
        clean_session=True,
        protocol=mqtt.MQTTv311
    )
    
    # Set username & password
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Configure SSL/TLS
    client.tls_set(
        ca_certs=None,
        certfile=None,
        keyfile=None,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None
    )
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    # client.on_log = on_log  # Uncomment for debug
    
    try:
        print(f"🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        print(f"👤 Username: {MQTT_USERNAME}")
        print(f"🔐 SSL/TLS: Enabled")
        
        # Connect
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        
        # Start loop
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("⛔ Stopped by user")
        print(f"💾 Total records saved: {message_count}")
        print(f"📁 File: {OUTPUT_FILE}")
        print("=" * 70)
        client.disconnect()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check MQTT_BROKER and MQTT_PORT")
        print("   2. Check MQTT_USERNAME and MQTT_PASSWORD")
        print("   3. Make sure SSL/TLS is enabled (port 8883)")
        print("   4. Check firewall/network connection")
        print("   5. Test connection with MQTT Explorer first")

if __name__ == "__main__":
    main()

