/**
 * IoTSensoresAgua.h - Sensores de calidad de agua.
 *
 *   pH        DFRobot SEN0161 (salida 0-3 V), calibracion de dos puntos.
 *   Turbidez  DFRobot SEN0189 (salida hasta 4.5 V: usar divisor de tension).
 *   TDS       DFRobot SEN0244 (salida 0-2.3 V), compensado por temperatura.
 *   Flotador  Interruptor magnetico de nivel.
 *
 * Todos los analogicos se leen con el ADS1115 (IoTAnalogo.h). Los voltajes de
 * calibracion del pH se guardan en memoria no volatil (Preferences).
 */

#ifndef IOT_SENSORES_AGUA_H
#define IOT_SENSORES_AGUA_H

#include <Arduino.h>
#include <Preferences.h>
#include "IoTAnalogo.h"
#include "IoTCalculos.h"

/** Voltaje fuera de este rango = sensor desconectado (entrada flotante o saturada). */
static inline bool iotVoltajePlausible(float v) { return !isnan(v) && v > 0.05f && v < 3.5f; }

class IoTSensorPh {
 public:
  IoTSensorPh(IoTAnalogo *adc, uint8_t canal) : _adc(adc), _canal(canal) {}

  /** Carga la calibracion guardada. Valores de fabrica orientativos si no hay. */
  void iniciar() {
    Preferences m;
    m.begin("ph", true);
    _v7 = m.getFloat("v7", 1.50f);
    _vAcido = m.getFloat("vAcido", 2.03f);
    m.end();
  }
  bool conectado() { return iotVoltajePlausible(_adc->voltios(_canal, 4)); }

  /** @return pH, o NAN si el sensor no esta conectado. */
  float leer() {
    float v = _adc->voltios(_canal, 16);
    return iotVoltajePlausible(v) ? iotPhDesdeVoltaje(v, _v7, _vAcido) : NAN;
  }
  /** Calibracion con el sensor en buffer de pH 7.00. */
  void calibrarPh7() { _v7 = _adc->voltios(_canal, 32); guardar(); }
  /** Calibracion con el sensor en buffer de pH 4.01. */
  void calibrarPh4() { _vAcido = _adc->voltios(_canal, 32); guardar(); }
  float voltaje() { return _adc->voltios(_canal, 16); }
  float v7() const { return _v7; }
  float vAcido() const { return _vAcido; }

 private:
  void guardar() {
    Preferences m;
    m.begin("ph", false);
    m.putFloat("v7", _v7);
    m.putFloat("vAcido", _vAcido);
    m.end();
  }
  IoTAnalogo *_adc;
  uint8_t _canal;
  float _v7 = 1.50f, _vAcido = 2.03f;
};

class IoTSensorTurbidez {
 public:
  /** @param factorDivisor Vsensor / Vadc del divisor (1.5 con 10 kOhm arriba y 20 kOhm abajo). */
  IoTSensorTurbidez(IoTAnalogo *adc, uint8_t canal, float factorDivisor = 1.5f)
      : _adc(adc), _canal(canal), _factor(factorDivisor) {}
  bool conectado() { return iotVoltajePlausible(_adc->voltios(_canal, 4)); }
  /** @return NTU, o NAN si el sensor no esta conectado. */
  float leer() {
    float v = _adc->voltios(_canal, 16);
    return iotVoltajePlausible(v) ? iotNtuDesdeVoltaje(v, _factor) : NAN;
  }

 private:
  IoTAnalogo *_adc;
  uint8_t _canal;
  float _factor;
};

class IoTSensorTds {
 public:
  IoTSensorTds(IoTAnalogo *adc, uint8_t canal) : _adc(adc), _canal(canal) {}
  bool conectado() { return iotVoltajePlausible(_adc->voltios(_canal, 4)); }
  /**
   * @param temperatura Temperatura del agua en C para compensar (NAN usa 25 C).
   * @return ppm, o NAN si el sensor no esta conectado.
   */
  float leer(float temperatura = NAN) {
    float v = _adc->voltios(_canal, 16);
    if (!iotVoltajePlausible(v)) return NAN;
    return iotTdsDesdeVoltaje(v, isnan(temperatura) ? 25.0f : temperatura);
  }

 private:
  IoTAnalogo *_adc;
  uint8_t _canal;
};

/** Flotador magnetico: 1 cuando el nivel de agua alcanzo el sensor. */
class IoTFlotador {
 public:
  /** @param activoBajo true si el contacto cerrado conecta el pin a GND (con pull-up interno). */
  IoTFlotador(int pin, bool activoBajo = true) : _pin(pin), _bajo(activoBajo) {}
  void iniciar() { pinMode(_pin, _bajo ? INPUT_PULLUP : INPUT_PULLDOWN); }
  float leer() { return (digitalRead(_pin) == (_bajo ? LOW : HIGH)) ? 1.0f : 0.0f; }

 private:
  int _pin;
  bool _bajo;
};

#endif  // IOT_SENSORES_AGUA_H
