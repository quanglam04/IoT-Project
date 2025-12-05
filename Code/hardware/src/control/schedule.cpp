#include "schedule.h"
#include "../network/ntp_time.h"
#include "../control/pump_control.h"
#include "../sensors/soil_sensor.h"
#include <ArduinoJson.h>

IrrigationSlot slots[MAX_SLOTS];
int slotCount = 0;

// ======================================
// Reset slot
// ======================================
void irrigation_clear() {
    slotCount = 0;
    for (int i = 0; i < MAX_SLOTS; i++) {
        slots[i].start = 0;
        slots[i].end = 0;
        slots[i].duration_min = 0;
        slots[i].soil_ref = 0;
        slots[i].executed = false;
    }
}

// ======================================
// Parse JSON từ server
// ======================================
void irrigation_load_from_json(const String &jsonPayload) {
    DynamicJsonDocument doc(16 * 1024);
    DeserializationError err = deserializeJson(doc, jsonPayload);

    if (err) {
        Serial.printf("❌ Cannot parse irrigation JSON: %s\n", err.c_str());
        return;
    }

    JsonArray arr = doc["slots"];
    if (arr.isNull()) {
        Serial.println("⚠️ JSON missing field 'slots'");
        return;
    }

    irrigation_clear();
    int idx = 0;

    for (JsonObject item : arr) {
        if (idx >= MAX_SLOTS) break;

        const char* start_ts = item["start_ts"] | "";
        const char* end_ts   = item["end_ts"]   | "";

        time_t st = parseISO8601(start_ts);
        time_t en = parseISO8601(end_ts);

        if (st == 0 || en == 0) {
            Serial.printf("⚠️ Bad timestamp: %s - %s\n", start_ts, end_ts);
            continue;
        }

        slots[idx].start         = st;
        slots[idx].end           = en;
        slots[idx].duration_min  = item["duration_min"]     | 0;
        slots[idx].soil_ref      = item["soil_moist_ref"]   | 60.0f;
        slots[idx].executed      = false;

        idx++;
    }

    slotCount = idx;
    Serial.printf("📅 Loaded %d irrigation slots\n", slotCount);
}

// ======================================
// Main irrigation loop (1s/lần)
// ======================================
void irrigation_loop() {
    time_t now  = get_epoch();
    float soil  = soil_read_percent();

    if (pump_is_on()) return;

    for (int i = 0; i < slotCount; i++) {
        IrrigationSlot &s = slots[i];

        if (now >= s.start && now < s.end) {

            Serial.printf("⏰ Slot %d active: soil=%.2f, ref=%.2f\n",
                          i, soil, s.soil_ref);

            if (soil < 60.0f && soil < s.soil_ref) {
                Serial.printf("🌱 Irrigation START (%d min)\n", s.duration_min);

                pump_on_with_duration(s.duration_min);
                return;
            } else {
                Serial.println("⏭ Soil is sufficient → skip this slot");
            }
        }
    }
}

// ======================================
// TRUE nếu đang trong thời gian tưới
// ======================================
bool schedule_is_watering_time() {
    time_t now = get_epoch();
    for (int i = 0; i < slotCount; i++) {
        if (now >= slots[i].start && now < slots[i].end) {
            return true;
        }
    }
    return false;
}
