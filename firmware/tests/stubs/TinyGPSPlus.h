#pragma once
#include <Arduino.h>
struct TinyLoc { bool isValid() { return true; } uint32_t age() { return 0; } double lat() { return 0; } double lng() { return 0; } };
struct TinySat { bool isValid() { return true; } uint32_t value() { return 4; } };
class TinyGPSPlus { public: bool encode(char) { return true; } TinyLoc location; TinySat satellites; };
