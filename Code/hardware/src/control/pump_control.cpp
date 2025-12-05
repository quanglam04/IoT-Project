#include "pump_control.h"
#include "../config.h"
#include "../network/mqtt_client.h"
#include "../sensors/soil_sensor.h"
#include "../network/ntp_time.h"

static bool pumpState = false;
static time_t pumpStartTime = 0;
static time_t pumpScheduledStop = 0;        // thời điểm phải tắt theo duration slot
static const uint32_t MAX_PUMP_SECONDS = 20 * 60;   // Hard limit 20 phút

// =======================
// Khởi tạo bơm
// =======================
void pump_init() {
    pinMode(PIN_PUMP, OUTPUT);

#if RELAY_ACTIVE_HIGH
    digitalWrite(PIN_PUMP, LOW);
#else
    digitalWrite(PIN_PUMP, HIGH);
#endif

    pumpState = false;
    pumpScheduledStop = 0;
    pump_publish_status();
    Serial.println("✅ Pump initialized");
}

// =======================
// BẬT BƠM (không duration)
// =======================
void pump_on() {
    if (pumpState) return;

#if RELAY_ACTIVE_HIGH
    digitalWrite(PIN_PUMP, HIGH);
#else
    digitalWrite(PIN_PUMP, LOW);
#endif

    pumpState = true;
    pumpStartTime = get_epoch();

    Serial.println("🚿 Pump ON");
    pump_publish_status();
}

// =======================
// BẬT BƠM THEO DURATION
// =======================
void pump_on_with_duration(int duration_min) {
    pump_on();
    pumpScheduledStop = get_epoch() + duration_min * 60;

    Serial.printf("⏳ Auto-stop scheduled after %d minutes (at %ld)\n",
                  duration_min, pumpScheduledStop);
}

// =======================
// TẮT BƠM
// =======================
void pump_off() {
    if (!pumpState) return;

#if RELAY_ACTIVE_HIGH
    digitalWrite(PIN_PUMP, LOW);
#else
    digitalWrite(PIN_PUMP, HIGH);
#endif

    pumpState = false;
    pumpScheduledStop = 0;

    Serial.println("🛑 Pump OFF");
    pump_publish_status();
}

// ======================= 
// Đảo trạng thái 
// ======================= 
void pump_toggle() { 
    if (pumpState)  pump_off(); 
    else pump_on(); 
} 

// ======================= 
// Kiểm tra trạng thái 
// ======================= 
bool pump_is_on() {
    return pumpState;
}

// =======================
// AUTO-STOP mỗi 1 giây
// =======================
void pump_update() {
    if (!pumpState) return;

    float soil = soil_read_percent();
    time_t now = get_epoch();

    // Rule 1: đủ ẩm
    if (soil >= 60.0f) {
        Serial.printf("🌧 Auto-stop: soil %.2f >= 60%% → OFF\n", soil);
        pump_off();
        return;
    }

    // Rule 2: hết duration_min
    if (pumpScheduledStop > 0 && now >= pumpScheduledStop) {
        Serial.println("⏱ Auto-stop: reached scheduled duration → OFF");
        pump_off();
        return;
    }

    // Rule 3: hard limit 20 phút
    if (now - pumpStartTime > MAX_PUMP_SECONDS) {
        Serial.println("⏰ Auto-stop: exceeded 20 minutes → OFF");
        pump_off();
        return;
    }
}

// =======================
// MQTT publish
// =======================
void pump_publish_status() {
#ifdef TOPIC_DEVICE_STATUS
    String payload = String("{\"pump\":\"") + (pumpState ? "ON" : "OFF") + "\"}";
    mqtt_publish(TOPIC_DEVICE_STATUS, payload);
#endif
}
