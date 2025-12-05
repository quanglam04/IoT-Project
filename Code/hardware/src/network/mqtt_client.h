#pragma once

#include <ArduinoJson.h>
void mqtt_init();
void mqtt_loop();
void mqtt_publish_sensor(JsonDocument &doc);
void mqtt_publish(const char* topic, const String &payload);
void mqtt_flush(unsigned long timeoutMs);