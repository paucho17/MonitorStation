/**
 * IoTEnergia.h - Alimentacion conmutada de los sensores y PMU de la T-Beam.
 *
 * Alimentacion de sensores: un pin de la placa activa un MOSFET (o modulo de
 * conmutacion) que energiza el riel de sensores. Los sensores solo consumen
 * mientras se mide, lo que prolonga la bateria de los nodos moviles.
 * IMPORTANTE: el riel conmutado alimenta solo los sensores analogicos, el
 * DS18B20 y el PMS5003. Los integrados I2C (OLED, ADS1115, BME280, SCD41) van
 * a 3.3 V permanente: un integrado I2C sin alimentacion sujeta las lineas SDA y
 * SCL a traves de sus diodos de proteccion y bloquearia todo el bus.
 *
 * PMU de la T-Beam: enciende los rieles del radio y del GPS. La T-Beam V1.2
 * trae AXP2101 (por defecto); para una V1.1 con AXP192 se define
 * IOT_TBEAM_AXP192 antes de incluir este archivo.
 */

#ifndef IOT_ENERGIA_H
#define IOT_ENERGIA_H

#include <Arduino.h>
#include <Wire.h>

/** Riel de sensores controlado por un pin digital. */
class IoTAlimentacion {
 public:
  explicit IoTAlimentacion(int pin, bool activoAlto = true) : _pin(pin), _alto(activoAlto) {}

  void iniciar() {
    if (_pin < 0) return;
    pinMode(_pin, OUTPUT);
    apagar();
  }
  /** Energiza el riel y espera el calentamiento de los sensores. */
  void encender(uint32_t calentamientoMs = 1500) {
    if (_pin >= 0) digitalWrite(_pin, _alto ? HIGH : LOW);
    delay(calentamientoMs);
  }
  void apagar() { if (_pin >= 0) digitalWrite(_pin, _alto ? LOW : HIGH); }

 private:
  int _pin;
  bool _alto;
};

#ifdef IOT_USA_PMU_TBEAM
#include <XPowersLib.h>

#ifdef IOT_TBEAM_AXP192
static XPowersAXP192 iotPmu;
#define IOT_PMU_RADIO XPOWERS_LDO2
#define IOT_PMU_GPS   XPOWERS_LDO3
#define IOT_PMU_ADDR  AXP192_SLAVE_ADDRESS
#else
static XPowersAXP2101 iotPmu;
#define IOT_PMU_RADIO XPOWERS_ALDO2
#define IOT_PMU_GPS   XPOWERS_ALDO3
#define IOT_PMU_ADDR  AXP2101_SLAVE_ADDRESS
#endif

/**
 * Inicia la PMU y energiza el radio (siempre) y el GPS (opcional).
 * Debe llamarse ANTES de iniciar el radio.
 * @return false si la PMU no responde.
 */
inline bool iotPmuIniciar(int sda, int scl, bool conGps) {
  if (!iotPmu.begin(Wire, IOT_PMU_ADDR, sda, scl)) return false;
  iotPmu.setPowerChannelVoltage(IOT_PMU_RADIO, 3300);
  iotPmu.enablePowerOutput(IOT_PMU_RADIO);
  if (conGps) {
    iotPmu.setPowerChannelVoltage(IOT_PMU_GPS, 3300);
    iotPmu.enablePowerOutput(IOT_PMU_GPS);
  } else {
    iotPmu.disablePowerOutput(IOT_PMU_GPS);
  }
  iotPmu.enableBattVoltageMeasure();
  return true;
}

/** Enciende o apaga el riel del GPS (apagado entre mediciones ahorra bateria). */
inline void iotPmuGps(bool encendido) {
  if (encendido) {
    iotPmu.setPowerChannelVoltage(IOT_PMU_GPS, 3300);
    iotPmu.enablePowerOutput(IOT_PMU_GPS);
  } else {
    iotPmu.disablePowerOutput(IOT_PMU_GPS);
  }
}

/** Porcentaje de bateria (0-100), o NAN si no hay bateria conectada. */
inline float iotPmuBateria() {
  int p = iotPmu.getBatteryPercent();
  return p < 0 ? NAN : (float)p;
}
#endif  // IOT_USA_PMU_TBEAM

#endif  // IOT_ENERGIA_H
