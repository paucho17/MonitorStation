# Firmware de la red LoRa

Carpeta `firmware/`. Todo funciona a 915 MHz con RadioLib (6.0 o superior).

## Estructura
| Carpeta | Contenido |
|---|---|
| `libraries/IoTMangrove` | Biblioteca común: protocolo, radio, envío con ACK, pantalla, GPS, energía y sensores |
| `gateway_tbeam` | Gateway T-Beam: recibe por LoRa, confirma (ACK) y publica en la API por WiFi |
| `nodo_agua_tbeam`, `nodo_suelo_tbeam`, `nodo_aire_tbeam` | Nodos móviles del manglar (0xAA, 0xCC, 0xBB), con GPS, pantalla y botones |
| `nodo_agua_lora32`, `nodo_suelo_lora32`, `nodo_aire_lora32` | Nodos fijos del vivero (0xA3, 0xA1, 0xA2), sin GPS, con sueño profundo |
| `tests` | Pruebas en PC de protocolo y cálculos, y verificación de sintaxis de los sketches |

## Instalación
1. Copiar `firmware/libraries/IoTMangrove` a la carpeta `Arduino/libraries`.
2. Instalar desde el gestor de bibliotecas: RadioLib, Adafruit GFX Library, Adafruit SSD1306, Adafruit ADS1X15, Adafruit BME280 Library, Adafruit Unified Sensor, OneWire, DallasTemperature, Sensirion I2C SCD4x, TinyGPSPlus y XPowersLib.
3. Gateway: copiar `gateway_tbeam/secrets.h.example` como `secrets.h` y completar WiFi y clave de API (`GATEWAY_API_KEY`).
4. Placa en el IDE: "T-Beam" (ESP32) para los T-Beam y "TTGO LoRa32-OLED" para los LoRa32.
5. T-Beam V1.1 con AXP192: agregar `#define IOT_TBEAM_AXP192` antes de incluir `IoTEnergia.h` en cada sketch. La V1.2 usa AXP2101 (por defecto).

## Protocolo
Trama: `[DESTINO][ORIGEN][ID][LONGITUD][PAYLOAD ASCII]` (igual que los nodos anteriores).

Payload de datos, enviado por el nodo cuando tiene datos:
```
D;<TIPO>;<AMBITO>;<clave>=<valor>,<clave>=<valor>[;G=<lat>,<lon>,<satelites>]
D;WATER;MANGLAR;ph=7.20,turbidity=21.5,tds=350;G=10.987650,-74.801230,8
```
`TIPO` es WATER, AMB o SOIL; `AMBITO` es MANGLAR, VIVERO o RIEGO. Las claves son los alias de la API (`variable_alias`). El gateway no conoce las variables: convierte el payload a JSON y lo publica, de modo que un sensor nuevo en un nodo no obliga a cambiar el gateway.

El gateway responde `A` con el mismo ID. Si el nodo no recibe el acuse reintenta (3 veces, con espera aleatoria creciente). Un reintento del mismo ID en 30 s se confirma pero no se guarda dos veces.

Los nodos envían por iniciativa propia en vez de ser sondeados: pueden dormir entre envíos, que es lo que necesitan los nodos móviles con batería y los fijos del vivero.

## Parámetros de radio (iguales en toda la red)
Frecuencia 915 MHz, ancho de banda 125 kHz, SF12, CR 4/5, sync word 0x77, CRC activo, 17 dBm. Con distancias de 600 m a 1.5 km, SF9 suele bastar y reduce el tiempo en el aire unas 8 veces; se cambia con `IOT_FACTOR_SF` en `IoTRadio.h` y debe cambiarse en TODOS los nodos y el gateway a la vez. Hágase tras pruebas de alcance.

## Nodos móviles T-Beam
Pantalla y dos botones: NAV (GPIO2) cambia la opción y OK (GPIO38) la ejecuta ("Medir y enviar" o "Estado del nodo"). Al medir se energiza el riel de sensores, se busca GPS (hasta 45 s), se mide, se envía con ACK y se apaga todo. La pantalla se apaga tras 30 s sin uso.

| Pin | Uso |
|---|---|
| 21 / 22 | I2C: OLED, ADS1115, BME280, SCD41 |
| 4 | DS18B20 (agua o suelo), con 4.7 kΩ a 3.3 V |
| 13 | Flotador de nivel (nodo agua) |
| 25 | Control del riel de sensores (MOSFET) |
| 14 / 15 / 32 | PMS5003 RX2 / TX2 / SET (nodo aire) |
| 2 / 38 | Botones NAV / OK |
| 34 / 12 | GPS (internos) |

El riel conmutado alimenta solo los sensores analógicos, la sonda y el PMS5003. El ADS1115, el BME280, el SCD41 y la pantalla van a 3.3 V permanente: un integrado I2C sin alimentación sujeta SDA y SCL por sus diodos de protección y bloquea el bus. Los sensores de 5 V (pH, turbidez, PMS5003) requieren un elevador a 5 V (por ejemplo MT3608) controlado por el mismo MOSFET, porque la T-Beam solo entrega 5 V con USB.

Entradas del ADS1115 (ganancia ±4.096 V, alimentado a 3.3 V, entradas máximas 3.6 V):
| Canal | Sensor | Nota |
|---|---|---|
| A0 | pH SEN0161 (agua) / capacitivo (suelo) | salida 0-3 V |
| A1 | Turbidez SEN0189 | divisor 10 kΩ arriba y 20 kΩ abajo (factor 1.5) |
| A2 | TDS SEN0244 | salida hasta 2.3 V |

## Nodos fijos LoRa32 del vivero
Cada 300 s despiertan, miden, envían con ACK y duermen (sueño profundo). Si no hay ACK reintentan a los 60 s. Pines: DS18B20 en GPIO2, flotador en GPIO13, PMS5003 RX 34 / TX 14 / SET 25 (se evita GPIO12 por ser pin de arranque).

## Calibración (por puerto serie, 115200)
- pH: buffer 7.00 con `7`, buffer 4.01 con `4`, `i` muestra voltajes.
- Suelo: sensor al aire con `s` (0 %), sensor en agua con `h` (100 %).
- En los LoRa32 el menú se ofrece 10 s tras conectar la energía; con una tecla se entra y con `q` se sale.
- Los valores se guardan en memoria no volátil.
- Turbidez, TDS, BME280, SCD41 y PMS5003 no requieren calibración propia (TDS se compensa con la temperatura del agua).

## Pruebas
```bash
# Protocolo y cálculos (en un PC)
cd firmware/libraries/IoTMangrove/tests
g++ -std=c++17 -Wall -Wextra -I../src probar_protocolo.cpp -o probar && ./probar
# Sintaxis de todos los sketches contra sustitutos de las bibliotecas
bash firmware/tests/verificar_sintaxis.sh
```
Alcance de las pruebas: la verificación de sintaxis usa sustitutos que reproducen el API esperado de cada biblioteca, así que no reemplaza la compilación con el IDE. Los cálculos y el protocolo sí se prueban con la lógica real.

## Pendiente (siguientes etapas)
Controlador central del riego (ESP32 con ESP-NOW, RTC DS3231 y enlace MQTT/HTTP con `/api/riego/central/*`), firmware de las válvulas motorizadas y, cuando se definan, nodos adicionales de la estación del vivero.
