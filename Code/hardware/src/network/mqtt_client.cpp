#include "mqtt_client.h"
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "../network/fota_update.h"
#include "../config.h"
#include "../network/ntp_time.h"
#include "../control/pump_control.h"
#include "../control/schedule.h"

// WiFiClientSecure cho kết nối TLS (HiveMQ Cloud)
static WiFiClientSecure espClient;
static PubSubClient mqttClient(espClient);

// Root CA (Let's Encrypt)
const char* root_ca = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgISA5u4k2a9A3Vdjf6zVJpO0I48MA0GCSqGSIb3DQEBCwUA
MEoxCzAJBgNVBAYTAlVTMRYwFAYDVQQKDA1MZXQncyBFbmNyeXB0MQ8wDQYDVQQD
DAZJQ0FfQ0EwHhcNMjQ0MDMwNTA3MDAwMFoXDTM0MDMwNTA3MDAwMFowSjELMAkG
A1UEBhMCVVMxFjAUBgNVBAoMDUxl dCdzIEVuY3J5cHQxDzANBgNVBAMMBklDQV9D
QTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBALj+ht3PA9qs2MG B4c2a
Ct y ND Sa P tAwU7sGztoXPpRej2yL91A5CGFnjSTBPG2E4Ib O E9v8haEfW697k+WT
T3RNb wac BDCV60 5lDtBMqpQvWt1kg l1tyc5BYeco aSlut t2R3bUKbjKfCsNSQjh
8BgHRGN9 j eHdwxtbst
...
-----END CERTIFICATE-----
)EOF";


// ----------------------------------------------------------------------------
// CALLBACK – Nhận dữ liệu từ MQTT
// ----------------------------------------------------------------------------
void onMqttMessage(char* topic, byte* payload, unsigned int length) {

    // ------------------------------
    // Convert payload → String
    // ------------------------------
    String msg;
    msg.reserve(length);
    for (size_t i = 0; i < length; i++) msg += (char)payload[i];

    Serial.printf("📩 MQTT <- %s : %s\n", topic, msg.c_str());

    // Parse JSON nếu hợp lệ
    DynamicJsonDocument doc(512);
    bool jsonOK = (deserializeJson(doc, msg) == DeserializationError::Ok);

    // Action fallback cho payload dạng "ON", "OFF"
    String action = jsonOK ? (doc["action"] | "") : msg;

    // =========================================================================
    // Xử lý điều khiển bơm
    // topic: device/control/pump
    // =========================================================================
    if (String(topic) == TOPIC_DEVICE_CONTROL) {
        Serial.printf("🧠 Pump command: %s\n", action.c_str());

        if (action == "ON")      pump_on();
        else if (action == "OFF") pump_off();

        String state = pump_is_on() ? "ON" : "OFF";
        String logMsg = "{\"source\":\"mqtt\",\"pump\":\"" + state + "\"}";
        mqtt_publish(TOPIC_DEVICE_STATUS, logMsg);
        return;
    }

    // =========================================================================
    // FORCE command (reset, restart…)
    // =========================================================================
    if (String(topic) == TOPIC_DEVICE_FORCE) {
        Serial.printf("🧠 Force command: %s\n", action.c_str());
        
        if (action == "RESTART") {
            Serial.println("🔄 Restarting device...");
            delay(300);
            ESP.restart();
        }
        return;
    }

    // =========================================================================
    // FOTA Update
    // topic: update/firmware
    // JSON mẫu: { "url": "https://server.com/firmware.bin" }
    // =========================================================================
    if (String(topic) == TOPIC_DEVICE_UPDATE) {
        Serial.println("🚀 OTA command received!");

        if (!doc.containsKey("url")) {
            Serial.println("⚠️ ERROR: Payload OTA không có trường 'url'");
            return;
        }

        String otaUrl = doc["url"].as<String>();
        Serial.println("🔗 Firmware URL: " + otaUrl);

        // Gọi FOTA từ file fota_update.cpp
        fota_update(otaUrl);
        return;
    }

    // nhận schedule JSON
    if (String(topic) == TOPIC_DEVICE_SCHEDULE) {
        Serial.println("📥 Received irrigation schedule via MQTT");
        irrigation_load_from_json(msg); // msg is the String payload you already built
        return;
    }
}

// =================== Kết nối MQTT ===================
void mqtt_connect() {
    while (!mqttClient.connected()) {

        Serial.print("🔄 Connecting to MQTT... ");

        String clientId = String(DEVICE_ID) + "-" + String(random(0xffff), HEX);

        // LWT — thông báo khi thiết bị chết đột ngột
        bool ok = mqttClient.connect(
            clientId.c_str(),
            MQTT_USER,
            MQTT_PASS,
            LWT_TOPIC,
            1,          // QoS
            false,       // Retain
            "{\"status\":\"offline\"}"
        );

        if (ok) {
            Serial.println("✅ Connected!");

            mqttClient.subscribe(TOPIC_DEVICE_CONTROL);
            mqttClient.subscribe(TOPIC_DEVICE_FORCE);
            mqttClient.subscribe(TOPIC_DEVICE_UPDATE);
            mqttClient.subscribe(TOPIC_DEVICE_SCHEDULE);

            mqtt_publish(TOPIC_DEVICE_STATUS, "{\"status\":\"online\"}");
        } else {
            Serial.printf("❌ Failed rc=%d - retry in 5s\n", mqttClient.state());
            delay(5000);
        }
    }
}

// ========== Khởi tạo MQTT ==========
void mqtt_init() {
    espClient.setInsecure();  // tạm bỏ verify CA nếu broker cho phép
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(onMqttMessage);
}

// ========== Loop MQTT ==========
void mqtt_loop() {
    if (!mqttClient.connected()) mqtt_connect();
    mqttClient.loop();
}

// ========== Publish dữ liệu cảm biến ==========
void mqtt_publish_sensor(JsonDocument &doc) {
    char buf[512];
    size_t n = serializeJson(doc, buf);
    boolean ok = mqttClient.publish(TOPIC_SENSOR_PUSH, buf, n);
    if (ok) {
        Serial.println("📤 MQTT publish OK");
    } else {
        Serial.println("⚠️ MQTT publish failed");
    }
}

// =================== Publish chung ===================
void mqtt_publish(const char* topic, const String &payload) {
    mqttClient.publish(topic, payload.c_str());
    Serial.printf("📤 MQTT %s → %s\n", topic, payload.c_str());
}

// MQTT Flush
void mqtt_flush(unsigned long timeoutMs) {
    unsigned long deadline = millis() + timeoutMs;
    while (millis() < deadline) {
        mqtt_loop();
        delay(0);  // yield cho WiFi/MQTT xử lý tối đa
    }
}



