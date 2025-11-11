#pragma once
#include <Arduino.h>
bool bme_init();
float bme_read_temperature();
float bme_read_humidity();
float bme_read_pressure();
