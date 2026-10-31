-- =====================================================================
-- IoT-Mangrove: migracion 04, ambitos de monitoreo y sistema de riego
--
-- Hace el modelo extensible sin tocar el codigo de la API:
--   * ambito         : dominio de monitoreo (MANGLAR, VIVERO, RIEGO, ...).
--                      Agregar un ambito nuevo es insertar una fila.
--   * variable_alias : nombres con que los nodos reportan cada variable.
--                      Agregar un sensor nuevo = una variable + sus alias.
--   * zona_riego, actuador, programa_riego : configuracion del riego.
--   * comando_riego  : cola de ordenes (panel -> controlador central).
--   * evento_riego   : bitacora de riegos ejecutados.
--
-- El script es idempotente: puede ejecutarse varias veces (scripts/migrar_db.sh)
-- y tambien se ejecuta automaticamente en el primer arranque del contenedor.
-- Requiere haber ejecutado 01_esquema.sql y 02_semillas.sql.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Ambitos
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ambito (
    id           SERIAL PRIMARY KEY,
    codigo       VARCHAR(20)  NOT NULL UNIQUE,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255),
    orden        SMALLINT     NOT NULL DEFAULT 0,
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

INSERT INTO ambito (codigo, nombre, descripcion, orden) VALUES
    ('MANGLAR', 'Manglar',            'Nodos moviles de campo: agua, suelo y aire del manglar', 1),
    ('VIVERO',  'Vivero',             'Estaciones fijas del vivero de manglar y huerto de hongos', 2),
    ('RIEGO',   'Sistema de riego',   'Tanque, bomba, valvulas y energia solar del riego', 3)
ON CONFLICT (codigo) DO NOTHING;

ALTER TABLE nodo ADD COLUMN IF NOT EXISTS ambito_id INTEGER REFERENCES ambito (id);
UPDATE nodo SET ambito_id = (SELECT id FROM ambito WHERE codigo = 'MANGLAR') WHERE ambito_id IS NULL;
ALTER TABLE nodo ALTER COLUMN ambito_id SET NOT NULL;
ALTER TABLE nodo ALTER COLUMN ambito_id SET DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_nodo_ambito ON nodo (ambito_id);

