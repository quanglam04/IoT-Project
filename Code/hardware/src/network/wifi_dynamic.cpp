#include "wifi_dynamic.h"
#include <WiFiManager.h>
#include <WiFi.h>

static WiFiManager wm;

// Tên AP và password cấu hình
const char* AP_NAME = "ESP32-SETUP";
const char* AP_PASS = "12345678";

// ------------------------------------------------------------------
void wifi_dynamic_init() {
    WiFi.mode(WIFI_STA);

    Serial.println("\n=============================");
    Serial.println("📶 WiFi Dynamic Init (Portal)");
    Serial.println("=============================");

    // wm.resetSettings();  // Bỏ comment nếu muốn reset WiFi để test

    // Tự connect -> nếu fail thì bật AP cấu hình
    bool ok = wm.autoConnect(AP_NAME, AP_PASS);

    if (!ok) {
        Serial.println("❌ WiFi Connect Failed! Rebooting...");
        delay(3000);
        ESP.restart();
    }

    Serial.println("✅ WiFi Connected!");
    Serial.print("📡 IP Address: ");
    Serial.println(WiFi.localIP());
}
