/**
 * Nodo de AIRE del vivero - LoRa32 (direccion 0xA2, tipo AMB, ambito VIVERO)
 *
 * Descripcion:
 *   Nodo fijo del vivero. Cada INTERVALO_S segundos despierta, mide
 *   temperatura, humedad, presion, CO2 y particulas PM y lo envia al gateway por LoRa
 *   (915 MHz, RadioLib) con acuse de recibo; despues entra en sueno profundo.
 *   No usa GPS porque su posicion es fija. Si el gateway no confirma, reintenta
 *   a los REINTENTO_S segundos.
 *
 * Calibracion:
 *   Tras un arranque por energia (no tras el sueno), el nodo espera 10 s una
 *   tecla por el puerto serie (115200). Con una tecla entra al menu de
 *   calibracion hasta recibir 'q'.
 *   Los sensores de aire vienen calibrados: el menu solo ofrece diagnostico (i).
 *
 * Conexiones (LoRa32):
 *   I2C SDA=21 SCL=22 : OLED SSD1306 (0x3C), BME280 (0x76) y SCD41 (0x62)
 *   PMS5003: TX del sensor -> GPIO34 (RX2), RX del sensor -> GPIO14, SET -> GPIO25 (alimentar a 5 V)
 *   Radio: interno (SPI 5/19/27/18, DIO0=26, RST=23)
 *
 * Dependencias: ver libraries/IoTMangrove/library.properties
 */

#include <IoTSensoresAire.h>
#include <IoTNodo.h>
#include <IoTPantalla.h>
#include <IoTProtocolo.h>
#include <IoTRadio.h>
#include <esp_sleep.h>

// ---------------------------------------------------------------------------
// Identidad del nodo
// ---------------------------------------------------------------------------
const uint8_t DIRECCION = 0xA2;
const char *TIPO = "AMB";
const char *AMBITO = "VIVERO";

// ---------------------------------------------------------------------------
// Pines
// ---------------------------------------------------------------------------
const int PIN_SDA = 21, PIN_SCL = 22;
const int PIN_RADIO_CS = 18, PIN_RADIO_SCK = 5, PIN_RADIO_MOSI = 27, PIN_RADIO_MISO = 19;
const int PIN_RADIO_DIO0 = 26, PIN_RADIO_RST = 23;
const int PIN_PMS_RX = 34, PIN_PMS_TX = 14, PIN_PMS_SET = 25;

// ---------------------------------------------------------------------------
// Ajustes
// ---------------------------------------------------------------------------
const uint32_t INTERVALO_S = 300;   // Periodo entre mediciones
const uint32_t REINTENTO_S = 60;    // Espera tras un envio sin acuse
const uint32_t VENTILADOR_PMS_MS = 30000;  // Estabilizacion del PMS5003

// ---------------------------------------------------------------------------
// Objetos
// ---------------------------------------------------------------------------
IoTRadio radio(PIN_RADIO_CS, PIN_RADIO_DIO0, PIN_RADIO_RST);
IoTPantalla pantalla;
IoTBme280 bme;
IoTScd41 scd;
IoTPms5003 pms(&Serial2, PIN_PMS_SET);

// ---------------------------------------------------------------------------
// Medicion y envio
// ---------------------------------------------------------------------------

/**
 * Mide los sensores y envia el resultado al gateway.
 * @return true si el gateway confirmo la recepcion.
 */
