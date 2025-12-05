#include "bme_sensor.h"
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include "../config.h"

static Adafruit_BME280 bme; // I2C instance

bool bme_init(){
  Wire.begin(I2C_SDA, I2C_SCL);
  delay(200);  // cho BME280 ổn định sau khi cấp nguồn

  Serial.println("Initializing BME280 on I2C...");

  // MUST pass &Wire when using ESP32 with custom SDA/SCL
  if (!bme.begin(0x76, &Wire)) {
    Serial.println("BME280 not found at 0x76. Trying 0x77...");
    if (!bme.begin(0x77, &Wire)) {
      Serial.println("BME280 not found at 0x76 or 0x77.");
      return false;
    }
  }

  Serial.println("BME280 found!");
  return true;
}

float bme_read_temperature(){
  return bme.readTemperature();
}

float bme_read_humidity(){
  return bme.readHumidity();
}

float bme_read_pressure(){
  return bme.readPressure() / 100.0F;
}
