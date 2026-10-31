/**
 * IoTBoton.h - Boton con antirrebote (contacto a GND con pull-up).
 */

#ifndef IOT_BOTON_H
#define IOT_BOTON_H

#include <Arduino.h>

class IoTBoton {
 public:
  /** @param pullupInterno false para pines sin pull-up interno (GPIO 34-39): usar resistencia externa. */
  explicit IoTBoton(int pin, bool pullupInterno = true) : _pin(pin), _pullup(pullupInterno) {}

  void iniciar() { pinMode(_pin, _pullup ? INPUT_PULLUP : INPUT); }

  /** @return true una sola vez por pulsacion (flanco de bajada con antirrebote de 40 ms). */
  bool presionado() {
    bool bajo = digitalRead(_pin) == LOW;
    uint32_t ahora = millis();
    if (bajo && !_estabaBajo && ahora - _ultimo > 40) {
      _estabaBajo = true;
      _ultimo = ahora;
      return true;
    }
    if (!bajo) _estabaBajo = false;
    return false;
  }

 private:
  int _pin;
  bool _pullup;
  bool _estabaBajo = false;
  uint32_t _ultimo = 0;
};

#endif  // IOT_BOTON_H
