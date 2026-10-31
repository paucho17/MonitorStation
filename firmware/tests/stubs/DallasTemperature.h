#pragma once
#include <OneWire.h>
#define DEVICE_DISCONNECTED_C -127
class DallasTemperature {
 public:
  DallasTemperature(OneWire *) {}
  void begin() {}
  int getDeviceCount() { return 1; }
  void requestTemperatures() {}
  float getTempCByIndex(int) { return 20; }
};
