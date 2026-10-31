/**
 * IoTGps.h - Posicion GPS (modulo u-blox de la T-Beam) con TinyGPSPlus.
 */

#ifndef IOT_GPS_H
#define IOT_GPS_H

#include <Arduino.h>
#include <TinyGPSPlus.h>

class IoTGps {
 public:
  /** Abre el puerto serie del GPS (9600 baudios en la T-Beam: RX=34, TX=12). */
  void iniciar(int rx, int tx) { Serial1.begin(9600, SERIAL_8N1, rx, tx); }

  /**
   * Espera un fix valido con al menos 4 satelites.
   * @param esperaMs Tiempo maximo de espera.
   * @return true si se obtuvo posicion.
   */
  bool esperarFix(uint32_t esperaMs, double &lat, double &lon, int &satelites) {
    uint32_t inicio = millis();
    while (millis() - inicio < esperaMs) {
      while (Serial1.available()) _gps.encode(Serial1.read());
      if (_gps.location.isValid() && _gps.location.age() < 2000 && _gps.satellites.isValid() &&
          _gps.satellites.value() >= 4) {
        lat = _gps.location.lat();
        lon = _gps.location.lng();
        satelites = (int)_gps.satellites.value();
        return true;
      }
      delay(10);
    }
    return false;
  }

  /** Satelites vistos hasta ahora (para mostrar el avance en pantalla). */
  int satelites() { return _gps.satellites.isValid() ? (int)_gps.satellites.value() : 0; }

  /** Procesa los datos pendientes del GPS (llamar con frecuencia mientras se espera). */
  void atender() { while (Serial1.available()) _gps.encode(Serial1.read()); }

 private:
  TinyGPSPlus _gps;
};

#endif  // IOT_GPS_H
