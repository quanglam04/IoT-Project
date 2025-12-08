// mqtt_client.cpp
#include "mqtt_client.h"
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "../network/fota_update.h"
#include "../config.h"
#include "../network/ntp_time.h"
#include "../control/pump_control.h"
#include "../control/schedule.h"

// TLS client + PubSubClient
static WiFiClientSecure espClient;
static PubSubClient mqttClient(espClient);

// (Optional) Root CA (Let's Encrypt). Replace with full cert if you want verify server.
const char* root_ca = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgISA5u4k2a9A3Vdjf6zVJpO0I48MA0GCSqGSIb3DQEBCwUA
...
-----END CERTIFICATE-----
)EOF";

// ------------------------- Forward declarations -------------------------
void mqtt_heartbeat();
void mqtt_publish(const char* topic, const String &payload, bool retain);

// ------------------------- MQTT message callback -----------------------
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    String msg;
    msg.reserve(length);
    for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

    Serial.printf("📩 MQTT <- %s : %s\n", topic, msg.c_str());

    DynamicJsonDocument doc(1024);
    bool jsonOK = (deserializeJson(doc, msg) == DeserializationError::Ok);
    String action = jsonOK ? (doc["action"] | "") : msg;

    // Pump control
    if (String(topic) == TOPIC_DEVICE_CONTROL) {
        Serial.printf("🧠 Pump command: %s\n", action.c_str());
        if (action == "ON") pump_on();
        else if (action == "OFF") pump_off();

        String state = pump_is_on() ? "ON" : "OFF";
        String logMsg = "{\"source\":\"mqtt\",\"pump\":\"" + state + "\"}";
        mqtt_publish(TOPIC_PUMP_STATUS, logMsg, false); // retained status
        return;
    }

    // Force commands
    if (String(topic) == TOPIC_DEVICE_FORCE) {
        Serial.printf("🧠 Force command: %s\n", action.c_str());
        if (action == "RESTART") {
            Serial.println("🔄 Restarting device...");
            delay(300);
            ESP.restart();
        }
        return;
    }

    // FOTA
    if (String(topic) == TOPIC_DEVICE_UPDATE) {
        Serial.println("🚀 OTA command received!");
        if (!jsonOK || !doc.containsKey("url")) {
            Serial.println("⚠️ ERROR: Payload OTA missing 'url'");
            return;
        }
        String otaUrl = doc["url"].as<String>();
        Serial.println("🔗 Firmware URL: " + otaUrl);
        fota_update(otaUrl);
        return;
    }

    // Schedule payload
    if (String(topic) == TOPIC_DEVICE_SCHEDULE) {
        Serial.println("📥 Received irrigation schedule via MQTT");
        irrigation_load_from_json(msg);
        return;
    }
}

// ------------------------- MQTT connect -------------------------------
void mqtt_connect() {
    while (!mqttClient.connected()) {
        Serial.print("🔄 Connecting to MQTT... ");

        String clientId = String(DEVICE_ID) + "-" + String(random(0xffff), HEX);

        // LWT: retain = true so FE shows offline when abrupt disconnect
        bool ok = mqttClient.connect(
            clientId.c_str(),
            MQTT_USER,
            MQTT_PASS,
            LWT_TOPIC,
            1,               // qos
            false,            // retain LWT
            "{\"status\":\"offline\"}"
        );

        if (ok) {
            Serial.println("✅ MQTT connected");

            // subscribe topics
            mqttClient.subscribe(TOPIC_DEVICE_CONTROL);
            mqttClient.subscribe(TOPIC_DEVICE_FORCE);
            mqttClient.subscribe(TOPIC_DEVICE_UPDATE);
            mqttClient.subscribe(TOPIC_DEVICE_SCHEDULE);

            // publish online retained
            mqtt_publish(TOPIC_DEVICE_STATUS, String("{\"status\":\"online\",\"device\":\"") + DEVICE_ID + "\"}", false);

        } else {
            Serial.printf("❌ MQTT connect failed rc=%d - retry in 3s\n", mqttClient.state());
            delay(3000);
        }
    }
}

