/**
 * Gateway LoRa - LilyGO T-Beam (direccion 0xDD)
 *
 * Descripcion:
 *   Recibe por LoRa (915 MHz, RadioLib) los datos de todos los nodos de la red
 *   (T-Beam moviles y LoRa32 del vivero), responde de inmediato con un acuse
 *   (ACK) y reenvia cada medicion a la API por WiFi con POST /api/ingest.
 *
 * Funcionamiento:
 *   1. La recepcion es por interrupcion; el bucle solo atiende cuando llega un paquete.
 *   2. Si el paquete es de datos, el gateway responde ACK al nodo con el mismo ID
 *      ANTES de hablar con internet, para que el nodo no reintente innecesariamente.
 *   3. Los reintentos de un nodo (mismo origen e ID en 30 s) se confirman pero no se
 *      guardan dos veces.
 *   4. El payload se convierte a JSON (IoTProtocolo.h) sin conocer las variables:
 *      un sensor nuevo en un nodo no obliga a cambiar este programa.
 *   5. Los JSON se guardan en una cola en memoria. Si no hay WiFi o la API no
 *      responde, se conservan (hasta TAM_COLA) y se envian al recuperar la conexion.
 *
 * Configuracion: copiar secrets.h.example como secrets.h y completarlo.
 * Pines (T-Beam V1.2): radio SPI 5/19/27/18, DIO0=26, RST=23; I2C 21/22 (PMU y OLED).
 *
 * Dependencias: ver libraries/IoTMangrove/library.properties
 */

#define IOT_USA_PMU_TBEAM
#include <HTTPClient.h>
#include <IoTEnergia.h>
#include <IoTPantalla.h>
#include <IoTProtocolo.h>
#include <IoTRadio.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include "secrets.h"

// ---------------------------------------------------------------------------
// Pines y ajustes
// ---------------------------------------------------------------------------
const int PIN_SDA = 21, PIN_SCL = 22;
const int PIN_RADIO_CS = 18, PIN_RADIO_SCK = 5, PIN_RADIO_MOSI = 27, PIN_RADIO_MISO = 19;
const int PIN_RADIO_DIO0 = 26, PIN_RADIO_RST = 23;

const uint8_t TAM_COLA = 12;                  // Mediciones que se conservan sin conexion
const size_t TAM_JSON = 480;
const uint32_t VENTANA_DUPLICADO_MS = 30000;  // Un reintento del nodo dentro de este tiempo se ignora
const uint32_t REINTENTO_WIFI_MS = 10000;
const uint32_t REINTENTO_API_MS = 5000;

// ---------------------------------------------------------------------------
// Estado
// ---------------------------------------------------------------------------
IoTRadio radio(PIN_RADIO_CS, PIN_RADIO_DIO0, PIN_RADIO_RST);
IoTPantalla pantalla;

char cola[TAM_COLA][TAM_JSON];
uint8_t colaInicio = 0, colaCantidad = 0;

// Ultimo ID visto por origen, para descartar reintentos
uint8_t ultimoId[256];
uint32_t ultimoInstante[256];
bool hayUltimo[256];

uint32_t totalRecibidos = 0, totalEnviados = 0, totalPerdidos = 0;
uint32_t ultimoIntentoWifi = 0, ultimoIntentoApi = 0;
String ultimoNodo = "-";
int ultimoRssi = 0;

// ---------------------------------------------------------------------------
// Cola de envio
// ---------------------------------------------------------------------------

/** Agrega un JSON a la cola; si esta llena descarta el mas antiguo. */
void encolar(const char *json) {
  if (colaCantidad == TAM_COLA) {
    colaInicio = (colaInicio + 1) % TAM_COLA;
    colaCantidad--;
    totalPerdidos++;
  }
  uint8_t pos = (colaInicio + colaCantidad) % TAM_COLA;
  strlcpy(cola[pos], json, TAM_JSON);
  colaCantidad++;
}

/**
 * Envia a la API el JSON de `json`.
 * @return Codigo HTTP, o un valor negativo si no hubo respuesta.
 */
int publicar(const char *json) {
  HTTPClient http;
  int codigo;
  if (String(API_URL).startsWith("https")) {
    WiFiClientSecure cliente;
#ifdef API_CERT_RAIZ
    cliente.setCACert(API_CERT_RAIZ);
#else
    cliente.setInsecure();
#endif
    http.begin(cliente, API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_CLAVE);
    codigo = http.POST((uint8_t *)json, strlen(json));
  } else {
    WiFiClient cliente;
    http.begin(cliente, API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_CLAVE);
    codigo = http.POST((uint8_t *)json, strlen(json));
  }
  http.end();
  return codigo;
}

