/**
 * IoTRadio.h - Radio LoRa SX1276 con RadioLib (T-Beam y LoRa32, 915 MHz).
 *
 * Los parametros de radio deben ser IDENTICOS en el gateway y en todos los
 * nodos; si uno difiere, los paquetes simplemente no se reciben. Para cambiar
 * uno en toda la red (por ejemplo el factor de dispersion tras las pruebas de
 * alcance) se define antes de incluir esta biblioteca, o se edita aqui.
 *
 * La recepcion se atiende por interrupcion: el radio levanta una bandera y el
 * programa solo lee el paquete cuando llega, sin sondear el radio.
 *
 * Requiere RadioLib 6.0 o superior.
 */

#ifndef IOT_RADIO_H
#define IOT_RADIO_H

#include <Arduino.h>
#include <RadioLib.h>
#include <SPI.h>
#include "IoTProtocolo.h"

#ifndef IOT_FRECUENCIA_MHZ
#define IOT_FRECUENCIA_MHZ 915.0   // Banda unica de la red
#endif
#ifndef IOT_ANCHO_BANDA_KHZ
#define IOT_ANCHO_BANDA_KHZ 125.0
#endif
#ifndef IOT_FACTOR_SF
#define IOT_FACTOR_SF 12           // Bajar a 9 en TODA la red si el alcance (<= 1.5 km) lo permite
#endif
#ifndef IOT_CODING_RATE
#define IOT_CODING_RATE 5          // Equivale a 4/5
#endif
#ifndef IOT_PALABRA_SYNC
#define IOT_PALABRA_SYNC 0x77
#endif
#ifndef IOT_POTENCIA_DBM
#define IOT_POTENCIA_DBM 17
#endif

// Bandera de la interrupcion de recepcion (un solo radio por placa)
static volatile bool iotPaqueteRecibido = false;
static void IRAM_ATTR iotAlRecibirPaquete() { iotPaqueteRecibido = true; }

class IoTRadio {
 public:
  /** Los pines DIO1 no se usan: la recepcion se resuelve con DIO0. */
  IoTRadio(int cs, int dio0, int rst) : _radio(new Module(cs, dio0, rst, RADIOLIB_NC)) {}

  /**
   * Inicializa el SPI y el radio con los parametros de la red.
   * @return RADIOLIB_ERR_NONE si todo salio bien; otro codigo de RadioLib si falla.
   */
  int iniciar(int sck, int miso, int mosi, int cs) {
    SPI.begin(sck, miso, mosi, cs);
    int estado = _radio.begin(IOT_FRECUENCIA_MHZ, IOT_ANCHO_BANDA_KHZ, IOT_FACTOR_SF,
                              IOT_CODING_RATE, IOT_PALABRA_SYNC, IOT_POTENCIA_DBM);
    if (estado != RADIOLIB_ERR_NONE) return estado;
    _radio.setCRC(true);
    _radio.setPacketReceivedAction(iotAlRecibirPaquete);
    return _radio.startReceive();
  }

  /** Pone el radio en escucha. */
  void escuchar() { _radio.startReceive(); }

  /** Apaga el radio (bajo consumo) entre envios. */
  void dormir() { _radio.sleep(); }

  /** Transmite una trama y vuelve a escuchar. @return Codigo de RadioLib. */
  int enviar(uint8_t destino, uint8_t origen, uint8_t id, const char *payload) {
    uint8_t buf[IOT_TRAMA_MAX];
    size_t n = iotTramaConstruir(destino, origen, id, payload, buf, sizeof(buf));
    if (n == 0) return RADIOLIB_ERR_PACKET_TOO_LONG;
    iotPaqueteRecibido = false;
    int estado = _radio.transmit(buf, n);
    _radio.startReceive();
    return estado;
  }

  /**
   * Si llego un paquete, lo lee y lo decodifica.
   * @return true si hay una trama valida en `t` (RSSI y SNR quedan disponibles).
   */
  bool recibir(IotTrama &t) {
    if (!iotPaqueteRecibido) return false;
    iotPaqueteRecibido = false;
    uint8_t buf[IOT_TRAMA_MAX];
    size_t largo = _radio.getPacketLength();
    if (largo > sizeof(buf)) largo = sizeof(buf);
    int estado = _radio.readData(buf, largo);
    _rssi = (int)_radio.getRSSI();
    _snr = _radio.getSNR();
    _radio.startReceive();
    return estado == RADIOLIB_ERR_NONE && iotTramaLeer(buf, largo, &t);
  }

  /** Espera una trama hasta `esperaMs`. @return true si llego una valida. */
  bool esperarTrama(IotTrama &t, uint32_t esperaMs) {
    uint32_t inicio = millis();
    while (millis() - inicio < esperaMs) {
      if (recibir(t)) return true;
      delay(5);
    }
    return false;
  }

  int rssi() const { return _rssi; }
  float snr() const { return _snr; }

 private:
  SX1276 _radio;
  int _rssi = 0;
  float _snr = 0;
};

#endif  // IOT_RADIO_H
