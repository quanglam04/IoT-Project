#include "pump_control.h"
#include "../config.h"
#include "../network/mqtt_client.h"

static bool pumpState = false;  // Trạng thái hiện tại của bơm

// =======================
// Khởi tạo chân Relay
// =======================
void pump_init() {
    pinMode(PIN_PUMP, OUTPUT);

#if RELAY_ACTIVE_HIGH
    digitalWrite(PIN_PUMP, LOW);   // Mặc định tắt relay nếu active HIGH
#else
    digitalWrite(PIN_PUMP, HIGH);  // Mặc định tắt relay nếu active LOW
#endif

    pumpState = false;
    Serial.println("✅ Pump initialized (OFF)");
    pump_publish_status();
}

// =======================
// Bật bơm
// =======================
void pump_on() {
    if (pumpState) return;  // Nếu đã ON thì không làm gì

#if RELAY_ACTIVE_HIGH
    digitalWrite(PIN_PUMP, HIGH);  // bật relay
#else
    digitalWrite(PIN_PUMP, LOW);   // bật relay nếu active LOW
#endif

    pumpState = true;
    Serial.println("🚿 Pump ON");
    pump_publish_status();
}

// =======================
// Tắt bơm
// =======================
void pump_off() {
    if (!pumpState) return;  // Nếu đã OFF thì không làm gì

#if RELAY_ACTIVE_HIGH
    digitalWrite(PIN_PUMP, LOW);   // tắt relay
#else
    digitalWrite(PIN_PUMP, HIGH);  // tắt relay nếu active LOW
#endif

    pumpState = false;
    Serial.println("🛑 Pump OFF");
    pump_publish_status();
}

// =======================
// Đảo trạng thái
// =======================
void pump_toggle() {
    if (pumpState) pump_off();
    else pump_on();
}

// =======================
// Kiểm tra trạng thái
// =======================
bool pump_is_on() {
    return pumpState;
}

// =======================
// Gửi trạng thái lên MQTT
// =======================
void pump_publish_status() {
#ifdef TOPIC_DEVICE_STATUS
    String payload = String("{\"pump\":\"") + (pumpState ? "ON" : "OFF") + "\"}";
    mqtt_publish(TOPIC_DEVICE_STATUS, payload);

    // Log trạng thái chân relay để debug
#if RELAY_ACTIVE_HIGH
    Serial.printf("📤 Pump status published → %s | Pin %d = %s\n",
                  payload.c_str(), PIN_PUMP, digitalRead(PIN_PUMP) ? "HIGH" : "LOW");
#else
    Serial.printf("📤 Pump status published → %s | Pin %d = %s\n",
                  payload.c_str(), PIN_PUMP, digitalRead(PIN_PUMP) ? "LOW" : "HIGH");
#endif
#endif
}
