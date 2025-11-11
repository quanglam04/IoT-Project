#pragma once

// Cấu hình WiFi
#define WIFI_SSID       "Bo"      // SSID WiFi 
#define WIFI_PASSWORD   "hwgc5970"  // Mật khẩu

// MQTT Broker
#define MQTT_BROKER     "6737c5bbe1cd42bc9fe23790f95a7e72.s1.eu.hivemq.cloud"     // Địa chỉ public broker
#define MQTT_PORT       8883
#define MQTT_USER       "server"
#define MQTT_PASS       "Server123456"

// Device infor
#define DEVICE_ID       "esp32-001"                     // Định danh thiết bị (phân biệt khi có nhiều thiết bị khác nhau)
#define LWT_TOPIC       "device/lastwill/" DEVICE_ID    // Last Will and Testament: Đây là topic đặc biệt mà broker sẽ tự động publish khi thiết bị mất kết nối đột ngột => Giám sát online/offline thiết bị

// Topics
#define TOPIC_SENSOR_PUSH       "sensor/data/push"              // Thiết bị gửi dữ liệu cảm biến => Publish
#define TOPIC_DEVICE_CONTROL    "device/control/pump"       // Nhận lệnh hẹn giờ hoặc tưới tự động từ server => Subcribe
#define TOPIC_DEVICE_FORCE      "device/force/manual"           // Nhận lệnh điều khiển thủ công => Subcribe
#define TOPIC_DASHBOARD_SENSOR  "dashboard/update/sensor"       // Gửi dữ liệu cập nhật realtime lên dashboard => Publish
#define TOPIC_DEVICE_STATUS     "device/status/" DEVICE_ID      // Gửi trạng thái hoạt động/kết nối của thiết bị => Publish
#define TOPIC_DEVICE_LOG        "device/log/" DEVICE_ID         // Gửi log/cảnh báo về server => Publish

// Pins
#define PIN_SOIL_ADC        34      // Analog input của cảm biến độ ẩm đất
#define PIN_PUMP            23      // Relay điều khiển motor
#define I2C_SDA             21      // SDA
#define I2C_SCL             22      // SCL            4       
#define PIN_OVERRIDE_BTN    33      // Nút nhấn thủ công bật/tắt bơm

// Timing
#define SENSOR_INTERVAL_MS  15000UL             // Thời gian giữa hai lần đọc cảm biến và gửi dữ liệu là 30s 
#define MQTT_RECONNECT_MS   5000UL              // Thời gian chờ giữa hai lần thử reconnect MQTT là 5s
#define MANUAL_OVERRIDE_TIMEOUT_MS  1200000UL   // Thời gian cho phép chạy bơm ở chế độ thủ công tối đa là 20 phút

// Safety
#define MAX_PUMP_RUNTIME_SEC    600     // Define thời gian bơm mặc định tối đa là 10 phút

// Soil calibration (raw ADC -> percent)
#define SOIL_RAW_DRY   3000   // dry reading 
#define SOIL_RAW_WET   1000   // wet reading 