#include "mqtt_client.h"
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "../config.h"
#include "../network/ntp_time.h"
#include "../control/pump_control.h"

// WiFiClientSecure cho kết nối TLS (HiveMQ Cloud)
static WiFiClientSecure espClient;
static PubSubClient mqttClient(espClient);

// Root CA (Let's Encrypt)
const char* root_ca PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgISA5u4k2a9A3Vdjf6zVJpO0I48MA0GCSqGSIb3DQEBCwUA
MEoxCzAJBgNVBAYTAlVTMRYwFAYDVQQKDA1MZXQncyBFbmNyeXB0MQ8wDQYDVQQD
DAZJQ0FfQ0EwHhcNMjQwMzA1MDcwMDAwWhcNMzQwMzA1MDcwMDAwWjBKMQswCQYD
VQQGEwJVUzEWMBQGA1UECgwNTGV0J3MgRW5jcnlwdDEPMA0GA1UEAwwGSUNBX0NB
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAuP6G3c8D2qzYwYHhzZoK
3I0NJo+0DBTuwbO2hc+lF6Pb4L91A5CGFnjSTBPG2E4IbO4T2/yFoR9br3uT5ZNP
dE1vBpwEMJXrT2UO0EyqlC9a3WSCXW3JzkFh5yGhJYrbbdkd21Cm4ynwrDUkI4fA
YB0Rjffo3h3cMbW7K2E9WsvOrq6+n2GEnlghFOuZrIhArwNh9ZJH/boTVem6NYG4
v+H86y5b6BfL53sIoe7ZbAbnT2IB0q9zHKt+R5EX6QeAbnRAh2+7R2i5gOGFs4uD
p2MZgkN4Su9s4qDzpgY1tOvZZiR8MFQDXVYsoZZUsJ2SgUUDipM+5v3UQ+HxWe61
53dQTVugCVVzt8r+wFc3/p7qBlDUUxR9QknX3Jm7zB0kB8qZzAF+3ZhD1r1Z+xV5
AUpjGLsNnYwMjIUZyCP2f/fDvbKcE2q8IotjQOmrkAztL3tM1RQJc7e8yOlfMOMk
d/6kDdOdAlkE0Ph7JvbAYETB95nTTjZht+SbpH8Cw+Pp0S1tXsvr17B8HXz/mQ==
-----END CERTIFICATE-----
)EOF";

// ========== Callback khi nhận message MQTT ==========
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    String msg;
    for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
    Serial.printf("📩 MQTT <- %s : %s\n", topic, msg.c_str());

    // Nếu payload là JSON
    DynamicJsonDocument doc(256);
    auto err = deserializeJson(doc, msg);

    String action;
    if (!err) {
        action = doc["action"] | "";
    } else {
        // Nếu không phải JSON, coi payload là "ON"/"OFF"
        action = msg;
    }

    // xử lý pump
    if (String(topic) == TOPIC_DEVICE_CONTROL) {
        Serial.printf("🧠 Command: %s\n", action.c_str());
        if (action == "ON") pump_on();
        else if (action == "OFF") pump_off();

        String state = pump_is_on() ? "ON" : "OFF";
        String logMsg = "{\"source\":\"MQTT\",\"pump\":\"" + state + "\"}";
        mqtt_publish(TOPIC_DEVICE_STATUS, logMsg);
    }
}

// =================== Kết nối MQTT ===================
void mqtt_connect() {
    while (!mqttClient.connected()) {
        Serial.print("🔄 Connecting to MQTT...");
        String clientId = String(DEVICE_ID) + "-" + String(random(0xffff), HEX);
        if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
            Serial.println("✅ Connected!");

            // Subscribe các topic lệnh
            mqttClient.subscribe(TOPIC_DEVICE_CONTROL);
            mqttClient.subscribe(TOPIC_DEVICE_FORCE);

            // Thông báo thiết bị online
            mqtt_publish(TOPIC_DEVICE_STATUS, "{\"status\":\"online\"}");
        } else {
            Serial.printf("❌ Failed rc=%d. Retry in 5s...\n", mqttClient.state());
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
