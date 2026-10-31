/**
 * Nodo de SUELO movil - LilyGO T-Beam (direccion 0xCC, tipo SOIL, ambito MANGLAR)
 *
 * Descripcion:
 *   Nodo portatil que se lleva al manglar. Al pulsar el boton mide la
 *   humedad del suelo (sensor capacitivo v1.2) y su temperatura (DS18B20
 *   enterrado), obtiene la posicion GPS y envia todo al gateway por LoRa
 *   (915 MHz, RadioLib) con acuse de recibo. Los sensores solo se alimentan
 *   mientras se mide.
 *
 * Interfaz:
 *   Boton NAV (GPIO2)  : cambia la opcion del menu en pantalla.
 *   Boton OK  (GPIO38) : ejecuta la opcion (boton de usuario de la T-Beam).
 *   Menu: "Medir y enviar" | "Estado del nodo".
 *   Puerto serie (115200): calibracion de la humedad (ver menu impreso al arrancar).
 *
 * Conexiones (T-Beam V1.2):
 *   I2C SDA=21 SCL=22 : OLED SSD1306 (0x3C) y ADS1115 (0x48)
 *   ADS1115 A0 = salida analogica del sensor capacitivo
 *   DS18B20 (temperatura del suelo) -> GPIO4 (con 4.7 kOhm a 3.3 V)
 *   Riel de sensores conmutado -> GPIO25 (MOSFET que energiza solo los sensores
 *   analogicos, la sonda y el PMS5003; el ADS1115, el BME280, el SCD41 y la
 *   pantalla van a 3.3 V permanente)
 *   Radio y GPS: internos (SPI 5/19/27/18, DIO0=26, RST=23; GPS RX=34 TX=12)
 *
 * Calibracion: con el sensor al aire pulsar "s" por serie (0 %); con el sensor
 * sumergido en agua hasta la linea marcada pulsar "h" (100 %). Se guarda en
 * memoria no volatil.
 *
 * Dependencias: ver libraries/IoTMangrove/library.properties
 */

#define IOT_USA_PMU_TBEAM
#include <IoTBoton.h>
#include <IoTEnergia.h>
#include <IoTGps.h>
#include <IoTNodo.h>
#include <IoTPantalla.h>
#include <IoTProtocolo.h>
#include <IoTRadio.h>
#include <IoTSensorSuelo.h>
#include <IoTTemperaturaSonda.h>

// ---------------------------------------------------------------------------
// Identidad del nodo
// ---------------------------------------------------------------------------
const uint8_t DIRECCION = 0xCC;
const char *TIPO = "SOIL";
const char *AMBITO = "MANGLAR";

// ---------------------------------------------------------------------------
// Pines
// ---------------------------------------------------------------------------
const int PIN_SDA = 21, PIN_SCL = 22;
const int PIN_RADIO_CS = 18, PIN_RADIO_SCK = 5, PIN_RADIO_MOSI = 27, PIN_RADIO_MISO = 19;
const int PIN_RADIO_DIO0 = 26, PIN_RADIO_RST = 23;
const int PIN_GPS_RX = 34, PIN_GPS_TX = 12;
const int PIN_DS18B20 = 4, PIN_SENSORES_EN = 25;
const int PIN_BTN_NAV = 2, PIN_BTN_OK = 38;

// ---------------------------------------------------------------------------
// Ajustes
// ---------------------------------------------------------------------------
const uint32_t CALENTAMIENTO_MS = 2000;     // Estabilizacion de los sensores tras energizar
const uint32_t ESPERA_GPS_MS = 45000;       // Tiempo maximo para obtener posicion
const uint32_t APAGAR_PANTALLA_MS = 30000;  // Inactividad antes de apagar la pantalla

// ---------------------------------------------------------------------------
// Objetos
// ---------------------------------------------------------------------------
IoTRadio radio(PIN_RADIO_CS, PIN_RADIO_DIO0, PIN_RADIO_RST);
IoTPantalla pantalla;
IoTAnalogo adc;
IoTSensorSuelo sensorSuelo(&adc, 0);
IoTTemperaturaSonda sondaSuelo(PIN_DS18B20);
IoTAlimentacion riel(PIN_SENSORES_EN);
IoTGps gps;
IoTBoton botonNav(PIN_BTN_NAV);
IoTBoton botonOk(PIN_BTN_OK, false);  // GPIO38 no tiene pull-up interno (la placa trae uno externo)

int opcionMenu = 0;
const int NUM_OPCIONES = 2;
uint32_t ultimaActividad = 0;
bool pantallaEncendida = true;

// ---------------------------------------------------------------------------
// Pantalla y menu
// ---------------------------------------------------------------------------

void mostrarMenu() {
  pantalla.mostrar("Nodo SUELO 0xCC", opcionMenu == 0 ? "> Medir y enviar" : "  Medir y enviar",
                   opcionMenu == 1 ? "> Estado del nodo" : "  Estado del nodo",
                   "Bat:" + String(iotPmuBateria(), 0) + "%");
}

void despertarPantalla() {
  ultimaActividad = millis();
  if (!pantallaEncendida) { pantalla.encender(); pantallaEncendida = true; mostrarMenu(); }
}

// ---------------------------------------------------------------------------
// Medicion y envio
// ---------------------------------------------------------------------------

/**
 * Mide todos los sensores, agrega la posicion y envia el resultado al
 * gateway. Los sensores se energizan solo durante la medicion.
 */
