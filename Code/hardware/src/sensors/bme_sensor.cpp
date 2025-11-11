#include "bme_sensor.h"
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include "../config.h"

static Adafruit_BME280 bme; // I2C

bool bme_init(){
  Wire.begin(I2C_SDA, I2C_SCL);
  if (!bme.begin(0x76)) { // try address 0x76; change to 0x77 if needed
    Serial.println("BME280 not found at 0x76 (try 0x77).");
    return false;
  }
  Serial.println("BME280 found.");
  return true;
}

float bme_read_temperature(){
  return bme.readTemperature(); // Celsius
}

float bme_read_humidity(){
  return bme.readHumidity(); // %
}

float bme_read_pressure(){
  return bme.readPressure() / 100.0F; // hPa
}
