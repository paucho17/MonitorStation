#pragma once
#include <WiFi.h>
class HTTPClient {
 public:
  bool begin(WiFiClient &, const char *) { return true; }
  void addHeader(const char *, const char *) {}
  int POST(uint8_t *, size_t) { return 201; }
  void end() {}
};
