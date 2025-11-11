#include "sensor_manager.h"
#include "bme_sensor.h"
#include "soil_sensor.h"
#include "../network/mqtt_client.h"
#include "../network/ntp_time.h"
#include "../config.h"

static unsigned long lastSensorMillis = 0;

void sensor_manager_init(){
  bme_init();
  soil_init();
}

void sensor_manager_loop_check(){
  unsigned long now = millis();
  if (now - lastSensorMillis < SENSOR_INTERVAL_MS) return;
  lastSensorMillis = now;

  // read sensors
  float temp = NAN, hum = NAN, press = NAN;
  float soilPct = NAN;

  temp = bme_read_temperature();
  hum = bme_read_humidity();
  press = bme_read_pressure();
  soilPct = soil_read_percent();

  // Build JSON
  StaticJsonDocument<256> doc;
  doc["deviceId"] = DEVICE_ID;
  if (!isnan(temp)) doc["temperature"] = temp;
  if (!isnan(hum)) doc["humidity"] = hum;
  doc["pressure_hpa"] = press;
  doc["soilMoisture"] = soilPct;
  doc["timestamp"] = iso_now(); // from ntp_time.cpp

  // Publish via mqtt wrapper
  mqtt_publish_sensor(doc);

  // Debug
  Serial.print("Published sensor: ");
  serializeJson(doc, Serial);
  Serial.println();
}
