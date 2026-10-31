/**
 * IoTPantalla.h - Pantalla OLED SSD1306 de 128x64 con cuatro lineas de texto.
 */

#ifndef IOT_PANTALLA_H
#define IOT_PANTALLA_H

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <Wire.h>

class IoTPantalla {
 public:
  IoTPantalla() : _oled(128, 64, &Wire, -1) {}

  /** Inicia la pantalla. El bus I2C debe estar iniciado (Wire.begin). @return false si no responde. */
  bool iniciar() {
    _ok = _oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
    return _ok;
  }

  /** Muestra hasta cuatro lineas; las vacias pueden ser "". */
  void mostrar(const String &l1, const String &l2 = "", const String &l3 = "", const String &l4 = "") {
    if (!_ok) return;
    _oled.clearDisplay();
    _oled.setTextSize(1);
    _oled.setTextColor(SSD1306_WHITE);
    const String *lineas[4] = {&l1, &l2, &l3, &l4};
    for (int i = 0; i < 4; i++) {
      _oled.setCursor(0, i * 16);
      _oled.println(*lineas[i]);
    }
    _oled.display();
  }

  /** Apaga la pantalla para ahorrar energia. */
  void apagar() {
    if (_ok) { _oled.clearDisplay(); _oled.display(); _oled.ssd1306_command(SSD1306_DISPLAYOFF); }
  }
  void encender() { if (_ok) _oled.ssd1306_command(SSD1306_DISPLAYON); }

 private:
  Adafruit_SSD1306 _oled;
  bool _ok = false;
};

#endif  // IOT_PANTALLA_H
