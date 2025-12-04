#include "fota_update.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Update.h>

void fota_update(String url) {
    Serial.println("🔄 Starting OTA update...");
    Serial.printf("📡 Downloading: %s\n", url.c_str());

    WiFiClientSecure client;
    client.setInsecure();  

    HTTPClient http;

    if (!http.begin(client, url)) {
        Serial.println("❌ OTA begin failed!");
        return;
    }

    int httpCode = http.GET();
    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("❌ HTTP GET failed: %d\n", httpCode);
        http.end();
        return;
    }

    int total = http.getSize();
    WiFiClient * stream = http.getStreamPtr();

    Serial.printf("📦 Firmware size: %d bytes\n", total);
    delay(200);

    if (!Update.begin(total)) {
        Serial.printf("❌ Not enough space: %s\n", Update.errorString());
        http.end();
        return;
    }

    size_t written = Update.writeStream(*stream);

    if (written != total) {
        Serial.printf("❌ Written only %d / %d bytes\n", written, total);
        http.end();
        Update.abort();
        return;
    }

    if (!Update.end()) {
        Serial.printf("❌ OTA Error: %s\n", Update.errorString());
        http.end();
        return;
    }

    http.end();

    Serial.println("✅ OTA Update Successful!");
    Serial.println("🔁 Restarting device...");
    delay(1000);
    ESP.restart();
}
