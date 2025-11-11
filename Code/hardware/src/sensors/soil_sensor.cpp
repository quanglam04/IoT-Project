#include "soil_sensor.h"
#include "../config.h"
#include <Arduino.h>

void soil_init(){
  analogReadResolution(12); // ESP32 ADC 12-bit: 0..4095
}

int soil_read_raw(){
  int raw = analogRead(PIN_SOIL_ADC);
  return raw;
}

float soil_read_percent(){
  int raw = soil_read_raw();
  // clamp
  int rawDry = SOIL_RAW_DRY;
  int rawWet = SOIL_RAW_WET;
  if (raw > rawDry) raw = rawDry;
  if (raw < rawWet) raw = rawWet;
  float pct = (float)(rawDry - raw) / (float)(rawDry - rawWet) * 100.0;
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}
