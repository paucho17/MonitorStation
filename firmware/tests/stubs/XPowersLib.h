#pragma once
#include <Wire.h>
#define XPOWERS_ALDO2 2
#define XPOWERS_ALDO3 3
#define XPOWERS_LDO2 12
#define XPOWERS_LDO3 13
#define AXP2101_SLAVE_ADDRESS 0x34
#define AXP192_SLAVE_ADDRESS 0x34
template <int N> class XPowersBase {
 public:
  bool begin(TwoWire &, uint8_t, int, int) { return true; }
  bool setPowerChannelVoltage(uint8_t, uint16_t) { return true; }
  bool enablePowerOutput(uint8_t) { return true; }
  bool disablePowerOutput(uint8_t) { return true; }
  void enableBattVoltageMeasure() {}
  int getBatteryPercent() { return 50; }
};
typedef XPowersBase<1> XPowersAXP2101;
typedef XPowersBase<2> XPowersAXP192;
