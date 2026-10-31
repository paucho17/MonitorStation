// Sustituto minimo de Arduino.h para verificar sintaxis en un PC (no es el API real completo).
#pragma once
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#define IRAM_ATTR
#define HEX 16
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define INPUT_PULLDOWN 3
#define HIGH 1
#define LOW 0
#define SERIAL_8N1 0x800001c
#define constrain(a, l, h) ((a) < (l) ? (l) : ((a) > (h) ? (h) : (a)))
class String {
 public:
  String() {}
  String(const char *s) : _s(s) {}
  String(const std::string &s) : _s(s) {}
  String(int v, int base = 10) { char b[32]; snprintf(b, 32, base == 16 ? "%x" : "%d", v); _s = b; }
  String(unsigned v, int base = 10) { char b[32]; snprintf(b, 32, base == 16 ? "%x" : "%u", v); _s = b; }
  String(unsigned char v, int base = 10) { char b[32]; snprintf(b, 32, base == 16 ? "%x" : "%u", v); _s = b; }
  String(unsigned long v) { _s = std::to_string(v); }
  String(float v, int d = 2) { char b[32]; snprintf(b, 32, "%.*f", d, v); _s = b; }
  String(double v, int d = 2) { char b[32]; snprintf(b, 32, "%.*f", d, v); _s = b; }
  String operator+(const String &o) const { return String(_s + o._s); }
  String operator+(const char *o) const { return String(_s + o); }
  friend String operator+(const char *a, const String &b) { return String(std::string(a) + b._s); }
  String &operator+=(const String &o) { _s += o._s; return *this; }
  bool startsWith(const char *p) const { return _s.rfind(p, 0) == 0; }
  const char *c_str() const { return _s.c_str(); }
 private:
  std::string _s;
};
class HardwareSerial {
 public:
  void begin(unsigned long, uint32_t = 0, int = -1, int = -1) {}
  int available() { return 0; }
  int read() { return -1; }
  void println(const String &) {}
  void println(const char *) {}
  void println() {}
  void print(const String &) {}
  int printf(const char *, ...) { return 0; }
  void write(const uint8_t *, size_t) {}
  long parseInt() { return 0; }
};
extern HardwareSerial Serial, Serial1, Serial2;
void delay(uint32_t);
uint32_t millis();
void pinMode(int, int);
void digitalWrite(int, int);
int digitalRead(int);
long random(long, long);
uint32_t esp_random();
