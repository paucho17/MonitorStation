#pragma once
#include <Wire.h>
#define SCD41_I2C_ADDR_62 0x62
class SensirionI2cScd4x {
 public:
  void begin(TwoWire &, uint8_t) {}
  int16_t stopPeriodicMeasurement() { return 0; }
  int16_t getSerialNumber(uint64_t &) { return 0; }
  int16_t measureAndReadSingleShot(uint16_t &, float &, float &) { return 0; }
};
