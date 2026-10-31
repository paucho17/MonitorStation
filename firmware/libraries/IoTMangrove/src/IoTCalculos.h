/**
 * IoTCalculos.h - Conversiones de senal a magnitud fisica (sin hardware).
 *
 * Funciones puras, probadas en PC (tests/probar_protocolo.cpp). Los
 * sensores analogicos se leen con un ADS1115 y entregan voltios; aqui se
 * convierten a pH, NTU, ppm y porcentaje de humedad.
 */

#ifndef IOT_CALCULOS_H
#define IOT_CALCULOS_H

#include <math.h>

/** Limita un valor a [minimo, maximo]. */
inline float iotLimitar(float v, float minimo, float maximo) {
  return v < minimo ? minimo : (v > maximo ? maximo : v);
}

/**
 * pH por interpolacion lineal entre dos soluciones buffer.
 * @param v     Voltaje medido.
 * @param v7    Voltaje con buffer pH 7.00.
 * @param vAcido Voltaje con el buffer acido (pH `phAcido`, normalmente 4.01).
 * @return pH limitado a 0-14, o NAN si la calibracion es degenerada.
 */
inline float iotPhDesdeVoltaje(float v, float v7, float vAcido, float phAcido = 4.01f) {
  if (fabsf(v7 - vAcido) < 1e-4f) return NAN;
  float pendiente = (7.0f - phAcido) / (v7 - vAcido);
  return iotLimitar(7.0f + (v - v7) * pendiente, 0.0f, 14.0f);
}

/**
 * Turbidez (NTU) del sensor SEN0189. La salida baja al aumentar la
 * turbidez. Polinomio del fabricante, valido con salida de 2.5 a 4.2 V; por
 * debajo de 2.5 V el agua es muy turbia y se informa el maximo (3000 NTU).
 * @param v      Voltaje en el ADC (despues del divisor).
 * @param factorDivisor Relacion Vsensor / Vadc (por ejemplo 1.5 con 10k + 20k).
 */
inline float iotNtuDesdeVoltaje(float v, float factorDivisor = 1.0f) {
  float vs = v * factorDivisor;
  if (vs < 2.5f) return 3000.0f;
  float ntu = -1120.4f * vs * vs + 5742.3f * vs - 4352.9f;
  return iotLimitar(ntu, 0.0f, 3000.0f);
}

/**
 * Solidos disueltos (ppm) del sensor SEN0244 con compensacion de temperatura.
 * @param v           Voltaje del sensor.
 * @param temperatura Temperatura del agua en C (25 si no hay sonda).
 */
inline float iotTdsDesdeVoltaje(float v, float temperatura = 25.0f) {
  float coef = 1.0f + 0.02f * (temperatura - 25.0f);
  float vc = v / coef;
  float tds = (133.42f * vc * vc * vc - 255.86f * vc * vc + 857.39f * vc) * 0.5f;
  return iotLimitar(tds, 0.0f, 5000.0f);
}

/**
 * Humedad (%) de un sensor capacitivo: el voltaje es alto al aire y baja al
 * mojarse. Interpolacion lineal entre los voltajes de calibracion.
 * @return 0-100, o NAN si la calibracion es degenerada.
 */
inline float iotHumedadDesdeVoltaje(float v, float vSeco, float vHumedo) {
  if (fabsf(vSeco - vHumedo) < 1e-4f) return NAN;
  return iotLimitar((vSeco - v) * 100.0f / (vSeco - vHumedo), 0.0f, 100.0f);
}

/**
 * Analiza una trama de 32 bytes del PMS5003 (encabezado 0x42 0x4D).
 * Entrega las concentraciones atmosfericas en ug/m3.
 * @return true si el encabezado y la suma de verificacion son correctos.
 */
inline bool iotPmsAnalizar(const unsigned char *t, float *pm1, float *pm25, float *pm10) {
  if (t[0] != 0x42 || t[1] != 0x4D) return false;
  unsigned int suma = 0;
  for (int i = 0; i < 30; i++) suma += t[i];
  unsigned int control = ((unsigned int)t[30] << 8) | t[31];
  if ((suma & 0xFFFF) != control) return false;
  *pm1 = (float)(((unsigned int)t[10] << 8) | t[11]);
  *pm25 = (float)(((unsigned int)t[12] << 8) | t[13]);
  *pm10 = (float)(((unsigned int)t[14] << 8) | t[15]);
  return true;
}

#endif  // IOT_CALCULOS_H