// ------------------------- MQTT init ----------------------------------
void mqtt_init() {
    espClient.setInsecure();

    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(onMqttMessage);

    mqttClient.setKeepAlive(15); // seconds
    mqttClient.setSocketTimeout(5);
}

// ------------------------- MQTT loop ----------------------------------
static bool wifiLost = false;

void mqtt_loop() {
    // 1) If WiFi lost -> close TLS socket to trigger broker LWT, do not attempt reconnect while WiFi down
    if (WiFi.status() != WL_CONNECTED) {
        if (!wifiLost) {
            Serial.println("⚠️ WiFi LOST -> closing TLS socket to allow broker LWT");
            espClient.stop(); // close TCP/TLS socket
            wifiLost = true;
        }
        return;
    }

    // WiFi restored
    if (wifiLost) {
        Serial.println("📡 WiFi restored -> reconnect MQTT");
        wifiLost = false;
    }

    // Reconnect if MQTT disconnected
    if (!mqttClient.connected()) {
        mqtt_connect();
    }

    // Normal loop
    mqttClient.loop();

    // send heartbeat periodically while connected
    if (mqttClient.connected()) mqtt_heartbeat();
}

// ------------------------- Publish helpers ----------------------------
void mqtt_publish(const char* topic, const String &payload, bool retain) {
    if (!mqttClient.connected()) {
        Serial.printf("⚠️ Skipped publish %s: not connected\n", topic);
        return;
    }
    bool ok = mqttClient.publish(topic, payload.c_str(), retain);
    if (ok) Serial.printf("📤 MQTT %s (retain=%d) → %s\n", topic, retain ? 1 : 0, payload.c_str());
    else Serial.printf("⚠️ MQTT publish failed %s\n", topic);
}

// overload without retain (default false)
void mqtt_publish(const char* topic, const String &payload) {
    mqtt_publish(topic, payload, false);
}

// publish raw buffer with retain option
void mqtt_publish_buffer(const char* topic, const uint8_t* buf, size_t len, bool retain) {
    if (!mqttClient.connected()) {
        Serial.printf("⚠️ Skipped publish %s: not connected\n", topic);
        return;
    }
    bool ok = mqttClient.publish(topic, buf, len, retain);
    if (ok) Serial.printf("📤 MQTT %s (buf,len=%u,retain=%d) ok\n", topic, (unsigned)len, retain ? 1 : 0);
    else Serial.printf("⚠️ MQTT publish failed %s\n", topic);
}

// ------------------------- Publish sensor -----------------------------
void mqtt_publish_sensor(JsonDocument &doc) {
    if (!mqttClient.connected()) {
        Serial.println("⚠️ MQTT publish skipped: not connected");
        return;
    }
    char buf[512];
    size_t n = serializeJson(doc, buf);
    mqtt_publish_buffer(TOPIC_SENSOR_PUSH, (const uint8_t*)buf, n, false);
}

// ------------------------- Heartbeat (retain) -------------------------
void mqtt_heartbeat() {
    static unsigned long lastBeat = 0;
    const unsigned long intervalMs = 5000; // 5 giây

    if (millis() - lastBeat < intervalMs) return;
    lastBeat = millis();

    if (!mqttClient.connected()) {
        Serial.println("⚠️ HEARTBEAT skipped: MQTT not connected");
        return;
    }

    DynamicJsonDocument doc(256);
    doc["status"] = "online";
    doc["ts"] = get_epoch();

    // Log JSON payload trước khi publish
    String jsonStr;
    serializeJson(doc, jsonStr);

    // Không publish RETAINED message
    bool ok = mqttClient.publish(
        TOPIC_DEVICE_STATUS,
        jsonStr.c_str(),
        false // retain
    );
}

// ------------------------- MQTT flush helper ---------------------------
void mqtt_flush(unsigned long timeoutMs) {
    unsigned long deadline = millis() + timeoutMs;
    while (millis() < deadline) {
        mqtt_loop();
        delay(0);
    }
}

