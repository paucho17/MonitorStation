-- =====================================================================
-- IoT-Mangrove: base de datos principal (PostgreSQL 15+)
--
-- Modelo normalizado (3FN) de 16 tablas. Todas las tablas incluyen:
--   * id         : llave primaria
--   * estado     : BOOLEAN, TRUE por defecto. FALSE = registro eliminado
--                  de forma logica (la fila no se borra). Lo manipula la API.
--   * creado     : fecha de creacion, asignada por el motor (DEFAULT now()).
--   * actualizado: fecha de la ultima modificacion, mantenida por el
--                  trigger trg_actualizado (el desarrollador no la envia).
--
-- Grupos de tablas:
--   Seguridad      : rol, usuario, modulo, modulo_rol, sesion_token
--   Infraestructura: zona_manglar, gateway, tipo_nodo, nodo
--   Catalogos      : unidad_medida, variable, sensor
--   Datos          : lectura, medicion
--   Alertas        : umbral, alerta
-- =====================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS citext;

-- ---------------------------------------------------------------------
-- Funcion de auditoria: actualiza el campo "actualizado" en cada UPDATE
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_set_actualizado()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- SEGURIDAD
-- =====================================================================

CREATE TABLE rol (
    id           SERIAL PRIMARY KEY,
    nombre       CITEXT       NOT NULL UNIQUE,
    descripcion  VARCHAR(255),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE usuario (
    id               SERIAL PRIMARY KEY,
    rol_id           INTEGER      NOT NULL REFERENCES rol (id),
    username         CITEXT       NOT NULL UNIQUE,
    email            CITEXT       UNIQUE,
    nombre_completo  VARCHAR(120),
    password_hash    VARCHAR(255) NOT NULL,   -- bcrypt, nunca texto plano
    estado           BOOLEAN      NOT NULL DEFAULT TRUE,
    creado           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_usuario_rol ON usuario (rol_id);

CREATE TABLE modulo (
    id           SERIAL PRIMARY KEY,
    nombre       CITEXT       NOT NULL UNIQUE,   -- clave usada por la API
    ruta         VARCHAR(100) NOT NULL UNIQUE,   -- ruta del recurso en la API
    descripcion  VARCHAR(255),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- moduloxrol: permisos de cada rol sobre cada modulo
CREATE TABLE modulo_rol (
    id               SERIAL PRIMARY KEY,
    rol_id           INTEGER     NOT NULL REFERENCES rol (id),
    modulo_id        INTEGER     NOT NULL REFERENCES modulo (id),
    puede_leer       BOOLEAN     NOT NULL DEFAULT TRUE,
    puede_crear      BOOLEAN     NOT NULL DEFAULT FALSE,
    puede_editar     BOOLEAN     NOT NULL DEFAULT FALSE,
    puede_eliminar   BOOLEAN     NOT NULL DEFAULT FALSE,
    estado           BOOLEAN     NOT NULL DEFAULT TRUE,
    creado           TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_modulo_rol UNIQUE (rol_id, modulo_id)
);
CREATE INDEX idx_modulo_rol_modulo ON modulo_rol (modulo_id);

-- Registro de tokens JWT emitidos (permite cerrar sesion / revocar)
CREATE TABLE sesion_token (
    id           BIGSERIAL PRIMARY KEY,
    usuario_id   INTEGER      NOT NULL REFERENCES usuario (id),
    jti          VARCHAR(64)  NOT NULL UNIQUE,   -- identificador unico del JWT
    expira_en    TIMESTAMPTZ  NOT NULL,
    revocado     BOOLEAN      NOT NULL DEFAULT FALSE,
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_sesion_usuario ON sesion_token (usuario_id);

-- =====================================================================
-- INFRAESTRUCTURA
-- =====================================================================

CREATE TABLE zona_manglar (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(100)     NOT NULL UNIQUE,
    descripcion  VARCHAR(255),
    municipio    VARCHAR(100),
    latitud      DOUBLE PRECISION CHECK (latitud  BETWEEN -90  AND 90),
    longitud     DOUBLE PRECISION CHECK (longitud BETWEEN -180 AND 180),
    estado       BOOLEAN          NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ      NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ      NOT NULL DEFAULT now()
);

CREATE TABLE gateway (
    id                SERIAL PRIMARY KEY,
    codigo            VARCHAR(20)  NOT NULL UNIQUE,   -- p. ej. 0xDD
    nombre            VARCHAR(100) NOT NULL,
    zona_id           INTEGER      REFERENCES zona_manglar (id),
    api_key_hash      CHAR(64)     NOT NULL UNIQUE,   -- SHA-256 de la clave
    ultima_conexion   TIMESTAMPTZ,
    estado            BOOLEAN      NOT NULL DEFAULT TRUE,
    creado            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado       TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_gateway_zona ON gateway (zona_id);

-- Categoria del nodo segun la trama LoRa: WATER, AMB, SOIL
CREATE TABLE tipo_nodo (
    id           SERIAL PRIMARY KEY,
    codigo       VARCHAR(20)  NOT NULL UNIQUE,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE nodo (
    id            SERIAL PRIMARY KEY,
    codigo        VARCHAR(20)  NOT NULL UNIQUE,      -- p. ej. 0xAA
    nombre        VARCHAR(100),
    tipo_nodo_id  INTEGER      NOT NULL REFERENCES tipo_nodo (id),
    zona_id       INTEGER      REFERENCES zona_manglar (id),
    gateway_id    INTEGER      REFERENCES gateway (id),
    hardware      VARCHAR(100) DEFAULT 'LilyGO T-Beam V1.2',
    estado        BOOLEAN      NOT NULL DEFAULT TRUE,
    creado        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_nodo_tipo    ON nodo (tipo_nodo_id);
CREATE INDEX idx_nodo_zona    ON nodo (zona_id);
CREATE INDEX idx_nodo_gateway ON nodo (gateway_id);

-- =====================================================================
-- CATALOGOS
-- =====================================================================

CREATE TABLE unidad_medida (
    id           SERIAL PRIMARY KEY,
    simbolo      VARCHAR(20)  NOT NULL UNIQUE,
    nombre       VARCHAR(60)  NOT NULL,
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE variable (
    id             SERIAL PRIMARY KEY,
    codigo         VARCHAR(30)  NOT NULL UNIQUE,     -- ph, turbidity, ...
    nombre         VARCHAR(100) NOT NULL,
    descripcion    VARCHAR(255),
    unidad_id      INTEGER      NOT NULL REFERENCES unidad_medida (id),
    tipo_nodo_id   INTEGER      REFERENCES tipo_nodo (id),
    rango_min      REAL,                              -- rango fisico valido
    rango_max      REAL,
    estado         BOOLEAN      NOT NULL DEFAULT TRUE,
    creado         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_variable_rango CHECK (rango_min IS NULL OR rango_max IS NULL OR rango_min < rango_max)
);
CREATE INDEX idx_variable_unidad ON variable (unidad_id);
CREATE INDEX idx_variable_tipo   ON variable (tipo_nodo_id);

-- Sensor fisico instalado en un nodo (un registro por variable que mide)
CREATE TABLE sensor (
    id                   SERIAL PRIMARY KEY,
    nodo_id              INTEGER      NOT NULL REFERENCES nodo (id),
    variable_id          INTEGER      NOT NULL REFERENCES variable (id),
    modelo               VARCHAR(60)  NOT NULL,       -- BME280, SGP30, ...
    fecha_instalacion    DATE,
    estado               BOOLEAN      NOT NULL DEFAULT TRUE,
    creado               TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_sensor UNIQUE (nodo_id, variable_id, modelo)
);
CREATE INDEX idx_sensor_variable ON sensor (variable_id);

-- =====================================================================
-- DATOS
-- =====================================================================

-- Una lectura = una trama LoRa recibida por un gateway
CREATE TABLE lectura (
    id                BIGSERIAL PRIMARY KEY,
    nodo_id           INTEGER          NOT NULL REFERENCES nodo (id),
    gateway_id        INTEGER          NOT NULL REFERENCES gateway (id),
    rssi              INTEGER,
    snr               REAL,
    latitud           DOUBLE PRECISION CHECK (latitud  BETWEEN -90  AND 90),
    longitud          DOUBLE PRECISION CHECK (longitud BETWEEN -180 AND 180),
    satelites         SMALLINT,
    fecha_recepcion   TIMESTAMPTZ      NOT NULL DEFAULT now(),
    estado            BOOLEAN          NOT NULL DEFAULT TRUE,
    creado            TIMESTAMPTZ      NOT NULL DEFAULT now(),
    actualizado       TIMESTAMPTZ      NOT NULL DEFAULT now()
);
CREATE INDEX idx_lectura_fecha   ON lectura (fecha_recepcion DESC);
CREATE INDEX idx_lectura_nodo    ON lectura (nodo_id, fecha_recepcion DESC);
CREATE INDEX idx_lectura_gateway ON lectura (gateway_id);

-- Cada valor medido dentro de una lectura (una fila por variable)
CREATE TABLE medicion (
    id           BIGSERIAL PRIMARY KEY,
    lectura_id   BIGINT           NOT NULL REFERENCES lectura (id),
    variable_id  INTEGER          NOT NULL REFERENCES variable (id),
    valor        DOUBLE PRECISION NOT NULL,
    estado       BOOLEAN          NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ      NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ      NOT NULL DEFAULT now(),
    CONSTRAINT uq_medicion UNIQUE (lectura_id, variable_id)
);
CREATE INDEX idx_medicion_variable ON medicion (variable_id, creado DESC);

-- =====================================================================
-- ALERTAS
-- =====================================================================

-- Rango aceptable por variable y nivel. Un valor fuera de [minimo, maximo]
-- dispara una alerta de ese nivel (el nivel CRITICO se evalua primero).
CREATE TABLE umbral (
    id           SERIAL PRIMARY KEY,
    variable_id  INTEGER      NOT NULL REFERENCES variable (id),
    nivel        VARCHAR(15)  NOT NULL CHECK (nivel IN ('ADVERTENCIA', 'CRITICO')),
    minimo       REAL,
    maximo       REAL,
    mensaje      VARCHAR(255),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_umbral UNIQUE (variable_id, nivel),
    CONSTRAINT ck_umbral_rango CHECK (minimo IS NULL OR maximo IS NULL OR minimo < maximo)
);

CREATE TABLE alerta (
    id           BIGSERIAL PRIMARY KEY,
    medicion_id  BIGINT       NOT NULL REFERENCES medicion (id),
    umbral_id    INTEGER      NOT NULL REFERENCES umbral (id),
    mensaje      VARCHAR(255),
    atendida     BOOLEAN      NOT NULL DEFAULT FALSE,
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_alerta UNIQUE (medicion_id, umbral_id)
);
CREATE INDEX idx_alerta_creado ON alerta (creado DESC);

-- ---------------------------------------------------------------------
-- Trigger de auditoria en TODAS las tablas
-- ---------------------------------------------------------------------
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'rol', 'usuario', 'modulo', 'modulo_rol', 'sesion_token',
        'zona_manglar', 'gateway', 'tipo_nodo', 'nodo',
        'unidad_medida', 'variable', 'sensor',
        'lectura', 'medicion', 'umbral', 'alerta'
    ]
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_actualizado BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION fn_set_actualizado()', t);
    END LOOP;
END $$;

COMMIT;
