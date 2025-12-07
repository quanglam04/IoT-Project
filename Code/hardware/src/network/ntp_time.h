#pragma once
#include <Arduino.h>
#include <time.h>

void ntp_init();
time_t get_epoch();
String iso_now();

// Prototype:
time_t parseISO8601(const char* iso8601); // parses "YYYY-MM-DDTHH:MM:SS" (local)
