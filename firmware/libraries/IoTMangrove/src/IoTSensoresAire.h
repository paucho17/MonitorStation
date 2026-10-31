/**
 * IoTSensoresAire.h - Sensores de aire.
 *
 *   BME280   temperatura, humedad relativa y presion (I2C 0x76 o 0x77).
 *   SCD41    CO2 real por fotoacustica (I2C 0x62), en modo de una sola medida
 *            (adecuado con alimentacion conmutada: tarda unos 5 s).
 *   PMS5003  material particulado PM1.0, PM2.5 y PM10 (UART 9600, 5 V).
 *
 * El MQ-135 y el DHT22 de las versiones anteriores quedaron reemplazados.
 */

#ifndef IOT_SENSORES_AIRE_H
#define IOT_SENSORES_AIRE_H

#include <Adafruit_BME280.h>
#include <Arduino.h>
#include <SensirionI2cScd4x.h>
#include <Wire.h>
#include "IoTCalculos.h"

class IoTBme280 {
 public:
  /** @return true si el sensor responde en 0x76 o 0x77. */
  bool iniciar(TwoWire &bus = Wire) {
    _ok = _bme.begin(0x76, &bus) || _bme.begin(0x77, &bus);
    return _ok;
  }
  float temperatura() { return _ok ? _bme.readTemperature() : NAN; }
  float humedad() { return _ok ? _bme.readHumidity() : NAN; }
  /** Presion en hPa. */
  float presion() { return _ok ? _bme.readPressure() / 100.0f : NAN; }
  bool presente() const { return _ok; }

 private:
  Adafruit_BME280 _bme;
  bool _ok = false;
};

class IoTScd41 {
 public:
  /** @return true si el sensor responde. */
  bool iniciar(TwoWire &bus = Wire) {
    _scd.begin(bus, SCD41_I2C_ADDR_62);
    _scd.stopPeriodicMeasurement();   // por si quedo midiendo tras un reinicio
    uint64_t serie = 0;
    // Leer el numero de serie confirma que el sensor responde, sin esperar una medida
    _ok = (_scd.getSerialNumber(serie) == 0);
    return _ok;
  }

  /** Mide y devuelve el CO2 en ppm (bloquea unos 5 s). NAN si falla. */
  float co2() {
    if (!_ok) return NAN;
    uint16_t c;
    float t, h;
    if (_scd.measureAndReadSingleShot(c, t, h) != 0 || c == 0) return NAN;
    return (float)c;
  }
  bool presente() const { return _ok; }

 private:
  SensirionI2cScd4x _scd;
  bool _ok = false;
};

class IoTPms5003 {
 public:
  /**
   * @param puerto Puerto serie (por ejemplo Serial2).
   * @param pinSet Pin SET del sensor (HIGH = activo, LOW = reposo); -1 si no se usa.
   */
  IoTPms5003(HardwareSerial *puerto, int pinSet = -1) : _serie(puerto), _set(pinSet) {}

  void iniciar(int rx, int tx) {
    _serie->begin(9600, SERIAL_8N1, rx, tx);
    if (_set >= 0) { pinMode(_set, OUTPUT); digitalWrite(_set, LOW); }
  }
  void despertar() { if (_set >= 0) digitalWrite(_set, HIGH); }
  void reposo() { if (_set >= 0) digitalWrite(_set, LOW); }

  /**
   * Lee una trama valida. El ventilador necesita unos 30 s tras energizarse
   * para estabilizar la medida: el llamador espera ese tiempo antes.
   * @param esperaMs Tiempo maximo para encontrar una trama completa.
   * @return true si se obtuvo una trama con suma de verificacion correcta.
   */
  bool leer(float *pm1, float *pm25, float *pm10, uint32_t esperaMs = 3000) {
    uint32_t inicio = millis();
    while (_serie->available()) _serie->read();   // descarta datos viejos
    uint8_t buf[32];
    int n = 0;
    while (millis() - inicio < esperaMs) {
      if (!_serie->available()) { delay(2); continue; }
      uint8_t b = (uint8_t)_serie->read();
      if (n == 0 && b != 0x42) continue;
      if (n == 1 && b != 0x4D) { n = (b == 0x42) ? 1 : 0; continue; }
      buf[n++] = b;
      if (n == 32) {
        if (iotPmsAnalizar(buf, pm1, pm25, pm10)) return true;
        n = 0;
      }
    }
    return false;
  }

 private:
  HardwareSerial *_serie;
  int _set;
};

#endif  // IOT_SENSORES_AIRE_H
