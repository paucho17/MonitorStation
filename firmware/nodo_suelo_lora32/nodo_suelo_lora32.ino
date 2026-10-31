/**
 * Nodo de SUELO del vivero - LoRa32 (direccion 0xA1, tipo SOIL, ambito VIVERO)
 *
 * Descripcion:
 *   Nodo fijo del vivero. Cada INTERVALO_S segundos despierta, mide
 *   la humedad y la temperatura del suelo y lo envia al gateway por LoRa
 *   (915 MHz, RadioLib) con acuse de recibo; despues entra en sueno profundo.
 *   No usa GPS porque su posicion es fija. Si el gateway no confirma, reintenta
 *   a los REINTENTO_S segundos.
 *
 * Calibracion:
 *   Tras un arranque por energia (no tras el sueno), el nodo espera 10 s una
 *   tecla por el puerto serie (115200). Con una tecla entra al menu de
 *   calibracion hasta recibir 'q'.
 *   Opciones: s = sensor al aire (0 %), h = sensor en agua (100 %), i = informacion.
 *
 * Conexiones (LoRa32):
 *   I2C SDA=21 SCL=22 : OLED SSD1306 (0x3C) y ADS1115 (0x48)
 *   ADS1115 A0 = salida analogica del sensor capacitivo v1.2
 *   DS18B20 (temperatura del suelo) -> GPIO2 (con 4.7 kOhm a 3.3 V)
 *   Radio: interno (SPI 5/19/27/18, DIO0=26, RST=23)
 *
 * Dependencias: ver libraries/IoTMangrove/library.properties
 */

#include <IoTSensorSuelo.h>
#include <IoTTemperaturaSonda.h>
#include <IoTNodo.h>
#include <IoTPantalla.h>
#include <IoTProtocolo.h>
#include <IoTRadio.h>
#include <esp_sleep.h>

// ---------------------------------------------------------------------------
// Identidad del nodo
// ---------------------------------------------------------------------------
const uint8_t DIRECCION = 0xA1;
const char *TIPO = "SOIL";
const char *AMBITO = "VIVERO";

// ---------------------------------------------------------------------------
// Pines
// ---------------------------------------------------------------------------
const int PIN_SDA = 21, PIN_SCL = 22;
const int PIN_RADIO_CS = 18, PIN_RADIO_SCK = 5, PIN_RADIO_MOSI = 27, PIN_RADIO_MISO = 19;
const int PIN_RADIO_DIO0 = 26, PIN_RADIO_RST = 23;
const int PIN_DS18B20 = 2;

// ---------------------------------------------------------------------------
// Ajustes
// ---------------------------------------------------------------------------
const uint32_t INTERVALO_S = 300;   // Periodo entre mediciones
const uint32_t REINTENTO_S = 60;    // Espera tras un envio sin acuse
const uint32_t CALENTAMIENTO_MS = 500;   // Estabilizacion del sensor

// ---------------------------------------------------------------------------
// Objetos
// ---------------------------------------------------------------------------
IoTRadio radio(PIN_RADIO_CS, PIN_RADIO_DIO0, PIN_RADIO_RST);
IoTPantalla pantalla;
IoTAnalogo adc;
IoTSensorSuelo sensorSuelo(&adc, 0);
IoTTemperaturaSonda sondaSuelo(PIN_DS18B20);

// ---------------------------------------------------------------------------
// Medicion y envio
// ---------------------------------------------------------------------------

/**
 * Mide los sensores y envia el resultado al gateway.
 * @return true si el gateway confirmo la recepcion.
 */
bool medirYEnviar() {
  delay(CALENTAMIENTO_MS);
  float humedad = sensorSuelo.leer();
  float temperatura = sondaSuelo.leer();

  IotPayload p;
  p.iniciar(TIPO, AMBITO);
  p.agregar("soilHumidity", humedad, 1);
  p.agregar("soilTemp", temperatura, 1);

  Serial.println(String("Payload: ") + p.texto());
  if (p.valores() == 0) {
    pantalla.mostrar("Nodo SUELO " + String(DIRECCION, HEX), "Sin sensores", "Revise conexiones", "");
    return false;
  }
  pantalla.mostrar("Enviando...", "Hum " + String(humedad, 1) + " %", "Temp " + String(temperatura, 1) + " C", "");
  bool ok = iotEnviarConAck(radio, DIRECCION, p.texto());
  radio.dormir();
  pantalla.mostrar(ok ? "ENVIADO" : "SIN ACK", "Hum " + String(humedad, 1) + " %", "Temp " + String(temperatura, 1) + " C", "");
  return ok;
}

// ---------------------------------------------------------------------------
// Calibracion por puerto serie (solo tras un arranque por energia)
// ---------------------------------------------------------------------------

void imprimirMenuSerie() {
  Serial.println("\n--- CALIBRACION HUMEDAD DE SUELO ---");
  Serial.println("s - capturar SECO (sensor al aire = 0 %)");
  Serial.println("h - capturar HUMEDO (sensor en agua = 100 %)");
  Serial.println("i - mostrar voltajes y lectura actual");
  Serial.println("q - salir");
}

void atenderOpcion(char c) {
  if (c == 's') { sensorSuelo.calibrarSeco(); Serial.println("vSeco = " + String(sensorSuelo.vSeco(), 4) + " V (guardado)"); }
  else if (c == 'h') { sensorSuelo.calibrarHumedo(); Serial.println("vHumedo = " + String(sensorSuelo.vHumedo(), 4) + " V (guardado)"); }
  else if (c == 'i') {
    Serial.println("V suelo: " + String(sensorSuelo.voltaje(), 4) + "  Humedad: " + String(sensorSuelo.leer(), 1) + " %");
    Serial.println("vSeco=" + String(sensorSuelo.vSeco(), 4) + " vHumedo=" + String(sensorSuelo.vHumedo(), 4));
  } else imprimirMenuSerie();
}

/** Espera 10 s una tecla por serie; si llega, atiende el menu hasta 'q'. */
void ventanaCalibracion() {
  pantalla.mostrar("Nodo SUELO " + String(DIRECCION, HEX), "Calibrar?", "Envie una tecla", "por serie (10 s)");
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
  pantalla.mostrar("Nodo SUELO " + String(DIRECCION, HEX), "Iniciando...", "", "");
  adc.iniciar();
  sensorSuelo.iniciar();
  sondaSuelo.iniciar();

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
