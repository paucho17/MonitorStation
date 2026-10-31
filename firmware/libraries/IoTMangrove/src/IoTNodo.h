/**
 * IoTNodo.h - Envio de datos de un nodo al gateway con acuse de recibo (ACK).
 *
 * El nodo transmite cuando tiene datos (por boton o por temporizador) y espera
 * el acuse del gateway con el mismo ID. Si no llega, reintenta con una espera
 * aleatoria creciente para no chocar con otros nodos. Este modelo permite que
 * los nodos duerman entre envios, a diferencia del sondeo desde el gateway.
 */

#ifndef IOT_NODO_H
#define IOT_NODO_H

#include <Arduino.h>
#include "IoTRadio.h"

/**
 * Envia un payload de datos al gateway y espera su acuse.
 * @param radio       Radio ya inicializado.
 * @param origen      Direccion de este nodo.
 * @param payload     Texto construido con IotPayload.
 * @param reintentos  Intentos totales (3 por defecto).
 * @param esperaAckMs Tiempo de espera del acuse por intento. Con SF12 el viaje
 *                    de ida y vuelta toma varios segundos.
 * @return true si el gateway confirmo la recepcion.
 */
inline bool iotEnviarConAck(IoTRadio &radio, uint8_t origen, const char *payload,
                            uint8_t reintentos = 3, uint32_t esperaAckMs = 6000) {
  static uint8_t contador = 0;
  for (uint8_t intento = 0; intento < reintentos; intento++) {
    uint8_t id = (uint8_t)(++contador ^ (uint8_t)(esp_random() & 0xFF));
    int estado = radio.enviar(IOT_DIR_GATEWAY, origen, id, payload);
    if (estado != RADIOLIB_ERR_NONE) {
      Serial.printf("Error al transmitir (%d)\n", estado);
    } else {
      uint32_t inicio = millis();
      while (millis() - inicio < esperaAckMs) {
        IotTrama t;
        if (radio.esperarTrama(t, esperaAckMs - (millis() - inicio)) &&
            t.destino == origen && t.origen == IOT_DIR_GATEWAY && t.id == id && t.payload[0] == 'A') {
          return true;
        }
      }
    }
    delay(random(500, 1500) * (intento + 1));
  }
  return false;
}

#endif  // IOT_NODO_H
