/**
 * IoTSensorSuelo.h - Humedad de suelo con sensor capacitivo v1.2.
 *
 * El voltaje es alto con el sensor al aire (0 %) y baja al sumergirlo en agua
 * (100 %). La calibracion de dos puntos se guarda en memoria no volatil
 * (Preferences) y sobrevive a reinicios y cortes de energia.
 */

#ifndef IOT_SENSOR_SUELO_H
#define IOT_SENSOR_SUELO_H

#include <Arduino.h>
#include <Preferences.h>
#include "IoTAnalogo.h"
#include "IoTCalculos.h"
#include "IoTSensoresAgua.h"

class IoTSensorSuelo {
 public:
  IoTSensorSuelo(IoTAnalogo *adc, uint8_t canal) : _adc(adc), _canal(canal) {}

  /** Carga la calibracion guardada (valores de fabrica orientativos si no hay). */
  void iniciar() {
    Preferences m;
    m.begin("suelo", true);
    _vSeco = m.getFloat("vSeco", 2.60f);
    _vHumedo = m.getFloat("vHumedo", 1.20f);
    m.end();
  }
  bool conectado() { return iotVoltajePlausible(_adc->voltios(_canal, 4)); }

  /** @return Humedad en %, o NAN si no hay sensor o la calibracion es invalida. */
  float leer() {
    float v = _adc->voltios(_canal, 16);
    return iotVoltajePlausible(v) ? iotHumedadDesdeVoltaje(v, _vSeco, _vHumedo) : NAN;
  }
  void calibrarSeco() { _vSeco = _adc->voltios(_canal, 32); guardar(); }
  void calibrarHumedo() { _vHumedo = _adc->voltios(_canal, 32); guardar(); }
  float voltaje() { return _adc->voltios(_canal, 16); }
  float vSeco() const { return _vSeco; }
  float vHumedo() const { return _vHumedo; }

 private:
  void guardar() {
    Preferences m;
    m.begin("suelo", false);
    m.putFloat("vSeco", _vSeco);
    m.putFloat("vHumedo", _vHumedo);
    m.end();
  }
  IoTAnalogo *_adc;
  uint8_t _canal;
  float _vSeco = 2.60f, _vHumedo = 1.20f;
};

#endif  // IOT_SENSOR_SUELO_H