bool medirYEnviar() {
  pantalla.mostrar("Midiendo...", "Ventilador PMS 30 s", "", "");
  pms.despertar();
  delay(VENTILADOR_PMS_MS);
  float temperatura = bme.temperatura();
  float humedad = bme.humedad();
  float presion = bme.presion();
  float co2 = scd.co2();
  float pm1 = NAN, pm25 = NAN, pm10 = NAN;
  pms.leer(&pm1, &pm25, &pm10);
  pms.reposo();

  IotPayload p;
  p.iniciar(TIPO, AMBITO);
  p.agregar("temperature", temperatura, 1);
  p.agregar("humidity", humedad, 1);
  p.agregar("pressure", presion, 1);
  p.agregar("co2", co2, 0);
  p.agregar("pm1", pm1, 0);
  p.agregar("pm25", pm25, 0);
  p.agregar("pm10", pm10, 0);

  Serial.println(String("Payload: ") + p.texto());
  if (p.valores() == 0) {
    pantalla.mostrar("Nodo AIRE " + String(DIRECCION, HEX), "Sin sensores", "Revise conexiones", "");
    return false;
  }
  pantalla.mostrar("Enviando...", "T " + String(temperatura, 1) + " H " + String(humedad, 0), "CO2 " + String(co2, 0) + " PM2.5 " + String(pm25, 0), "");
  bool ok = iotEnviarConAck(radio, DIRECCION, p.texto());
  radio.dormir();
  pantalla.mostrar(ok ? "ENVIADO" : "SIN ACK", "T " + String(temperatura, 1) + " H " + String(humedad, 0), "CO2 " + String(co2, 0) + " PM2.5 " + String(pm25, 0), "");
  return ok;
}

// ---------------------------------------------------------------------------
// Calibracion por puerto serie (solo tras un arranque por energia)
// ---------------------------------------------------------------------------

void imprimirMenuSerie() {
  Serial.println("\nNodo AIRE sin calibracion. 'i' = estado de sensores, 'q' = salir.");
}

void atenderOpcion(char c) {
  if (c == 'i') Serial.println(String("BME280: ") + (bme.presente() ? "ok" : "no detectado") +
                               "  SCD41: " + (scd.presente() ? "ok" : "no detectado"));
  else imprimirMenuSerie();
}

/** Espera 10 s una tecla por serie; si llega, atiende el menu hasta 'q'. */
void ventanaCalibracion() {
  pantalla.mostrar("Nodo AIRE " + String(DIRECCION, HEX), "Calibrar?", "Envie una tecla", "por serie (10 s)");
  Serial.println("\nPulse una tecla en 10 s para calibrar...");
  uint32_t inicio = millis();
  while (millis() - inicio < 10000 && !Serial.available()) delay(50);
  if (!Serial.available()) return;
  while (Serial.available()) Serial.read();
  imprimirMenuSerie();
  while (true) {
    if (!Serial.available()) { delay(50); continue; }
    char c = (char)Serial.read();
    while (Serial.available()) Serial.read();
    if (c == 'q') { Serial.println("Saliendo de la calibracion"); return; }
    atenderOpcion(c);
  }
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

/** Entra en sueno profundo; al despertar el nodo reinicia y vuelve a medir. */
void dormir(uint32_t segundos) {
  pantalla.apagar();
  radio.dormir();
  esp_sleep_enable_timer_wakeup((uint64_t)segundos * 1000000ULL);
  esp_deep_sleep_start();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  pantalla.iniciar();
  pantalla.mostrar("Nodo AIRE " + String(DIRECCION, HEX), "Iniciando...", "", "");
  bme.iniciar();
  scd.iniciar();
  pms.iniciar(PIN_PMS_RX, PIN_PMS_TX);

  int estado = radio.iniciar(PIN_RADIO_SCK, PIN_RADIO_MISO, PIN_RADIO_MOSI, PIN_RADIO_CS);
  if (estado != RADIOLIB_ERR_NONE) {
    pantalla.mostrar("Error LoRa", "Codigo " + String(estado), "", "");
    delay(5000);
    dormir(REINTENTO_S);
  }

  // La calibracion solo se ofrece tras un arranque por energia, no al despertar del sueno
  if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_UNDEFINED) ventanaCalibracion();

  bool ok = medirYEnviar();
  delay(3000);
  dormir(ok ? INTERVALO_S : REINTENTO_S);
}

void loop() {
  // No se alcanza: el nodo duerme al final de setup()
}
