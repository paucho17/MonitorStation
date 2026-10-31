/**
 * IoTTemperaturaSonda.h - Sonda de temperatura DS18B20 (1-Wire).
 *
 * Se usa para el agua (sumergible) y para el suelo (enterrada). Requiere una
 * resistencia de 4.7 kOhm entre la linea de datos y 3.3 V.
 */

#ifndef IOT_TEMPERATURA_SONDA_H
#define IOT_TEMPERATURA_SONDA_H

#include <Arduino.h>
#include <DallasTemperature.h>
#include <OneWire.h>

class IoTTemperaturaSonda {
 public:
  explicit IoTTemperaturaSonda(int pin) : _bus(pin), _sensor(&_bus) {}

  /** @return true si hay al menos una sonda en el bus. */
  bool iniciar() {
    _sensor.begin();
    return _sensor.getDeviceCount() > 0;
  }

  /** Temperatura en C, o NAN si no hay sonda o la lectura es invalida. */
  float leer() {
    _sensor.requestTemperatures();
    float t = _sensor.getTempCByIndex(0);
    return (t == DEVICE_DISCONNECTED_C || t < -55.0f || t > 125.0f) ? NAN : t;
  }

 private:
  OneWire _bus;
  DallasTemperature _sensor;
};

#endif  // IOT_TEMPERATURA_SONDA_H
