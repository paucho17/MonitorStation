#pragma once
#include <Arduino.h>
#define RADIOLIB_NC (-1)
#define RADIOLIB_ERR_NONE 0
#define RADIOLIB_ERR_PACKET_TOO_LONG (-4)
class Module { public: Module(int, int, int, int) {} };
class SX1276 {
 public:
  SX1276(Module *) {}
  int begin(float, float, uint8_t, uint8_t, uint8_t, int8_t) { return 0; }
  int setCRC(bool) { return 0; }
  void setPacketReceivedAction(void (*)(void)) {}
  int startReceive() { return 0; }
  int sleep() { return 0; }
  int transmit(uint8_t *, size_t) { return 0; }
  size_t getPacketLength() { return 0; }
  int readData(uint8_t *, size_t) { return 0; }
  float getRSSI() { return 0; }
  float getSNR() { return 0; }
};
