#include <Arduino.h>
#include "WiFi.h"

#include "config.h"
#include "network/mqtt_client.h"
#include "network/wifi_dynamic.h"
#include "network/ntp_time.h"
#include "sensors/sensor_manager.h"
#include "control/pump_control.h"
#include "control/schedule.h"

// ======================================================
// SETUP
// ======================================================
void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n==========================");
    Serial.println("🚀 ESP32 Smart Irrigation Booting...");
    Serial.println("==========================");

    // ====== WiFi ======
    wifi_dynamic_init();

    // ====== Time (NTP) ======
    ntp_init();

    // ====== MQTT ======
    mqtt_init();

    // ====== Pump ======
    pump_init();

    // ====== Sensors ======
    sensor_manager_init();

    Serial.println("✅ Setup completed.\n");
}

// ======================================================
// LOOP CHÍNH
// ======================================================
void loop() {
    // // Kiểm tra WiFi
    // if (WiFi.status() != WL_CONNECTED) {
    //     Serial.println("⚠️ WiFi lost. Reconnecting...");
    //     WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    //     delay(5000);
    // }

    // MQTT loop & callback
    mqtt_loop();

    // Đọc cảm biến + publish định kỳ
    sensor_manager_loop_check();

    // Lịch tưới
    irrigation_loop();           
    pump_update();
    delay(1000);
}
