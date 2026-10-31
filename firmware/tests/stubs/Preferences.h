#pragma once
#include <Arduino.h>
class Preferences {
 public:
  bool begin(const char *, bool = false) { return true; }
  void end() {}
  float getFloat(const char *, float d = 0) { return d; }
  size_t putFloat(const char *, float) { return 4; }
};
