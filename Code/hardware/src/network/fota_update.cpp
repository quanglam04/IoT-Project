#include "fota_update.h"
#include "config.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Update.h>

#include "../network/mqtt_client.h"  

bool fota_update(String url) {

    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"starting\"}");

    Serial.println("\n==============================");
    Serial.println("🚀 FOTA UPDATE START (HTTPS)");
    Serial.println("==============================");
    Serial.printf("📡 Downloading from: %s\n", url.c_str());

    WiFiClientSecure client;
    client.setInsecure();

    HTTPClient http;

    if (!http.begin(client, url)) {
        Serial.println("❌ ERROR: http.begin() thất bại!");
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"begin\"}");
        return false;
    }

    int httpCode = http.GET();
    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("❌ HTTP GET FAILED: %d\n", httpCode);
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"download\"}");
        http.end();
        return false;
    }

    int total = http.getSize();
    if (total <= 0) {
        Serial.println("❌ ERROR: File OTA rỗng hoặc không đúng!");
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"invalid_file\"}");
        http.end();
        return false;
    }

    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"downloading\",\"size\":" + String(total) + "}");

    WiFiClient *stream = http.getStreamPtr();

    if (!Update.begin(total)) {
        Serial.printf("❌ Update.begin() ERROR: %s\n", Update.errorString());
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"flash_begin\"}");
        http.end();
        return false;
    }

    size_t written = Update.writeStream(*stream);

    mqtt_publish(TOPIC_UPDATE_STATUS, 
        "{\"status\":\"writing\",\"written\":" + String(written) + "," +
        "\"total\":" + String(total) + "}"
    );

    if (written != total) {
        Serial.printf("❌ ERROR: Chỉ ghi %d / %d bytes\n", written, total);
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"write_mismatch\"}");
        Update.abort();
        http.end();
        return false;
    }

    if (!Update.end()) {
        Serial.printf("❌ OTA ERROR: %s\n", Update.errorString());
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"flash_end\"}");
        http.end();
        return false;
    }

    http.end();

    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"done\"}");

    Serial.println("🔁 Restart trong 1s...");
    delay(1000);

    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"rebooting\"}");
    ESP.restart();

    return true;
}
