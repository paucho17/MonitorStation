/**
 * IoTAnalogo.h - Entradas analogicas con ADS1115 (16 bits, I2C 0x48).
 *
 * Se usa un ADS1115 en lugar del ADC del ESP32 porque este es no lineal y
 * ruidoso, y porque libera pines. Ganancia x1 (+-4.096 V). Con el ADS1115
 * alimentado a 3.3 V, ninguna entrada debe superar 3.6 V: los sensores de
 * salida de 0 a 5 V (turbidez) requieren un divisor de tension.
 */

#ifndef IOT_ANALOGO_H
#define IOT_ANALOGO_H

#include <Adafruit_ADS1X15.h>
#include <Arduino.h>
#include <Wire.h>

class IoTAnalogo {
 public:
  /** @return false si el ADS1115 no responde en el bus. */
  bool iniciar(TwoWire &bus = Wire, uint8_t direccion = 0x48) {
    _ok = _ads.begin(direccion, &bus);
    if (_ok) _ads.setGain(GAIN_ONE);
    return _ok;
  }
  bool presente() const { return _ok; }

  /** Voltaje promedio del canal (0 a 3) en voltios, o NAN si no hay ADS. */
  float voltios(uint8_t canal, int muestras = 8) {
    if (!_ok) return NAN;
    float suma = 0;
    for (int i = 0; i < muestras; i++) {
      suma += _ads.computeVolts(_ads.readADC_SingleEnded(canal));
    }
    return suma / muestras;
  }

 private:
  Adafruit_ADS1115 _ads;
  bool _ok = false;
};

#endif  // IOT_ANALOGO_H