-- ---------------------------------------------------------------------
-- Alias de variables (sustituye al diccionario fijo del codigo)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS variable_alias (
    id           SERIAL PRIMARY KEY,
    alias        VARCHAR(40)  NOT NULL UNIQUE,
    variable_id  INTEGER      NOT NULL REFERENCES variable (id),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_alias_variable ON variable_alias (variable_id);

-- ---------------------------------------------------------------------
-- Riego
-- ---------------------------------------------------------------------
-- Zona regada: agrupa valvulas y define como se decide el riego.
CREATE TABLE IF NOT EXISTS zona_riego (
    id                 SERIAL PRIMARY KEY,
    codigo             VARCHAR(20)  NOT NULL UNIQUE,
    nombre             VARCHAR(100) NOT NULL,
    descripcion        VARCHAR(255),
    ambito_id          INTEGER      NOT NULL REFERENCES ambito (id),
    modo               VARCHAR(12)  NOT NULL DEFAULT 'APAGADO'
                       CHECK (modo IN ('AUTO', 'PROGRAMADO', 'MANUAL', 'APAGADO')),
    nodo_sensor_id     INTEGER      REFERENCES nodo (id),     -- nodo cuya humedad decide el riego
    variable_id        INTEGER      REFERENCES variable (id), -- normalmente soil_humidity
    humedad_min        REAL         NOT NULL DEFAULT 35,      -- AUTO: abre por debajo
    humedad_max        REAL         NOT NULL DEFAULT 60,      -- AUTO: cierra por encima
    duracion_max_s     INTEGER      NOT NULL DEFAULT 600 CHECK (duracion_max_s > 0),
    descanso_min_s     INTEGER      NOT NULL DEFAULT 900 CHECK (descanso_min_s >= 0),
    limite_diario_s    INTEGER      NOT NULL DEFAULT 3600 CHECK (limite_diario_s > 0),
    estado             BOOLEAN      NOT NULL DEFAULT TRUE,
    creado             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_zona_riego_humedad CHECK (humedad_min < humedad_max)
);
CREATE INDEX IF NOT EXISTS idx_zona_riego_ambito ON zona_riego (ambito_id);

-- Valvula motorizada o bomba controlada por un ESP32
CREATE TABLE IF NOT EXISTS actuador (
    id                 SERIAL PRIMARY KEY,
    codigo             VARCHAR(20)  NOT NULL UNIQUE,
    nombre             VARCHAR(100) NOT NULL,
    tipo               VARCHAR(10)  NOT NULL CHECK (tipo IN ('VALVULA', 'BOMBA')),
    zona_riego_id      INTEGER      REFERENCES zona_riego (id),
    hardware           VARCHAR(100) DEFAULT 'ESP32',
    posicion           VARCHAR(12)  NOT NULL DEFAULT 'DESCONOCIDA'
                       CHECK (posicion IN ('ABIERTA', 'CERRADA', 'ENCENDIDA', 'APAGADA', 'DESCONOCIDA')),
    ultimo_reporte     TIMESTAMPTZ,
    estado             BOOLEAN      NOT NULL DEFAULT TRUE,
    creado             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado        TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_actuador_zona ON actuador (zona_riego_id);

-- Riego programado: dias como cadena de 7 caracteres (lunes a domingo, '1' = activo)
CREATE TABLE IF NOT EXISTS programa_riego (
    id               SERIAL PRIMARY KEY,
    zona_riego_id    INTEGER      NOT NULL REFERENCES zona_riego (id),
    hora_inicio      TIME         NOT NULL,
    duracion_s       INTEGER      NOT NULL CHECK (duracion_s > 0),
    dias             CHAR(7)      NOT NULL DEFAULT '1111111' CHECK (dias ~ '^[01]{7}$'),
    habilitado       BOOLEAN      NOT NULL DEFAULT TRUE,
    estado           BOOLEAN      NOT NULL DEFAULT TRUE,
    creado           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_programa_zona ON programa_riego (zona_riego_id);

-- Ordenes del panel hacia el controlador central (cola con acuse)
CREATE TABLE IF NOT EXISTS comando_riego (
    id               BIGSERIAL PRIMARY KEY,
    actuador_id      INTEGER      NOT NULL REFERENCES actuador (id),
    accion           VARCHAR(10)  NOT NULL CHECK (accion IN ('ABRIR', 'CERRAR')),
    duracion_s       INTEGER      CHECK (duracion_s IS NULL OR duracion_s > 0),
    origen           VARCHAR(12)  NOT NULL DEFAULT 'MANUAL'
                     CHECK (origen IN ('MANUAL', 'AUTO', 'PROGRAMADO', 'SEGURIDAD')),
    usuario_id       INTEGER      REFERENCES usuario (id),
    situacion        VARCHAR(10)  NOT NULL DEFAULT 'PENDIENTE'
                     CHECK (situacion IN ('PENDIENTE', 'ENVIADO', 'EJECUTADO', 'FALLIDO', 'CANCELADO')),
    detalle          VARCHAR(255),
    estado           BOOLEAN      NOT NULL DEFAULT TRUE,
    creado           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_comando_situacion ON comando_riego (situacion, creado);
CREATE INDEX IF NOT EXISTS idx_comando_actuador ON comando_riego (actuador_id);

-- Bitacora de riegos ejecutados (la reporta el controlador central)
CREATE TABLE IF NOT EXISTS evento_riego (
    id               BIGSERIAL PRIMARY KEY,
    actuador_id      INTEGER      NOT NULL REFERENCES actuador (id),
    zona_riego_id    INTEGER      REFERENCES zona_riego (id),
    inicio           TIMESTAMPTZ  NOT NULL,
    fin              TIMESTAMPTZ,
    duracion_s       INTEGER      CHECK (duracion_s IS NULL OR duracion_s >= 0),
    origen           VARCHAR(12)  NOT NULL DEFAULT 'MANUAL'
                     CHECK (origen IN ('MANUAL', 'AUTO', 'PROGRAMADO', 'SEGURIDAD')),
    motivo           VARCHAR(255),
    estado           BOOLEAN      NOT NULL DEFAULT TRUE,
    creado           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_evento_inicio ON evento_riego (inicio DESC);
CREATE INDEX IF NOT EXISTS idx_evento_zona ON evento_riego (zona_riego_id);

-- ---------------------------------------------------------------------
-- Trigger de auditoria en las tablas nuevas (idempotente)
-- ---------------------------------------------------------------------
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'ambito', 'variable_alias', 'zona_riego', 'actuador',
        'programa_riego', 'comando_riego', 'evento_riego'
    ]
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'trg_actualizado' AND tgrelid = t::regclass
        ) THEN
            EXECUTE format(
                'CREATE TRIGGER trg_actualizado BEFORE UPDATE ON %I
                 FOR EACH ROW EXECUTE FUNCTION fn_set_actualizado()', t);
        END IF;
    END LOOP;
END $$;

-- ---------------------------------------------------------------------
-- Catalogos: tipos de nodo, unidades, variables, alias y umbrales
-- ---------------------------------------------------------------------
INSERT INTO tipo_nodo (codigo, nombre, descripcion) VALUES
    ('RIEGO', 'Sistema de riego', 'Controlador central: tanque, bomba, valvulas y energia')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO unidad_medida (simbolo, nombre) VALUES
    ('ug/m3', 'Microgramos por metro cubico'),
    ('V',     'Voltios'),
    ('L/min', 'Litros por minuto')
ON CONFLICT (simbolo) DO NOTHING;

INSERT INTO variable (codigo, nombre, descripcion, unidad_id, tipo_nodo_id, rango_min, rango_max)
SELECT v.codigo, v.nombre, v.descripcion,
       (SELECT id FROM unidad_medida WHERE simbolo = v.unidad),
       (SELECT id FROM tipo_nodo     WHERE codigo  = v.tipo),
       v.rmin, v.rmax
FROM (VALUES
    ('water_temperature', 'Temperatura del agua',   'Sonda DS18B20 sumergible',                  'C',     'WATER',   -5,    60),
    ('soil_temperature',  'Temperatura del suelo',  'Sonda DS18B20 enterrada',                   'C',     'SOIL',   -10,    70),
    ('co2',               'CO2',                    'Dioxido de carbono medido (SCD41)',         'ppm',   'AMB',      0, 40000),
    ('pm1',               'PM1.0',                  'Material particulado fino (PMS5003)',       'ug/m3', 'AMB',      0,  1000),
    ('pm2_5',             'PM2.5',                  'Material particulado fino (PMS5003)',       'ug/m3', 'AMB',      0,  1000),
    ('pm10',              'PM10',                   'Material particulado grueso (PMS5003)',     'ug/m3', 'AMB',      0,  1000),
    ('tank_level',        'Nivel del tanque',       'Porcentaje de llenado del tanque de riego', '%',     'RIEGO',    0,   100),
    ('pump_state',        'Estado de la bomba',     '1 = bomba encendida',                       'bin',   'RIEGO',    0,     1),
    ('flow_rate',         'Caudal',                 'Caudal de la linea de riego',               'L/min', 'RIEGO',    0,   100),
    ('battery_voltage',   'Voltaje de bateria',     'Bateria del sistema solar',                 'V',     'RIEGO',    0,    30),
    ('battery_percent',   'Carga de bateria',       'Estado de carga estimado',                  '%',     'RIEGO',    0,   100)
) AS v (codigo, nombre, descripcion, unidad, tipo, rmin, rmax)
ON CONFLICT (codigo) DO NOTHING;

-- Alias: nombre en la trama -> variable. Los alias existentes salen del
-- diccionario que antes estaba escrito en la API.
INSERT INTO variable_alias (alias, variable_id)
SELECT a.alias, v.id
FROM (VALUES
    ('ph', 'ph'), ('turbidity', 'turbidity'), ('tds', 'tds'),
    ('waterLevel', 'water_level'), ('water_level', 'water_level'),
    ('temperature', 'temperature'), ('humidity', 'humidity'), ('pressure', 'pressure'),
    ('eco2', 'eco2'), ('eCO2', 'eco2'), ('tvoc', 'tvoc'), ('TVOC', 'tvoc'),
    ('soilHumidity', 'soil_humidity'), ('soil_humidity', 'soil_humidity'),
    ('waterTemp', 'water_temperature'), ('water_temperature', 'water_temperature'),
    ('soilTemp', 'soil_temperature'), ('soil_temperature', 'soil_temperature'),
    ('co2', 'co2'), ('CO2', 'co2'),
    ('pm1', 'pm1'), ('pm25', 'pm2_5'), ('pm2_5', 'pm2_5'), ('pm10', 'pm10'),
    ('tankLevel', 'tank_level'), ('tank_level', 'tank_level'),
    ('pump', 'pump_state'), ('pump_state', 'pump_state'),
    ('flow', 'flow_rate'), ('flow_rate', 'flow_rate'),
    ('vbat', 'battery_voltage'), ('battery_voltage', 'battery_voltage'),
    ('bat', 'battery_percent'), ('battery_percent', 'battery_percent')
) AS a (alias, codigo)
JOIN variable v ON v.codigo = a.codigo
ON CONFLICT (alias) DO NOTHING;

INSERT INTO umbral (variable_id, nivel, minimo, maximo, mensaje)
SELECT (SELECT id FROM variable WHERE codigo = u.codigo), u.nivel, u.minimo, u.maximo, u.mensaje
FROM (VALUES
    ('water_temperature', 'ADVERTENCIA', 20,  32,   'Temperatura del agua fuera del rango habitual'),
    ('water_temperature', 'CRITICO',     15,  35,   'Temperatura del agua extrema'),
    ('soil_temperature',  'ADVERTENCIA', 15,  35,   'Temperatura del suelo fuera del rango habitual'),
    ('soil_temperature',  'CRITICO',     10,  42,   'Temperatura del suelo extrema'),
    ('co2',               'ADVERTENCIA', NULL, 1000, 'CO2 elevado'),
    ('co2',               'CRITICO',     NULL, 2000, 'CO2 critico'),
    ('pm2_5',             'ADVERTENCIA', NULL, 35,   'Material particulado PM2.5 elevado'),
    ('pm2_5',             'CRITICO',     NULL, 75,   'Material particulado PM2.5 critico'),
    ('pm10',              'ADVERTENCIA', NULL, 50,   'Material particulado PM10 elevado'),
    ('pm10',              'CRITICO',     NULL, 150,  'Material particulado PM10 critico'),
    ('tank_level',        'ADVERTENCIA', 25,  NULL,  'Nivel del tanque bajo'),
    ('tank_level',        'CRITICO',     10,  NULL,  'Tanque casi vacio: riego bloqueado'),
    ('battery_percent',   'ADVERTENCIA', 30,  NULL,  'Bateria baja'),
    ('battery_percent',   'CRITICO',     15,  NULL,  'Bateria critica')
) AS u (codigo, nivel, minimo, maximo, mensaje)
ON CONFLICT (variable_id, nivel) DO NOTHING;

-- ---------------------------------------------------------------------
-- Modulos y permisos
-- ---------------------------------------------------------------------
INSERT INTO modulo (nombre, ruta, descripcion) VALUES
    ('ambitos',         '/api/ambitos',         'Ambitos de monitoreo'),
    ('alias-variables', '/api/alias-variables', 'Nombres de variable aceptados en la ingesta'),
    ('zonas-riego',     '/api/zonas-riego',     'Zonas de riego y sus reglas'),
    ('actuadores',      '/api/actuadores',      'Valvulas y bomba'),
    ('programas-riego', '/api/programas-riego', 'Horarios de riego programado'),
    ('comandos-riego',  '/api/comandos-riego',  'Cola de ordenes de riego'),
    ('eventos-riego',   '/api/eventos-riego',   'Bitacora de riegos ejecutados'),
    ('riego',           '/api/riego',           'Estado del riego, modos y mando manual')
ON CONFLICT (nombre) DO NOTHING;

-- admin: todo
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear, puede_editar, puede_eliminar)
SELECT r.id, m.id, TRUE, TRUE, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'admin'
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

-- operador: administra el riego; lee ambitos, alias, ordenes y bitacora
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear, puede_editar, puede_eliminar)
SELECT r.id, m.id, TRUE, TRUE, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'operador'
  AND m.nombre IN ('zonas-riego', 'actuadores', 'programas-riego', 'riego')
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer)
SELECT r.id, m.id, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'operador'
  AND m.nombre IN ('ambitos', 'alias-variables', 'comandos-riego', 'eventos-riego')
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

-- consulta: solo lectura
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer)
SELECT r.id, m.id, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'consulta'
  AND m.nombre IN ('ambitos', 'zonas-riego', 'actuadores', 'programas-riego',
                   'eventos-riego', 'riego')
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

COMMIT;
