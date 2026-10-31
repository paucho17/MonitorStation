#pragma once
#include <Wire.h>
class Adafruit_BME280 {
 public:
  bool begin(uint8_t, TwoWire *) { return true; }
  float readTemperature() { return 0; }
  float readHumidity() { return 0; }
  float readPressure() { return 0; }
};
