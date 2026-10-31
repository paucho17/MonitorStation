#pragma once
#include <Arduino.h>
#define WL_CONNECTED 3
#define WIFI_STA 1
class WiFiClient {};
class WiFiClass {
 public:
  int status() { return 0; }
  void mode(int) {}
  void begin(const char *, const char *) {}
  void disconnect() {}
  void setAutoReconnect(bool) {}
};
extern WiFiClass WiFi;
