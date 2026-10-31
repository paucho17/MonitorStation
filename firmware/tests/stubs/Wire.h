#pragma once
#include <Arduino.h>
class TwoWire { public: bool begin(int = -1, int = -1) { return true; } };
extern TwoWire Wire;
