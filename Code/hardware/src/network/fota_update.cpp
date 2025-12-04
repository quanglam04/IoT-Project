#include "fota_update.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Update.h>

/**
 * Hàm thực hiện OTA từ URL HTTPS
 * url: đường link trỏ đến firmware .bin
 */
bool fota_update(String url) {

    Serial.println("\n==============================");
    Serial.println("🚀 FOTA UPDATE START (HTTPS)");
    Serial.println("==============================");
    Serial.printf("📡 Downloading from: %s\n", url.c_str());

    WiFiClientSecure client;
    client.setInsecure();  // Bỏ kiểm tra chứng chỉ SSL

    HTTPClient http;

    if (!http.begin(client, url)) {
        Serial.println("❌ ERROR: http.begin() thất bại!");
        return false;
    }

    int httpCode = http.GET();
    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("❌ HTTP GET FAILED: %d\n", httpCode);
        http.end();
        return false;
    }

    int total = http.getSize();
    if (total <= 0) {
        Serial.println("❌ ERROR: File OTA rỗng hoặc không đúng!");
        http.end();
        return false;
    }

    Serial.printf("📦 Firmware size: %d bytes\n", total);

    WiFiClient *stream = http.getStreamPtr();

    if (!Update.begin(total)) {
        Serial.printf("❌ Update.begin() ERROR: %s\n", Update.errorString());
        http.end();
        return false;
    }

    size_t written = Update.writeStream(*stream);

    if (written != total) {
        Serial.printf("❌ ERROR: Chỉ ghi %d / %d bytes\n", written, total);
        Update.abort();
        http.end();
        return false;
    }

    if (!Update.end()) {
        Serial.printf("❌ OTA ERROR: %s\n", Update.errorString());
        http.end();
        return false;
    }

    http.end();

    Serial.println("✅ OTA Update thành công!");
    Serial.println("🔁 Restart trong 1s...");
    delay(1000);
    ESP.restart();

    return true;
}

