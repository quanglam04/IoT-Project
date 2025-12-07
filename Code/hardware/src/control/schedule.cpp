#include "schedule.h"
#include "../network/ntp_time.h"
#include "../control/pump_control.h"
#include "../sensors/soil_sensor.h"
#include <ArduinoJson.h>

IrrigationSlot slots[MAX_SLOTS];
int slotCount = 0;

// ======================================
// Reset schedule
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
// Debug: Print all slots
// ======================================
void irrigation_print_slots() {
    Serial.println("========== 📋 SAVED IRRIGATION SLOTS ==========");

    if (slotCount == 0) {
        Serial.println("⚠️ No irrigation slots saved.");
        return;
    }

    for (int i = 0; i < slotCount; i++) {
        IrrigationSlot &s = slots[i];

        // Không cộng thêm UTC+7!
        time_t start_ts = s.start;
        time_t end_ts   = s.end;

        struct tm start_tm;
        struct tm end_tm;

        localtime_r(&start_ts, &start_tm);
        localtime_r(&end_ts, &end_tm);

        char start_buf[32];
        char end_buf[32];

        strftime(start_buf, sizeof(start_buf), "%Y-%m-%d %H:%M:%S", &start_tm);
        strftime(end_buf, sizeof(end_buf), "%Y-%m-%d %H:%M:%S", &end_tm);

        Serial.printf(
            "Slot %d:\n"
            "  Start (VN)   : %s (epoch %ld)\n"
            "  End   (VN)   : %s (epoch %ld)\n"
            "  Duration     : %d min\n"
            "  Soil Ref     : %.2f%%\n"
            "  Executed     : %s\n",
            i,
            start_buf, s.start,
            end_buf, s.end,
            s.duration_min,
            s.soil_ref,
            s.executed ? "YES" : "NO"
        );
    }

    Serial.println("================================================");
}

// ======================================
// Parse weekly schedule JSON
// ======================================
void irrigation_load_from_json(const String &jsonPayload) {

    DynamicJsonDocument doc(16 * 1024);
    DeserializationError err = deserializeJson(doc, jsonPayload);

    if (err) {
        Serial.printf("❌ Cannot parse irrigation JSON: %s\n", err.c_str());
        return;
    }

    if (!doc.is<JsonArray>()) {
        Serial.println("⚠️ Expected weekly JSON array");
        return;
    }

    JsonArray days = doc.as<JsonArray>();

    irrigation_clear();
    int idx = 0;

    for (JsonObject dayObj : days) {
        JsonArray daySlots = dayObj["slots"];

        if (daySlots.isNull()) {
            Serial.println("📭 No slots for this day → skip");
            continue;
        }

        for (JsonObject item : daySlots) {

            if (idx >= MAX_SLOTS) break;

            // ------------------------------------------------------------------
            // NEW: kiểm tra decision
            // ------------------------------------------------------------------
            bool decision = item["decision"] | false;

            if (!decision) {
                Serial.println("⏭️ Skip slot: decision=false");
                continue;   // không lưu slot này
            }
            // ------------------------------------------------------------------

            const char* start_ts = item["start_ts"] | "";
            const char* end_ts   = item["end_ts"]   | "";

            time_t st = parseISO8601(start_ts);
            time_t en = parseISO8601(end_ts);

            if (st == 0 || en == 0) {
                Serial.printf("⚠️ Bad timestamp: %s - %s\n", start_ts, end_ts);
                continue;
            }

            slots[idx].start        = st;
            slots[idx].end          = en;
            slots[idx].duration_min = item["duration_min"] | 0;

            // Dùng soil_ref = 60.0 mặc định
            slots[idx].soil_ref     = 60.0f; 
            slots[idx].executed     = false;

            Serial.printf("✅ Saved slot %d (%d min): %s → %s\n",
                          idx,
                          slots[idx].duration_min,
                          start_ts, end_ts);

            idx++;
        }
    }

    slotCount = idx;
    Serial.printf("📅 Loaded %d irrigation slots (decision=true only)\n", idx);

    irrigation_print_slots();
}

// ======================================
// MAIN loop — check every 1s
// ======================================
void irrigation_loop() {
    time_t now = get_epoch();
    float soil = soil_read_percent();

    // Nếu pump đang chạy thì không xét slot khác
    if (pump_is_on()) return;

    for (int i = 0; i < slotCount; i++) {
        IrrigationSlot &s = slots[i];

        // Nếu đã tưới hoặc đã skip slot này → bỏ qua
        if (s.executed) continue;

        if (now >= s.start && now < s.end) {

            Serial.printf("⏰ Slot %d ACTIVE: soil=%.2f, ref=%.2f\n",
                          i, soil, s.soil_ref);

            // Điều kiện tưới
            if (soil < s.soil_ref) {

                Serial.printf("🌱 START irrigation for %d min\n", s.duration_min);

                pump_on_with_duration(s.duration_min);

                s.executed = true;   // đánh dấu đã xử lý slot

                return;
            } 
            else {
                Serial.println("⏭ Soil moisture OK → skip this slot");
                s.executed = true;   // slot được xử lý (skip)
            }
        }
    }
}

// ======================================
// Check if now is inside any watering slot
// ======================================
bool schedule_is_watering_time() {
    time_t now = get_epoch();

    for (int i = 0; i < slotCount; i++) {
        if (now >= slots[i].start && now < slots[i].end) return true;
    }

    return false;
}
