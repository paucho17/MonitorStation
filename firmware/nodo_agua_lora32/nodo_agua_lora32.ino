/**
 * Nodo de AGUA del vivero - LoRa32 (direccion 0xA3, tipo WATER, ambito VIVERO)
 *
 * Descripcion:
 *   Nodo fijo del vivero. Cada INTERVALO_S segundos despierta, mide
 *   pH, turbidez, TDS, temperatura del agua y nivel y lo envia al gateway por LoRa
 *   (915 MHz, RadioLib) con acuse de recibo; despues entra en sueno profundo.
 *   No usa GPS porque su posicion es fija. Si el gateway no confirma, reintenta
 *   a los REINTENTO_S segundos.
 *
 * Calibracion:
 *   Tras un arranque por energia (no tras el sueno), el nodo espera 10 s una
 *   tecla por el puerto serie (115200). Con una tecla entra al menu de
 *   calibracion hasta recibir 'q'.
 *   Opciones: 7 = buffer pH 7.00, 4 = buffer pH 4.01, i = informacion.
 *
 * Conexiones (LoRa32):
 *   I2C SDA=21 SCL=22 : OLED SSD1306 (0x3C) y ADS1115 (0x48)
 *   ADS1115 A0 = pH (SEN0161), A1 = turbidez (SEN0189 con divisor 10k/20k), A2 = TDS (SEN0244)
 *   DS18B20 (temperatura del agua) -> GPIO2 (con 4.7 kOhm a 3.3 V)
 *   Flotador de nivel -> GPIO13 y GND
 *   Radio: interno (SPI 5/19/27/18, DIO0=26, RST=23)
 *
 * Dependencias: ver libraries/IoTMangrove/library.properties
 */

#include <IoTSensoresAgua.h>
#include <IoTTemperaturaSonda.h>
#include <IoTNodo.h>
#include <IoTPantalla.h>
#include <IoTProtocolo.h>
#include <IoTRadio.h>
#include <esp_sleep.h>

// ---------------------------------------------------------------------------
// Identidad del nodo
// ---------------------------------------------------------------------------
const uint8_t DIRECCION = 0xA3;
const char *TIPO = "WATER";
const char *AMBITO = "VIVERO";

// ---------------------------------------------------------------------------
// Pines
// ---------------------------------------------------------------------------
const int PIN_SDA = 21, PIN_SCL = 22;
const int PIN_RADIO_CS = 18, PIN_RADIO_SCK = 5, PIN_RADIO_MOSI = 27, PIN_RADIO_MISO = 19;
const int PIN_RADIO_DIO0 = 26, PIN_RADIO_RST = 23;
const int PIN_DS18B20 = 2, PIN_FLOTADOR = 13;

// ---------------------------------------------------------------------------
// Ajustes
// ---------------------------------------------------------------------------
const uint32_t INTERVALO_S = 300;   // Periodo entre mediciones
const uint32_t REINTENTO_S = 60;    // Espera tras un envio sin acuse
const uint32_t CALENTAMIENTO_MS = 2000;  // Estabilizacion de los sensores

// ---------------------------------------------------------------------------
// Objetos
// ---------------------------------------------------------------------------
IoTRadio radio(PIN_RADIO_CS, PIN_RADIO_DIO0, PIN_RADIO_RST);
IoTPantalla pantalla;
IoTAnalogo adc;
IoTSensorPh sensorPh(&adc, 0);
IoTSensorTurbidez sensorTurbidez(&adc, 1, 1.5f);
IoTSensorTds sensorTds(&adc, 2);
IoTTemperaturaSonda sondaAgua(PIN_DS18B20);
IoTFlotador flotador(PIN_FLOTADOR);

// ---------------------------------------------------------------------------
// Medicion y envio
// ---------------------------------------------------------------------------

/**
 * Mide los sensores y envia el resultado al gateway.
 * @return true si el gateway confirmo la recepcion.
 */
bool medirYEnviar() {
  delay(CALENTAMIENTO_MS);
  float temperatura = sondaAgua.leer();
  float ph = sensorPh.leer();
  float ntu = sensorTurbidez.leer();
  float tds = sensorTds.leer(temperatura);
  float nivel = flotador.leer();

  IotPayload p;
  p.iniciar(TIPO, AMBITO);
  p.agregar("ph", ph, 2);
  p.agregar("turbidity", ntu, 1);
  p.agregar("tds", tds, 0);
  p.agregar("waterTemp", temperatura, 1);
  p.agregar("waterLevel", nivel, 0);

  Serial.println(String("Payload: ") + p.texto());
  if (p.valores() == 0) {
    pantalla.mostrar("Nodo AGUA " + String(DIRECCION, HEX), "Sin sensores", "Revise conexiones", "");
    return false;
  }
  pantalla.mostrar("Enviando...", "pH " + String(ph, 2) + " NTU " + String(ntu, 0), "TDS " + String(tds, 0) + " T " + String(temperatura, 1), "");
  bool ok = iotEnviarConAck(radio, DIRECCION, p.texto());
  radio.dormir();
  pantalla.mostrar(ok ? "ENVIADO" : "SIN ACK", "pH " + String(ph, 2) + " NTU " + String(ntu, 0), "TDS " + String(tds, 0) + " T " + String(temperatura, 1), "");
  return ok;
}

// ---------------------------------------------------------------------------
// Calibracion por puerto serie (solo tras un arranque por energia)
// ---------------------------------------------------------------------------

void imprimirMenuSerie() {
  Serial.println("\n--- CALIBRACION pH ---");
  Serial.println("7 - capturar buffer pH 7.00");
  Serial.println("4 - capturar buffer pH 4.01");
  Serial.println("i - mostrar voltajes y lectura actual");
  Serial.println("q - salir");
}

void atenderOpcion(char c) {
  if (c == '7') { sensorPh.calibrarPh7(); Serial.println("v7 = " + String(sensorPh.v7(), 4) + " V (guardado)"); }
  else if (c == '4') { sensorPh.calibrarPh4(); Serial.println("vAcido = " + String(sensorPh.vAcido(), 4) + " V (guardado)"); }
  else if (c == 'i') {
    Serial.println("V pH: " + String(sensorPh.voltaje(), 4) + "  pH: " + String(sensorPh.leer(), 2));
    Serial.println("v7=" + String(sensorPh.v7(), 4) + " vAcido=" + String(sensorPh.vAcido(), 4));
  } else imprimirMenuSerie();
}

/** Espera 10 s una tecla por serie; si llega, atiende el menu hasta 'q'. */
void ventanaCalibracion() {
  pantalla.mostrar("Nodo AGUA " + String(DIRECCION, HEX), "Calibrar?", "Envie una tecla", "por serie (10 s)");
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
  pantalla.mostrar("Nodo AGUA " + String(DIRECCION, HEX), "Iniciando...", "", "");
  adc.iniciar();
  sensorPh.iniciar();
  sondaAgua.iniciar();
  flotador.iniciar();

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
