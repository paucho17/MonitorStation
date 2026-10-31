// Pruebas en PC del protocolo y los calculos: g++ -std=c++17 -I../src probar_protocolo.cpp && ./a.out
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include "IoTCalculos.h"
#include "IoTProtocolo.h"

static int fallos = 0;
#define VERIFICAR(c) do { if (!(c)) { std::printf("FALLO linea %d: %s\n", __LINE__, #c); fallos++; } } while (0)
static bool cerca(float a, float b, float tol) { return std::fabs(a - b) <= tol; }

int main() {
  // Trama: ida y vuelta
  uint8_t buf[255];
  size_t n = iotTramaConstruir(0xDD, 0xAA, 7, "D;WATER;MANGLAR;ph=7.20", buf, sizeof(buf));
  VERIFICAR(n == 4 + 23);
  IotTrama t;
  VERIFICAR(iotTramaLeer(buf, n, &t));
  VERIFICAR(t.destino == 0xDD && t.origen == 0xAA && t.id == 7 && std::string(t.payload) == "D;WATER;MANGLAR;ph=7.20");
  VERIFICAR(!iotTramaLeer(buf, n - 1, &t));            // truncada
  VERIFICAR(!iotTramaLeer(buf, 3, &t));                // sin cabecera
  std::string largo(252, 'x');
  VERIFICAR(iotTramaConstruir(1, 2, 3, largo.c_str(), buf, sizeof(buf)) == 0);  // payload excesivo

  // Payload: omite NAN y agrega GPS
  IotPayload p;
  p.iniciar("WATER", "MANGLAR");
  VERIFICAR(p.agregar("ph", 7.2f, 2));
  VERIFICAR(!p.agregar("tds", NAN));
  VERIFICAR(p.agregar("turbidity", 21.456f, 1));
  VERIFICAR(p.agregarGps(10.98765, -74.80123, 8));
  VERIFICAR(std::string(p.texto()) == "D;WATER;MANGLAR;ph=7.20,turbidity=21.5;G=10.987650,-74.801230,8");
  VERIFICAR(p.valores() == 2);

  // JSON para la API
  char json[400];
  size_t j = iotPayloadAJson(p.texto(), 0xAA, 0xDD, -95, 7.5f, json, sizeof(json));
  VERIFICAR(j > 0 && j == std::strlen(json));
  std::string esperado = "{\"gateway\":\"0xDD\",\"nodeID\":\"0xAA\",\"type\":\"WATER\",\"scope\":\"MANGLAR\",\"rssi\":-95,\"snr\":7.5,"
                         "\"latitude\":10.987650,\"longitude\":-74.801230,\"satellites\":8,\"data\":{\"ph\":7.20,\"turbidity\":21.5}}";
  VERIFICAR(std::string(json) == esperado);
  if (std::string(json) != esperado) std::printf("obtenido: %s\n", json);

  // Sin GPS y con una sola variable
  j = iotPayloadAJson("D;SOIL;VIVERO;soilHumidity=41.5", 0xA1, 0xDD, -70, 8.0f, json, sizeof(json));
  VERIFICAR(j > 0 && std::strstr(json, "\"scope\":\"VIVERO\"") && !std::strstr(json, "latitude") && std::strstr(json, "\"data\":{\"soilHumidity\":41.5}}"));

  // Entradas invalidas: nunca deben producir JSON
  VERIFICAR(iotPayloadAJson("A", 1, 2, 0, 0, json, sizeof(json)) == 0);
  VERIFICAR(iotPayloadAJson("D;WATER;MANGLAR;ph=abc", 1, 2, 0, 0, json, sizeof(json)) == 0);
  VERIFICAR(iotPayloadAJson("D;WATER;MANGLAR;ph", 1, 2, 0, 0, json, sizeof(json)) == 0);
  VERIFICAR(iotPayloadAJson("D;wa\"ter;MANGLAR;ph=7", 1, 2, 0, 0, json, sizeof(json)) == 0);
  VERIFICAR(iotPayloadAJson("D;WATER;MANGLAR;p\"h=7", 1, 2, 0, 0, json, sizeof(json)) == 0);
  VERIFICAR(iotPayloadAJson("D;WATER;MANGLAR;ph=7.2", 1, 2, 0, 0, json, 20) == 0);   // buffer corto
  VERIFICAR(iotPayloadAJson("D;WATER", 1, 2, 0, 0, json, sizeof(json)) == 0);

  // Desborde del payload
  IotPayload q;
  q.iniciar("AMB", "VIVERO");
  for (int i = 0; i < 100; i++) q.agregar("temperature", 25.0f);
  VERIFICAR(q.desbordado() && std::strlen(q.texto()) <= IOT_PAYLOAD_MAX);

  // Calculos
  VERIFICAR(cerca(iotPhDesdeVoltaje(1.50f, 1.50f, 1.80f), 7.0f, 0.001f));
  VERIFICAR(cerca(iotPhDesdeVoltaje(1.80f, 1.50f, 1.80f), 4.01f, 0.001f));
  VERIFICAR(cerca(iotPhDesdeVoltaje(1.35f, 1.50f, 1.80f), 8.495f, 0.01f));
  VERIFICAR(std::isnan(iotPhDesdeVoltaje(1.0f, 1.5f, 1.5f)));
  VERIFICAR(iotNtuDesdeVoltaje(4.2f) < 5.0f);                    // agua clara
  VERIFICAR(iotNtuDesdeVoltaje(2.0f) == 3000.0f);                // muy turbia
  VERIFICAR(cerca(iotNtuDesdeVoltaje(4.2f, 1.0f), iotNtuDesdeVoltaje(2.8f, 1.5f), 0.01f));   // divisor 2:3
  VERIFICAR(cerca(iotTdsDesdeVoltaje(1.0f, 25.0f), (133.42f - 255.86f + 857.39f) * 0.5f, 0.01f));
  VERIFICAR(iotTdsDesdeVoltaje(1.0f, 35.0f) < iotTdsDesdeVoltaje(1.0f, 25.0f));  // el mismo voltaje a mas calor es menos TDS
  VERIFICAR(cerca(iotHumedadDesdeVoltaje(2.6f, 2.6f, 1.2f), 0.0f, 0.001f));
  VERIFICAR(cerca(iotHumedadDesdeVoltaje(1.2f, 2.6f, 1.2f), 100.0f, 0.001f));
  VERIFICAR(cerca(iotHumedadDesdeVoltaje(1.9f, 2.6f, 1.2f), 50.0f, 0.001f));
  VERIFICAR(iotHumedadDesdeVoltaje(0.5f, 2.6f, 1.2f) == 100.0f);  // limitada
  VERIFICAR(std::isnan(iotHumedadDesdeVoltaje(1.0f, 2.0f, 2.0f)));

  // PMS5003
  unsigned char tp[32] = {0x42, 0x4D, 0x00, 0x1C};
  tp[10] = 0; tp[11] = 8; tp[12] = 0; tp[13] = 15; tp[14] = 0; tp[15] = 22;
  unsigned int s = 0; for (int i = 0; i < 30; i++) s += tp[i];
  tp[30] = (s >> 8) & 0xFF; tp[31] = s & 0xFF;
  float a, b, c;
  VERIFICAR(iotPmsAnalizar(tp, &a, &b, &c) && a == 8 && b == 15 && c == 22);
  tp[31] ^= 1;
  VERIFICAR(!iotPmsAnalizar(tp, &a, &b, &c));

  std::printf(fallos ? "%d prueba(s) fallida(s)\n" : "Todas las pruebas pasaron\n", fallos);
  return fallos ? 1 : 0;
}