void medirYEnviar() {
  pantalla.mostrar("Midiendo...", "Sensores en marcha", "Buscando GPS", "");
  riel.encender(CALENTAMIENTO_MS);
  iotPmuGps(true);
  gps.iniciar(PIN_GPS_RX, PIN_GPS_TX);

  double lat = 0, lon = 0;
  int sat = 0;
  bool hayGps = gps.esperarFix(ESPERA_GPS_MS, lat, lon, sat);

  float temperatura = sondaSuelo.leer();
  float humedad = sensorSuelo.leer();
  riel.apagar();
  iotPmuGps(false);

  IotPayload p;
  p.iniciar(TIPO, AMBITO);
  p.agregar("soilHumidity", humedad, 1);
  p.agregar("soilTemp", temperatura, 1);
  p.agregar("bat", iotPmuBateria(), 0);
  if (hayGps) p.agregarGps(lat, lon, sat);

  Serial.println(String("Payload: ") + p.texto());
  if (p.valores() == 0) {
    pantalla.mostrar("Sin sensores", "Revise conexiones", "", "");
    return;
  }
  pantalla.mostrar("Enviando...", "Hum " + String(humedad, 1) + " %",
                   hayGps ? "GPS ok (" + String(sat) + ")" : "Sin GPS", "");
  bool ok = iotEnviarConAck(radio, DIRECCION, p.texto());
  radio.dormir();
  pantalla.mostrar(ok ? "ENVIADO" : "SIN ACK", "Hum " + String(humedad, 1) + " %",
                   "Temp " + String(temperatura, 1) + " C",
                   hayGps ? "GPS " + String(sat) + " sat" : "Sin GPS");
  delay(4000);
}

/** Muestra el estado de los sensores y la bateria. */
void mostrarEstado() {
  riel.encender(CALENTAMIENTO_MS);
  bool hu = sensorSuelo.conectado();
  bool te = !isnan(sondaSuelo.leer());
  riel.apagar();
  pantalla.mostrar(String("Humedad:") + (hu ? "ok" : "--") + " Temp:" + (te ? "ok" : "--"),
                   "Seco " + String(sensorSuelo.vSeco(), 2) + "V",
                   "Humedo " + String(sensorSuelo.vHumedo(), 2) + "V",
                   "ADS:" + String(adc.presente() ? "ok" : "--") + " Bat:" + String(iotPmuBateria(), 0) + "%");
  delay(4000);
}

// ---------------------------------------------------------------------------
// Calibracion por puerto serie
// ---------------------------------------------------------------------------

void imprimirMenuSerie() {
  Serial.println("\n--- CALIBRACION HUMEDAD DE SUELO ---");
  Serial.println("s - capturar SECO (sensor al aire = 0 %)");
  Serial.println("h - capturar HUMEDO (sensor en agua = 100 %)");
  Serial.println("i - mostrar voltajes y lectura actual");
}

void atenderSerie() {
  if (!Serial.available()) return;
  char c = (char)Serial.read();
  while (Serial.available()) Serial.read();
  if (c != 's' && c != 'h' && c != 'i') { imprimirMenuSerie(); return; }
  riel.encender(CALENTAMIENTO_MS);
  if (c == 's') { sensorSuelo.calibrarSeco(); Serial.println("vSeco = " + String(sensorSuelo.vSeco(), 4) + " V (guardado)"); }
  if (c == 'h') { sensorSuelo.calibrarHumedo(); Serial.println("vHumedo = " + String(sensorSuelo.vHumedo(), 4) + " V (guardado)"); }
  if (c == 'i') {
    Serial.println("V suelo: " + String(sensorSuelo.voltaje(), 4) + "  Humedad: " + String(sensorSuelo.leer(), 1) + " %");
    Serial.println("vSeco=" + String(sensorSuelo.vSeco(), 4) + " vHumedo=" + String(sensorSuelo.vHumedo(), 4));
  }
  riel.apagar();
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  riel.iniciar();
  botonNav.iniciar();
  botonOk.iniciar();
  pantalla.iniciar();
  pantalla.mostrar("Nodo SUELO 0xCC", "Iniciando...", "", "");

  if (!iotPmuIniciar(PIN_SDA, PIN_SCL, false)) {
    pantalla.mostrar("Error PMU", "Revise la placa", "", "");
    while (true) delay(1000);
  }
  int estado = radio.iniciar(PIN_RADIO_SCK, PIN_RADIO_MISO, PIN_RADIO_MOSI, PIN_RADIO_CS);
  if (estado != RADIOLIB_ERR_NONE) {
    pantalla.mostrar("Error LoRa", "Codigo " + String(estado), "", "");
    while (true) delay(1000);
  }
  radio.dormir();

  riel.encender(CALENTAMIENTO_MS);
  adc.iniciar();
  sensorSuelo.iniciar();
  sondaSuelo.iniciar();
  riel.apagar();

  imprimirMenuSerie();
  mostrarMenu();
  ultimaActividad = millis();
}

void loop() {
  atenderSerie();

  if (botonNav.presionado()) {
    despertarPantalla();
    opcionMenu = (opcionMenu + 1) % NUM_OPCIONES;
    mostrarMenu();
  }
  if (botonOk.presionado()) {
    if (!pantallaEncendida) { despertarPantalla(); return; }
    despertarPantalla();
    if (opcionMenu == 0) medirYEnviar(); else mostrarEstado();
    mostrarMenu();
    ultimaActividad = millis();
  }
  if (pantallaEncendida && millis() - ultimaActividad > APAGAR_PANTALLA_MS) {
    pantalla.apagar();
    pantallaEncendida = false;
  }
  delay(10);
}