/**
 * Intenta enviar el primer elemento de la cola. Se quita de la cola si la API
 * lo acepto (2xx) o lo rechazo por ser invalido (4xx): reenviarlo no ayudaria.
 * Con errores de red o 5xx se conserva y se reintenta despues.
 */
void atenderCola() {
  if (colaCantidad == 0 || WiFi.status() != WL_CONNECTED) return;
  if (millis() - ultimoIntentoApi < REINTENTO_API_MS && ultimoIntentoApi != 0) return;
  int codigo = publicar(cola[colaInicio]);
  Serial.printf("POST -> %d\n", codigo);
  if ((codigo >= 200 && codigo < 300) || (codigo >= 400 && codigo < 500)) {
    if (codigo >= 400) Serial.printf("Rechazado por la API: %s\n", cola[colaInicio]);
    else totalEnviados++;
    colaInicio = (colaInicio + 1) % TAM_COLA;
    colaCantidad--;
    ultimoIntentoApi = 0;  // hay mas por enviar: sin espera
  } else {
    ultimoIntentoApi = millis();
  }
}

// ---------------------------------------------------------------------------
// WiFi
// ---------------------------------------------------------------------------

/** Reconecta sin bloquear el bucle principal. */
void mantenerWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  if (millis() - ultimoIntentoWifi < REINTENTO_WIFI_MS && ultimoIntentoWifi != 0) return;
  ultimoIntentoWifi = millis();
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);
}

// ---------------------------------------------------------------------------
// Pantalla
// ---------------------------------------------------------------------------

void actualizarPantalla() {
  pantalla.mostrar(String("GW 0xDD ") + (WiFi.status() == WL_CONNECTED ? "WiFi ok" : "sin WiFi"),
                   "Rx " + String(totalRecibidos) + " Tx " + String(totalEnviados),
                   "Cola " + String(colaCantidad) + " Perd " + String(totalPerdidos),
                   ultimoNodo + " " + String(ultimoRssi) + "dBm");
}

// ---------------------------------------------------------------------------
// Radio
// ---------------------------------------------------------------------------

/** Atiende un paquete LoRa recibido: ACK inmediato y encolado del JSON. */
void atenderPaquete(const IotTrama &t) {
  if (t.destino != IOT_DIR_GATEWAY || t.payload[0] != 'D') return;

  // El acuse sale primero para que el nodo no repita el envio
  radio.enviar(t.origen, IOT_DIR_GATEWAY, t.id, "A");

  uint32_t ahora = millis();
  bool duplicado = hayUltimo[t.origen] && ultimoId[t.origen] == t.id &&
                   ahora - ultimoInstante[t.origen] < VENTANA_DUPLICADO_MS;
  hayUltimo[t.origen] = true;
  ultimoId[t.origen] = t.id;
  ultimoInstante[t.origen] = ahora;
  if (duplicado) { Serial.println("Reintento duplicado ignorado"); return; }

  char json[TAM_JSON];
  size_t n = iotPayloadAJson(t.payload, t.origen, IOT_DIR_GATEWAY, radio.rssi(), radio.snr(), json, sizeof(json));
  if (n == 0) {
    Serial.printf("Payload invalido de 0x%02X: %s\n", t.origen, t.payload);
    return;
  }
  totalRecibidos++;
  ultimoNodo = String("0x") + String(t.origen, HEX);
  ultimoRssi = radio.rssi();
  Serial.println(json);
  encolar(json);
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  pantalla.iniciar();
  pantalla.mostrar("Gateway 0xDD", "Iniciando...", "", "");

  if (!iotPmuIniciar(PIN_SDA, PIN_SCL, false)) {
    pantalla.mostrar("Error PMU", "Revise la placa", "", "");
    while (true) delay(1000);
  }
  int estado = radio.iniciar(PIN_RADIO_SCK, PIN_RADIO_MISO, PIN_RADIO_MOSI, PIN_RADIO_CS);
  if (estado != RADIOLIB_ERR_NONE) {
    pantalla.mostrar("Error LoRa", "Codigo " + String(estado), "", "");
    while (true) delay(1000);
  }
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  mantenerWifi();
  actualizarPantalla();
}

void loop() {
  IotTrama t;
  if (radio.recibir(t)) {
    atenderPaquete(t);
    actualizarPantalla();
  }
  mantenerWifi();
  atenderCola();

  static uint32_t ultimaPantalla = 0;
  if (millis() - ultimaPantalla > 5000) {
    ultimaPantalla = millis();
    actualizarPantalla();
  }
  delay(2);
}
