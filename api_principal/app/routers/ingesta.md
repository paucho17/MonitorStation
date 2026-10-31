# Modulo `app/routers/ingesta.py`

Recibe las tramas del gateway LoRa. Prefijo `/api`, etiqueta `ingesta`.

| Metodo | Ruta | Acceso | Descripcion |
|---|---|---|---|
| POST | `/api/ingest` | Cabecera `X-API-Key` del gateway | Guarda una lectura y una medicion por variable valida. |

## Proceso
1. Verifica la clave comparando su hash SHA-256 con el del gateway.
2. Registra automaticamente el nodo si aun no existe.
3. Convierte los nombres de `data` a variables con la tabla `variable_alias` (se administra en `/api/alias-variables`, sin cambiar codigo).
4. Descarta valores fuera de rango fisico del sensor.
5. Guarda GPS (latitud, longitud, satelites) y metadatos de radio (RSSI, SNR) si llegan.
6. Compara cada valor con los umbrales y crea alertas: se evalua primero `CRITICO` y luego `ADVERTENCIA`.

El campo opcional `scope` (`MANGLAR`, `VIVERO`, `RIEGO`...) fija el ambito de un nodo nuevo; los nodos ya registrados conservan el suyo (se edita en `/api/nodos`).

## Ejemplo de trama
```json
{
  "gateway": "0xDD", "nodeID": "0xAA", "type": "WATER",
  "rssi": -95, "snr": 7.5,
  "data": {"ph": 7.2, "turbidity": 20.5}
}
```

## Respuestas
201 trama aceptada (con conteo de mediciones y alertas); 401 clave ausente o invalida; 422 formato invalido.
