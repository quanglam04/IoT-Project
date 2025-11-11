#pragma once
#include <Arduino.h>
#include <time.h>

void ntp_init();
time_t get_epoch();
String iso_now();