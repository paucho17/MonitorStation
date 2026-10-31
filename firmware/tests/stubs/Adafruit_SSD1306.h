#pragma once
#include <Adafruit_GFX.h>
#include <Wire.h>
#define SSD1306_SWITCHCAPVCC 2
#define SSD1306_WHITE 1
#define SSD1306_DISPLAYOFF 0xAE
#define SSD1306_DISPLAYON 0xAF
class Adafruit_SSD1306 : public Adafruit_GFX {
 public:
  Adafruit_SSD1306(int, int, TwoWire *, int) {}
  bool begin(uint8_t, uint8_t) { return true; }
  void clearDisplay() {}
  void display() {}
  void setTextSize(int) {}
  void setTextColor(int) {}
  void setCursor(int, int) {}
  void println(const String &) {}
  void ssd1306_command(uint8_t) {}
};
