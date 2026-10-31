/**
 * IoTProtocolo.h - Protocolo de la red IoT-Mangrove (sin dependencias de hardware).
 *
 * Este archivo solo usa la biblioteca estandar de C, por lo que se prueba
 * en un PC (ver tests/probar_protocolo.cpp) ademas de compilarse en el ESP32.
 *
 * Trama LoRa (la misma que usaban los nodos anteriores del proyecto):
 *   [DESTINO][ORIGEN][ID][LONGITUD][PAYLOAD ASCII, LONGITUD bytes]
 *   Direcciones de un byte: gateway 0xDD, nodos 0xAA, 0xBB, 0xCC, 0xA1...
 *
 * Payload de datos (el nodo lo envia de forma espontanea):
 *   D;<TIPO>;<AMBITO>;<clave>=<valor>,<clave>=<valor>[;G=<lat>,<lon>,<satelites>]
 *   Ejemplo: D;WATER;MANGLAR;ph=7.20,turbidity=21.5;G=10.98765,-74.80123,8
 *   TIPO   : WATER, AMB o SOIL (codigos de tipo_nodo de la API)
 *   AMBITO : MANGLAR, VIVERO, RIEGO... (codigos de la tabla ambito)
 *   Las claves son los alias que acepta la API (tabla variable_alias), de modo
 *   que un sensor nuevo no obliga a modificar el gateway.
 *
 * Payload de acuse (el gateway responde al nodo con el mismo ID):
 *   A
 */

#ifndef IOT_PROTOCOLO_H
#define IOT_PROTOCOLO_H

#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define IOT_DIR_GATEWAY    0xDD
#define IOT_TRAMA_MAX      255
#define IOT_CABECERA       4
#define IOT_PAYLOAD_MAX    (IOT_TRAMA_MAX - IOT_CABECERA)

/** Trama decodificada. */
struct IotTrama {
  uint8_t destino;
  uint8_t origen;
  uint8_t id;
  uint8_t longitud;
  char payload[IOT_PAYLOAD_MAX + 1];  // Terminado en '\0'
};

/**
 * Construye una trama en `salida`.
 * @return Bytes escritos, o 0 si el payload no cabe o el buffer es pequeno.
 */
inline size_t iotTramaConstruir(uint8_t destino, uint8_t origen, uint8_t id,
                                const char *payload, uint8_t *salida, size_t capacidad) {
  size_t n = strlen(payload);
  if (n > IOT_PAYLOAD_MAX || capacidad < n + IOT_CABECERA) return 0;
  salida[0] = destino;
  salida[1] = origen;
  salida[2] = id;
  salida[3] = (uint8_t)n;
  memcpy(salida + IOT_CABECERA, payload, n);
  return n + IOT_CABECERA;
}

/**
 * Decodifica una trama recibida. Verifica que la longitud declarada coincida
 * con los bytes recibidos para descartar paquetes ajenos o corruptos.
 * @return true si la trama es valida.
 */
inline bool iotTramaLeer(const uint8_t *datos, size_t n, IotTrama *t) {
  if (n < IOT_CABECERA) return false;
  uint8_t longitud = datos[3];
  if ((size_t)longitud + IOT_CABECERA != n) return false;
  t->destino = datos[0];
  t->origen = datos[1];
  t->id = datos[2];
  t->longitud = longitud;
  memcpy(t->payload, datos + IOT_CABECERA, longitud);
  t->payload[longitud] = '\0';
  return true;
}

/** Constructor del payload de datos, sin memoria dinamica. */
class IotPayload {
 public:
  /** Inicia un payload de datos. */
  void iniciar(const char *tipo, const char *ambito) {
    _n = 0;
    _valores = 0;
    _lleno = false;
    _buf[0] = '\0';
    agregarTexto("D;");
    agregarTexto(tipo);
    agregarTexto(";");
    agregarTexto(ambito);
    agregarTexto(";");
  }

  /**
   * Agrega una variable. Los valores no numericos (NAN, infinito) se omiten,
   * por eso un sensor ausente simplemente no aparece en la trama.
   * @return true si se agrego.
   */
  bool agregar(const char *clave, float valor, int decimales = 2) {
    if (!isfinite(valor) || _lleno) return false;
    char num[24];
    snprintf(num, sizeof(num), "%.*f", decimales, (double)valor);
    if (_valores > 0) agregarTexto(",");
    agregarTexto(clave);
    agregarTexto("=");
    agregarTexto(num);
    _valores++;
    return !_lleno;
  }

  /** Agrega la posicion GPS al final del payload. */
  bool agregarGps(double latitud, double longitud, int satelites) {
    if (_lleno) return false;
    char g[56];
    snprintf(g, sizeof(g), ";G=%.6f,%.6f,%d", latitud, longitud, satelites);
    agregarTexto(g);
    return !_lleno;
  }

  int valores() const { return _valores; }
  bool desbordado() const { return _lleno; }
  const char *texto() const { return _buf; }

 private:
  void agregarTexto(const char *s) {
    size_t l = strlen(s);
    if (_n + l > IOT_PAYLOAD_MAX) { _lleno = true; return; }
    memcpy(_buf + _n, s, l + 1);
    _n += l;
  }
  char _buf[IOT_PAYLOAD_MAX + 1];
  size_t _n = 0;
  int _valores = 0;
  bool _lleno = false;
};

