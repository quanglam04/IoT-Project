#pragma once
#include <Arduino.h>
void soil_init();
int soil_read_raw();
float soil_read_percent(); // 0..100
