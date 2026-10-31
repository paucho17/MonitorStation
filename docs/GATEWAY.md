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
  "scope": "MANGLAR",
  "data": { "ph": 7.2, "turbidity": 20.5, "tds": 350 }
}
```
`scope` es el ámbito del nodo (`MANGLAR`, `VIVERO`, `RIEGO`...). Solo se usa al registrar un nodo nuevo; si falta, se asume `MANGLAR`.

Las claves de `data` ya no están escritas en el código: se resuelven con la tabla `variable_alias` (recurso `/api/alias-variables`). Claves de fábrica:

| type | Claves aceptadas en `data` |
|---|---|
| WATER | `ph`, `turbidity`, `tds`, `waterLevel` (0 o 1), `waterTemp` |
| AMB | `temperature`, `humidity`, `pressure`, `co2`, `pm1`, `pm25`, `pm10` (y `eco2`, `tvoc` del SGP30 anterior) |
| SOIL | `soilHumidity`, `soilTemp` |
| RIEGO | `tankLevel`, `pump`, `flow`, `vbat`, `bat` |
| cualquiera | `bat` (porcentaje de batería) |

Para agregar un sensor nuevo: crear la variable (`/api/variables`), sus alias (`/api/alias-variables`) y, si aplica, sus umbrales (`/api/umbrales`). No se cambia código.

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