namespace iot_detalle {

inline bool claveValida(const char *s, size_t n) {
  if (n == 0 || n > 24) return false;
  for (size_t i = 0; i < n; i++) {
    char c = s[i];
    bool ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_';
    if (!ok) return false;
  }
  return true;
}

inline bool numeroValido(const char *s, size_t n) {
  if (n == 0 || n > 20) return false;
  bool digito = false;
  for (size_t i = 0; i < n; i++) {
    char c = s[i];
    if (c >= '0' && c <= '9') digito = true;
    else if (c != '.' && c != '-' && c != '+' && c != 'e' && c != 'E') return false;
  }
  return digito;
}

/** Copia `s[0..n)` a `salida` como cadena. */
inline void copiar(char *salida, size_t cap, const char *s, size_t n) {
  if (n >= cap) n = cap - 1;
  memcpy(salida, s, n);
  salida[n] = '\0';
}

}  // namespace iot_detalle

/**
 * Convierte un payload de datos en el JSON que espera POST /api/ingest.
 * Es generico: no conoce las variables, solo valida el formato, asi que
 * agregar sensores no exige cambiar el gateway.
 *
 * @return Longitud del JSON, o 0 si el payload es invalido o no cabe en `salida`.
 */
inline size_t iotPayloadAJson(const char *payload, uint8_t origen, uint8_t gateway,
                              int rssi, float snr, char *salida, size_t capacidad) {
  using namespace iot_detalle;
  if (payload[0] != 'D' || payload[1] != ';') return 0;

  // Partes separadas por ';': D, tipo, ambito, datos, [G=...]
  const char *p = payload + 2;
  const char *inicio[4];
  size_t largo[4];
  int partes = 0;
  while (partes < 4) {
    const char *fin = strchr(p, ';');
    inicio[partes] = p;
    largo[partes] = fin ? (size_t)(fin - p) : strlen(p);
    partes++;
    if (!fin) break;
    p = fin + 1;
  }
  if (partes < 3) return 0;

  char tipo[16], ambito[16];
  if (largo[0] == 0 || largo[0] >= sizeof(tipo) || largo[1] == 0 || largo[1] >= sizeof(ambito)) return 0;
  copiar(tipo, sizeof(tipo), inicio[0], largo[0]);
  copiar(ambito, sizeof(ambito), inicio[1], largo[1]);
  for (const char *c = tipo; *c; c++) if (!((*c >= 'A' && *c <= 'Z') || (*c >= '0' && *c <= '9'))) return 0;
  for (const char *c = ambito; *c; c++) if (!((*c >= 'A' && *c <= 'Z') || (*c >= '0' && *c <= '9'))) return 0;

  size_t n = (size_t)snprintf(salida, capacidad,
      "{\"gateway\":\"0x%02X\",\"nodeID\":\"0x%02X\",\"type\":\"%s\",\"scope\":\"%s\",\"rssi\":%d,\"snr\":%.1f",
      gateway, origen, tipo, ambito, rssi, (double)snr);
  if (n >= capacidad) return 0;

  // Posicion GPS opcional (cuarta parte)
  if (partes == 4 && largo[3] > 2 && inicio[3][0] == 'G' && inicio[3][1] == '=') {
    char g[48];
    copiar(g, sizeof(g), inicio[3] + 2, largo[3] - 2);
    double lat, lon;
    int sat;
    if (sscanf(g, "%lf,%lf,%d", &lat, &lon, &sat) == 3) {
      int w = snprintf(salida + n, capacidad - n,
                       ",\"latitude\":%.6f,\"longitude\":%.6f,\"satellites\":%d", lat, lon, sat);
      if (w < 0 || (size_t)w >= capacidad - n) return 0;
      n += (size_t)w;
    }
  }

  // Variables "clave=valor" separadas por coma
  int w = snprintf(salida + n, capacidad - n, ",\"data\":{");
  if (w < 0 || (size_t)w >= capacidad - n) return 0;
  n += (size_t)w;

  const char *d = inicio[2];
  const char *fin_d = d + largo[2];
  bool primero = true;
  while (d < fin_d) {
    const char *coma = (const char *)memchr(d, ',', (size_t)(fin_d - d));
    const char *fin_par = coma ? coma : fin_d;
    const char *igual = (const char *)memchr(d, '=', (size_t)(fin_par - d));
    if (!igual || !claveValida(d, (size_t)(igual - d)) || !numeroValido(igual + 1, (size_t)(fin_par - igual - 1))) return 0;
    w = snprintf(salida + n, capacidad - n, "%s\"%.*s\":%.*s", primero ? "" : ",",
                 (int)(igual - d), d, (int)(fin_par - igual - 1), igual + 1);
    if (w < 0 || (size_t)w >= capacidad - n) return 0;
    n += (size_t)w;
    primero = false;
    d = coma ? coma + 1 : fin_d;
  }
  w = snprintf(salida + n, capacidad - n, "}}");
  if (w < 0 || (size_t)w >= capacidad - n) return 0;
  return n + (size_t)w;
}

#endif  // IOT_PROTOCOLO_H
