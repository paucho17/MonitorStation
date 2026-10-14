# Integración del gateway LoRa con la API

El gateway debe enviar cada trama con `POST /api/ingest`, con la cabecera `X-API-Key` (valor de `GATEWAY_API_KEY` en `.env`, o la clave que devuelve `POST /api/gateways`).

## Formato de la trama
```json
{
  "gateway": "0xDD",
  "nodeID": "0xAA",
  "type": "WATER",
  "rssi": -95,
  "snr": 7.5,
  "latitude": 4.1234,
  "longitude": -76.1234,
  "satellites": 8,
  "data": { "ph": 7.2, "turbidity": 20.5, "tds": 350 }
}
```
Las claves de `data` por tipo de nodo:

| type | Claves aceptadas en `data` |
|---|---|
| WATER | `ph`, `turbidity`, `tds`, `waterLevel` (0 o 1) |
| AMB | `temperature`, `humidity`, `pressure`, `eco2`, `tvoc` |
| SOIL | `soilHumidity` |

- Las claves no reconocidas (por ejemplo las del MQ-135 retirado) se ignoran y se informan en la respuesta (`ignoradas`).
- Los valores fuera del rango físico de la variable (por ejemplo pH 40) se descartan (`descartadas`).
- Un nodo desconocido se registra automáticamente en su primer mensaje si su `type` existe.
- `latitude`, `longitude` y `satellites` son opcionales.

## Ejemplo en Arduino (ESP32, HTTP)
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* URL_API  = "http://iotmangrove.info/api/ingest";
const char* API_KEY  = "REEMPLAZAR_POR_GATEWAY_API_KEY";

// Envia una trama JSON a la API. Devuelve el codigo HTTP (201 = guardada).
int enviarTrama(const String& json) {
  HTTPClient http;
  http.begin(URL_API);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  int codigo = http.POST(json);
  http.end();
  return codigo;
}
```
Con HTTPS use `WiFiClientSecure` y `http.begin(cliente, "https://iotmangrove.info/api/ingest")`. En desarrollo puede usar `cliente.setInsecure()`; en producción cargue el certificado raiz con `cliente.setCACert(...)`.

La configuración de Nginx deja `/api/ingest` disponible también por HTTP (puerto 80) para gateways sin soporte TLS. La clave viaja en claro en ese caso: si el firmware soporta HTTPS, elimine ese bloque de `nginx/iotmangrove.conf`.

## Prueba manual
```bash
curl -X POST https://iotmangrove.info/api/ingest \
  -H "Content-Type: application/json" -H "X-API-Key: SU_CLAVE" \
  -d '{"nodeID":"0xAA","type":"WATER","rssi":-90,"snr":6,"data":{"ph":7.4,"turbidity":18}}'
```
