/**
 * Nodo de AIRE movil - LilyGO T-Beam (direccion 0xBB, tipo AMB, ambito MANGLAR)
 *
 * Descripcion:
 *   Nodo portatil que se lleva al manglar. Al pulsar el boton mide
 *   temperatura, humedad y presion (BME280), CO2 (SCD41) y material
 *   particulado PM1.0/PM2.5/PM10 (PMS5003), obtiene la posicion GPS y envia
 *   todo al gateway por LoRa (915 MHz, RadioLib) con acuse de recibo. Los
 *   sensores solo se alimentan mientras se mide; el PMS5003 necesita unos
 *   30 s de ventilador antes de medir, tiempo que se aprovecha para buscar
 *   satelites.
 *
 * Interfaz:
 *   Boton NAV (GPIO2)  : cambia la opcion del menu en pantalla.
 *   Boton OK  (GPIO38) : ejecuta la opcion (boton de usuario de la T-Beam).
 *   Menu: "Medir y enviar" | "Estado del nodo".
 *   Puerto serie (115200): informacion de diagnostico (no requiere calibracion).
 *
 * Conexiones (T-Beam V1.2):
 *   I2C SDA=21 SCL=22 : OLED SSD1306 (0x3C), BME280 (0x76) y SCD41 (0x62)
 *   PMS5003: TX del sensor -> GPIO14 (RX2), RX del sensor -> GPIO15, SET -> GPIO32
 *            (alimentar a 5 V desde el riel conmutado)
 *   Riel de sensores conmutado -> GPIO25 (MOSFET que energiza solo los sensores
 *   analogicos, la sonda y el PMS5003; el ADS1115, el BME280, el SCD41 y la
 *   pantalla van a 3.3 V permanente)
 *   Radio y GPS: internos (SPI 5/19/27/18, DIO0=26, RST=23; GPS RX=34 TX=12)
 *
 * Los sensores de aire vienen calibrados de fabrica.
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
#include <IoTSensoresAire.h>

// ---------------------------------------------------------------------------
// Identidad del nodo
// ---------------------------------------------------------------------------
const uint8_t DIRECCION = 0xBB;
const char *TIPO = "AMB";
const char *AMBITO = "MANGLAR";

// ---------------------------------------------------------------------------
// Pines
// ---------------------------------------------------------------------------
const int PIN_SDA = 21, PIN_SCL = 22;
const int PIN_RADIO_CS = 18, PIN_RADIO_SCK = 5, PIN_RADIO_MOSI = 27, PIN_RADIO_MISO = 19;
const int PIN_RADIO_DIO0 = 26, PIN_RADIO_RST = 23;
const int PIN_GPS_RX = 34, PIN_GPS_TX = 12;
const int PIN_PMS_RX = 14, PIN_PMS_TX = 15, PIN_PMS_SET = 32, PIN_SENSORES_EN = 25;
const int PIN_BTN_NAV = 2, PIN_BTN_OK = 38;

// ---------------------------------------------------------------------------
// Ajustes
// ---------------------------------------------------------------------------
const uint32_t CALENTAMIENTO_MS = 2000;     // Estabilizacion de los sensores tras energizar
const uint32_t VENTILADOR_PMS_MS = 30000;   // Estabilizacion del PMS5003
const uint32_t ESPERA_GPS_MS = 45000;       // Tiempo maximo para obtener posicion
const uint32_t APAGAR_PANTALLA_MS = 30000;  // Inactividad antes de apagar la pantalla

// ---------------------------------------------------------------------------
// Objetos
// ---------------------------------------------------------------------------
IoTRadio radio(PIN_RADIO_CS, PIN_RADIO_DIO0, PIN_RADIO_RST);
IoTPantalla pantalla;
IoTBme280 bme;
IoTScd41 scd;
IoTPms5003 pms(&Serial2, PIN_PMS_SET);
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
  pantalla.mostrar("Nodo AIRE 0xBB", opcionMenu == 0 ? "> Medir y enviar" : "  Medir y enviar",
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
  pantalla.mostrar("Midiendo...", "Ventilador PMS 30 s", "Buscando GPS", "");
  riel.encender(CALENTAMIENTO_MS);
  pms.despertar();
  iotPmuGps(true);
  gps.iniciar(PIN_GPS_RX, PIN_GPS_TX);

  // El PMS5003 necesita ~30 s con el ventilador en marcha: se aprovechan para el GPS
  uint32_t inicio = millis();
  double lat = 0, lon = 0;
  int sat = 0;
  bool hayGps = gps.esperarFix(ESPERA_GPS_MS, lat, lon, sat);
  while (millis() - inicio < VENTILADOR_PMS_MS) delay(100);

  float temperatura = bme.temperatura();
  float humedad = bme.humedad();
  float presion = bme.presion();
  float co2 = scd.co2();
  float pm1 = NAN, pm25 = NAN, pm10 = NAN;
  pms.leer(&pm1, &pm25, &pm10);
  pms.reposo();
  riel.apagar();
  iotPmuGps(false);

  IotPayload p;
  p.iniciar(TIPO, AMBITO);
  p.agregar("temperature", temperatura, 1);
  p.agregar("humidity", humedad, 1);
  p.agregar("pressure", presion, 1);
  p.agregar("co2", co2, 0);
  p.agregar("pm1", pm1, 0);
  p.agregar("pm25", pm25, 0);
  p.agregar("pm10", pm10, 0);
  p.agregar("bat", iotPmuBateria(), 0);
  if (hayGps) p.agregarGps(lat, lon, sat);

  Serial.println(String("Payload: ") + p.texto());
  if (p.valores() == 0) {
    pantalla.mostrar("Sin sensores", "Revise conexiones", "", "");
    return;
  }
  pantalla.mostrar("Enviando...", "T " + String(temperatura, 1) + " H " + String(humedad, 0),
                   hayGps ? "GPS ok (" + String(sat) + ")" : "Sin GPS", "");
  bool ok = iotEnviarConAck(radio, DIRECCION, p.texto());
  radio.dormir();
  pantalla.mostrar(ok ? "ENVIADO" : "SIN ACK", "T " + String(temperatura, 1) + " H " + String(humedad, 0),
                   "CO2 " + String(co2, 0) + " PM2.5 " + String(pm25, 0),
                   hayGps ? "GPS " + String(sat) + " sat" : "Sin GPS");
  delay(4000);
}

/** Muestra el estado de los sensores y la bateria. */
void mostrarEstado() {
  pantalla.mostrar(String("BME:") + (bme.presente() ? "ok " : "-- ") + "SCD:" + (scd.presente() ? "ok" : "--"),
                   "PMS5003: se prueba al medir",
                   "Bat:" + String(iotPmuBateria(), 0) + "%", "");
  delay(4000);
}

// ---------------------------------------------------------------------------
// Calibracion por puerto serie
// ---------------------------------------------------------------------------

void imprimirMenuSerie() {
  Serial.println("\nNodo AIRE: sin calibracion. Pulse 'i' para ver el estado.");
}

void atenderSerie() {
  if (!Serial.available()) return;
  char c = (char)Serial.read();
  while (Serial.available()) Serial.read();
  if (c == 'i') Serial.println(String("BME280: ") + (bme.presente() ? "ok" : "no detectado") +
                               "  SCD41: " + (scd.presente() ? "ok" : "no detectado"));
  else imprimirMenuSerie();
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
  pantalla.mostrar("Nodo AIRE 0xBB", "Iniciando...", "", "");

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
  bme.iniciar();
  scd.iniciar();
  pms.iniciar(PIN_PMS_RX, PIN_PMS_TX);
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
