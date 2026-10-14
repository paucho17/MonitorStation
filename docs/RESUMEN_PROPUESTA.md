# IoT-Mangrove: sistema telemático para el monitoreo ambiental de manglares

## Resumen de la propuesta

### Problemática
Los manglares protegen la costa de la erosión y las tormentas, almacenan carbono, filtran el agua y sirven de criadero a peces y crustáceos. Sin embargo, están expuestos a la contaminación, a cambios de salinidad y de pH, al aumento de sedimentos y a la deforestación. Hoy su seguimiento depende de visitas esporádicas en las que se toman muestras manuales. Esto genera tres problemas:

1. **Datos escasos y tardíos:** entre una visita y otra pueden ocurrir eventos de contaminación o estrés hídrico que nadie registra.
2. **Zonas de difícil acceso:** los manglares carecen de cobertura celular y de energía eléctrica, lo que encarece y limita el monitoreo continuo.
3. **Información dispersa:** las mediciones quedan en cuadernos u hojas sueltas, sin historial consultable ni alertas oportunas para quienes toman decisiones.

### Población beneficiada
- Comunidades costeras que dependen de la pesca y del turismo asociado al manglar.
- Autoridades ambientales y entidades de manejo de áreas protegidas, que requieren evidencia continua para actuar.
- Investigadores, docentes y estudiantes que necesitan series de datos históricos.
- Organizaciones de conservación que hacen seguimiento a proyectos de restauración.

### Solución propuesta
Una red de sensores de bajo consumo que mide variables del agua, del aire y del suelo y envía los datos por radio LoRa (largo alcance, sin infraestructura celular) hasta un gateway. El gateway pública las mediciones en internet, donde una API las almacena, evalua umbrales y genera alertas. Los usuarios consultan el último dato y el historial en un panel web, y un chatbot responde preguntas sobre las variables, sus umbrales y su uso.

Flujo de datos:
1. **Nodos emisores** (LilyGO T-Beam V1.2 con GPS): leen los sensores y empaquetan la trama junto con las coordenadas.
2. **Gateway LoRa:** recibe la trama por radio y la reenvía por HTTP a la API, autenticado con una clave propia.
3. **API principal (FastAPI) y base PostgreSQL:** validan, guardan, comparan con umbrales y generan alertas. Autenticación con JWT y permisos por rol y módulo.
4. **API auxiliar (Express) y base MySQL:** base de conocimiento del chatbot (fichas de variables, preguntas frecuentes y bitacora de consultas).
5. **Panel web:** inicio de sesión, último dato de cada variable, alertas e historial con filtros.

Todo se despliega con Docker en un VPS, detras de Nginx con HTTPS, en el dominio iotmangrove.info.

### Variables monitoreadas
| Grupo | Variable | Sensor |
|---|---|---|
| Agua | pH, turbidez, solidos disueltos (TDS), nivel | Módulos de pH, turbidez y TDS; flotador magnético |
| Ambiente | Temperatura, humedad, presión | BME280 |
| Ambiente | eCO2, TVOC | SGP30 (reemplaza al MQ-135 por su menor consumo) |
| Suelo | Humedad | Sensor capacitivo v1.2 |
| Ubicación | Latitud, longitud, satelites | GPS GNSS del T-Beam |

### Requerimientos generales
**Funcionales**
- RF1. Recibir tramas de los nodos a traves del gateway y almacenarlas con fecha, calidad de señal (RSSI, SNR) y posición GPS.
- RF2. Gestionar usuarios, roles, módulos y permisos (control de acceso por rol).
- RF3. Autenticar con JWT, con cierre de sesión que inválida el token.
- RF4. Administrar zonas, gateways, nodos, sensores, variables, unidades y umbrales (CRUD con eliminación lógica).
- RF5. Generar alertas (advertencia y crítica) cuando una medición sale de su umbral y permitir marcarlas como atendidas.
- RF6. Mostrar el último dato de cada variable y el historial filtrable por nodo, variable y fechas.
- RF7. Responder preguntas del chatbot sobre variables, umbrales y usos, y registrar las consultas.

**No funcionales**
- RNF1. Bajo consumo en los nodos (se descarta el MQ-135 por su calefactor y el sensor de suelo resistivo por corrosión).
- RNF2. Cobertura de largo alcance con LoRa (898 a 915 MHz).
- RNF3. Seguridad: contraseñas con bcrypt, JWT firmado, clave de API por gateway, HTTPS, bases de datos sin puertos públicos y secretos fuera del codigo.
- RNF4. Trazabilidad: toda tabla guarda estado, fecha de creación y fecha de actualización gestionadas por el motor de base de datos.
- RNF5. Despliegue reproducible con Docker Compose.

### Alcance del parcial
Se entrega la base de datos principal normalizada en PostgreSQL (16 tablas), la API principal con FastAPI (endpoints, JWT y despliegue), la base de datos auxiliar en MySQL (4 tablas), la API auxiliar con Express y el despliegue de ambas en el dominio.
