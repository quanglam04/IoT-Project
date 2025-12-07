#pragma once
#include <Arduino.h>
#include <time.h>

#define MAX_SLOTS 32

struct IrrigationSlot {
    time_t start;          // epoch seconds
    time_t end;            // epoch seconds
    int duration_min;      // server suggested duration
    float soil_ref;        // server soil moisture ref (percent)
    bool executed;         // whether slot action already performed (one-time control for that slot window)
};

extern IrrigationSlot slots[MAX_SLOTS];
extern int slotCount;

void irrigation_load_from_json(const String &jsonPayload);
void irrigation_loop(); // call from main loop periodically (e.g. every 1s)
void irrigation_clear(); // clear loaded slots
bool schedule_is_watering_time();
void irrigation_print_slots();
