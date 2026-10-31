#pragma once
#include <Wire.h>
#define ADS1X15_ADDRESS 0x48
enum adsGain_t { GAIN_ONE = 0x0200 };
class Adafruit_ADS1115 {
 public:
  bool begin(uint8_t = ADS1X15_ADDRESS, TwoWire * = &Wire) { return true; }
  void setGain(adsGain_t) {}
  int16_t readADC_SingleEnded(uint8_t) { return 0; }
  float computeVolts(int16_t) { return 0; }
};
