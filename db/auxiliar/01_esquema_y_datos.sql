-- =====================================================================
-- IoT-Mangrove: base de datos auxiliar (MySQL 8 / MariaDB 10.6+)
--
-- Base de conocimiento del chatbot (Tidio): preguntas frecuentes, fichas
-- de cada variable ambiental con sus umbrales y usos, y bitacora de las
-- consultas realizadas. Todas las tablas incluyen:
--   * id          : llave primaria
--   * estado      : TINYINT(1), 1 por defecto. 0 = eliminado logicamente
--   * creado      : fecha de creación, asignada por el motor
--   * actualizado : se actualiza sola en cada UPDATE (ON UPDATE)
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS categoria_conocimiento (
    id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre       VARCHAR(80)  NOT NULL,
    descripcion  VARCHAR(255) NULL,
    estado       TINYINT(1)   NOT NULL DEFAULT 1,
    creado       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_categoria_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ficha de cada variable: significado, rango normal y para que se usa.
-- codigo_variable coincide con variable.codigo de la base principal.
CREATE TABLE IF NOT EXISTS referencia_variable (
    id               INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    codigo_variable  VARCHAR(30)   NOT NULL,
    nombre           VARCHAR(100)  NOT NULL,
    unidad           VARCHAR(20)   NOT NULL,
    descripcion      TEXT          NOT NULL,
    uso              TEXT          NOT NULL,
    rango_normal_min DECIMAL(10,2) NULL,
    rango_normal_max DECIMAL(10,2) NULL,
    fuente           VARCHAR(255)  NULL,
    estado           TINYINT(1)    NOT NULL DEFAULT 1,
    creado           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_referencia_codigo (codigo_variable)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS conocimiento_chatbot (
    id                      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    categoria_id            INT UNSIGNED NOT NULL,
    referencia_variable_id  INT UNSIGNED NULL,
    pregunta                VARCHAR(255) NOT NULL,
    respuesta               TEXT         NOT NULL,
    palabras_clave          VARCHAR(255) NOT NULL,
    estado                  TINYINT(1)   NOT NULL DEFAULT 1,
    creado                  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado             TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_conocimiento_pregunta (pregunta),
    KEY idx_conocimiento_categoria (categoria_id),
    KEY idx_conocimiento_referencia (referencia_variable_id),
    CONSTRAINT fk_conocimiento_categoria FOREIGN KEY (categoria_id)
        REFERENCES categoria_conocimiento (id),
    CONSTRAINT fk_conocimiento_referencia FOREIGN KEY (referencia_variable_id)
        REFERENCES referencia_variable (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bitacora de lo que preguntan los usuarios al chatbot
CREATE TABLE IF NOT EXISTS consulta_chatbot (
    id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    conocimiento_id  INT UNSIGNED    NULL,
    texto_consulta   VARCHAR(500)    NOT NULL,
    encontrada       TINYINT(1)      NOT NULL DEFAULT 0,
    origen           VARCHAR(30)     NOT NULL DEFAULT 'tidio',
    estado           TINYINT(1)      NOT NULL DEFAULT 1,
    creado           TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_consulta_conocimiento (conocimiento_id),
    KEY idx_consulta_creado (creado),
    CONSTRAINT fk_consulta_conocimiento FOREIGN KEY (conocimiento_id)
        REFERENCES conocimiento_chatbot (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Datos iniciales
-- ---------------------------------------------------------------------
INSERT IGNORE INTO categoria_conocimiento (nombre, descripcion) VALUES
    ('Calidad del agua', 'pH, turbidez, TDS y nivel de agua'),
    ('Ambiente', 'Temperatura, humedad, presión y calidad del aire'),
    ('Suelo', 'Humedad del suelo'),
    ('Sistema', 'Funcionamiento del prototipo, nodos y alertas');

INSERT IGNORE INTO referencia_variable
    (codigo_variable, nombre, unidad, descripcion, uso, rango_normal_min, rango_normal_max, fuente) VALUES
    ('ph', 'pH del agua', 'pH',
     'Mide la acidez o alcalinidad del agua.',
     'Valores fuera de 6.5 a 8.5 afectan a peces, crustaceos y a la absorcion de nutrientes de las raíces del mangle.',
     6.50, 8.50, 'Umbral de referencia del proyecto; ajustable'),
    ('turbidity', 'Turbidez', 'NTU',
     'Cantidad de particulas en suspension que enturbian el agua.',
     'Una turbidez alta reduce la luz disponible y puede indicar erosion, vertimientos o remocion de sedimentos.',
     0.00, 50.00, 'Umbral de referencia del proyecto; ajustable'),
    ('tds', 'Solidos disueltos (TDS)', 'ppm',
     'Concentracion de sales y minerales disueltos en el agua.',
     'Permite estimar la salinidad y detectar cambios por aportes de agua dulce o contaminacion.',
     0.00, 1000.00, 'Umbral de referencia del proyecto; ajustable'),
    ('water_level', 'Nivel de agua', 'bin',
     'Indica con un flotador magnetico si el agua alcanzó el nivel del sensor (1) o no (0).',
     'Sirve para registrar el ciclo de mareas y las inundaciones del sitio.',
     NULL, NULL, 'Sensor tipo boya'),
    ('temperature', 'Temperatura ambiente', 'C',
     'Temperatura del aire medida con el sensor BME280.',
     'Influye en la evaporacion, la salinidad del suelo y el metabolismo de la fauna.',
     15.00, 35.00, 'Umbral de referencia del proyecto; ajustable'),
    ('humidity', 'Humedad relativa', '%',
     'Porcentaje de vapor de agua en el aire (BME280).',
     'Junto con la temperatura describe el microclima del manglar.',
     30.00, 90.00, 'Umbral de referencia del proyecto; ajustable'),
    ('pressure', 'Presión atmosférica', 'hPa',
     'Presión barométrica del aire (BME280).',
     'Sus caidas bruscas anticipan tormentas y cambios en las mareas.',
     980.00, 1030.00, 'Umbral de referencia del proyecto; ajustable'),
    ('eco2', 'eCO2', 'ppm',
     'Dioxido de carbono equivalente estimado por el sensor SGP30.',
     'Indica la calidad del aire; valores altos señalan quemas o descomposicion de materia orgánica.',
     400.00, 1000.00, 'Umbral de referencia del proyecto; ajustable'),
    ('tvoc', 'TVOC', 'ppb',
     'Compuestos orgánicos volátiles totales medidos por el sensor SGP30.',
     'Detecta emisiones de gases orgánicos, combustibles o descomposicion.',
     0.00, 220.00, 'Umbral de referencia del proyecto; ajustable'),
    ('soil_humidity', 'Humedad del suelo', '%',
     'Contenido de agua del suelo medido con un sensor capacitivo v1.2.',
     'Muestra la influencia de la marea y la sequía sobre el sustrato donde crecen las raíces.',
     20.00, 90.00, 'Umbral de referencia del proyecto; ajustable');

INSERT IGNORE INTO conocimiento_chatbot (categoria_id, referencia_variable_id, pregunta, respuesta, palabras_clave) VALUES
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Calidad del agua'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='ph'),
     '¿Cuál es el pH normal del agua del manglar?',
     'El rango de referencia del proyecto es de 6.5 a 8.5. Fuera de ese rango se genera una advertencia, y bajo 6.0 o sobre 9.0 una alerta crítica.',
     'ph acidez alcalinidad agua normal rango umbral'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Calidad del agua'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='turbidity'),
     '¿Qué significa la turbidez y cuándo es alta?',
     'La turbidez mide las particulas suspendidas en el agua, en NTU. Sobre 50 NTU hay advertencia y sobre 100 NTU alerta crítica.',
     'turbidez turbia sedimentos ntu agua'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Calidad del agua'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='tds'),
     '¿Qué es el TDS y para qué sirve?',
     'El TDS es la cantidad de solidos disueltos en el agua, en ppm. Permite estimar la salinidad. Sobre 1000 ppm hay advertencia y sobre 2000 ppm alerta crítica.',
     'tds solidos disueltos salinidad sales ppm'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Ambiente'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='temperature'),
     '¿Qué temperatura es normal en el manglar?',
     'El rango de referencia es de 15 a 35 grados Celsius. Fuera de él se emite una advertencia, y bajo 10 o sobre 40 una alerta crítica.',
     'temperatura calor frio grados celsius ambiente'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Ambiente'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='humidity'),
     '¿Cuál es la humedad relativa esperada?',
     'La humedad relativa habitual del manglar está entre 30 % y 90 %. Se mide con el sensor BME280.',
     'humedad relativa aire ambiente bme280'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Ambiente'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='eco2'),
     '¿Qué miden el eCO2 y el TVOC?',
     'Son estimaciones de calidad del aire que entrega el sensor SGP30. El eCO2 se mide en ppm (advertencia sobre 1000) y el TVOC en ppb (advertencia sobre 220).',
     'eco2 co2 tvoc aire calidad gases sgp30 voc'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Ambiente'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='pressure'),
     '¿Para qué se mide la presión atmosférica?',
     'La presión barométrica permite anticipar tormentas y cambios de marea. El rango de referencia es de 980 a 1030 hPa.',
     'presión atmosférica barométrica hpa tormenta'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Suelo'),
     (SELECT id FROM referencia_variable WHERE codigo_variable='soil_humidity'),
     '¿Cómo se mide la humedad del suelo?',
     'Con un sensor capacitivo v1.2, que no se corroe como los resistivos. El rango de referencia es de 20 % a 90 %.',
     'humedad suelo sustrato capacitivo tierra'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Sistema'), NULL,
     '¿Cada cuánto se actualizan los datos?',
     'Los nodos envian sus mediciones por LoRa al gateway, que las pública en el servidor. El dashboard se refresca automáticamente cada 15 segundos.',
     'actualizan frecuencia tiempo refresca datos cada cuanto'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Sistema'), NULL,
     '¿Qué significan las alertas de advertencia y crítica?',
     'La advertencia indica que un valor salió del rango recomendado. La alerta crítica indica un valor extremo que requiere atención inmediata.',
     'alerta advertencia crítica crítico umbral significado'),
    ((SELECT id FROM categoria_conocimiento WHERE nombre='Sistema'), NULL,
     '¿Cómo funciona el sistema?',
     'Los nodos con sensores y GPS transmiten por LoRa a un gateway, que envia los datos por internet a una API. Los datos se guardan en una base de datos y se muestran en el dashboard.',
     'sistema funciona como funciona lora gateway nodo arquitectura');
