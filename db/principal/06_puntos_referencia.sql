-- =====================================================================
-- IoT-Mangrove: migracion 06, puntos de referencia GPS
--
--   * punto_referencia : waypoints levantados en campo con GPS de mano
--                        (Garmin GPSMAP 78s) que el panel dibuja sobre el
--                        mapa. Una campana agrupa los puntos de una salida.
--
-- Carga la campana del 8 de noviembre de 2026 (Ciénaga de Mallorquín,
-- Asoplaya): punto 304 (muelle) y puntos 1 a 20 en cinco lineas de muestreo.
-- La elevacion del GPS no se almacena por no ser confiable bajo dosel.
--
-- Idempotente: puede ejecutarse varias veces (scripts/migrar_db.sh).
-- Requiere las migraciones 01 a 05.
-- =====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS punto_referencia (
    id           SERIAL PRIMARY KEY,
    campana      DATE             NOT NULL,
    nombre       VARCHAR(20)      NOT NULL,
    linea        VARCHAR(20),
    descripcion  VARCHAR(255),
    latitud      DOUBLE PRECISION NOT NULL CHECK (latitud  BETWEEN -90  AND 90),
    longitud     DOUBLE PRECISION NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    capturado_en TIMESTAMPTZ,
    estado       BOOLEAN          NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ      NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ      NOT NULL DEFAULT now(),
    UNIQUE (campana, nombre)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_actualizado' AND tgrelid = 'punto_referencia'::regclass
    ) THEN
        CREATE TRIGGER trg_actualizado BEFORE UPDATE ON punto_referencia
        FOR EACH ROW EXECUTE FUNCTION fn_set_actualizado();
    END IF;
END $$;

INSERT INTO punto_referencia (campana, nombre, linea, descripcion, latitud, longitud, capturado_en) VALUES
    ('2026-11-08', '304', NULL, 'Muelle de Asoplaya (referencia general)', 11.035785, -74.859928, '2026-11-08T12:32:21Z'),
    ('2026-11-08', '1er', 'Linea 1', NULL, 11.051339, -74.853287, '2026-11-08T13:41:12Z'),
    ('2026-11-08', '2do', 'Linea 1', NULL, 11.051381, -74.853278, '2026-11-08T13:43:13Z'),
    ('2026-11-08', '3er', 'Linea 1', NULL, 11.051428, -74.853271, '2026-11-08T13:45:06Z'),
    ('2026-11-08', '4to', 'Linea 1', NULL, 11.051468, -74.853258, '2026-11-08T13:49:33Z'),
    ('2026-11-08', '5to', 'Linea 2', NULL, 11.051292, -74.853279, '2026-11-08T13:52:31Z'),
    ('2026-11-08', '6to', 'Linea 2', NULL, 11.051250, -74.853287, '2026-11-08T13:53:29Z'),
    ('2026-11-08', '7mo', 'Linea 2', NULL, 11.051215, -74.853313, '2026-11-08T13:55:27Z'),
    ('2026-11-08', '8vo', 'Linea 2', NULL, 11.051170, -74.853327, '2026-11-08T13:56:44Z'),
    ('2026-11-08', '9vo', NULL, NULL, 11.051134, -74.853348, '2026-11-08T13:57:51Z'),
    ('2026-11-08', '10mo', 'Linea 3', NULL, 11.051158, -74.853387, '2026-11-08T14:01:23Z'),
    ('2026-11-08', '11', 'Linea 3', NULL, 11.051164, -74.853426, '2026-11-08T14:06:03Z'),
    ('2026-11-08', '12', 'Linea 3', NULL, 11.051163, -74.853472, '2026-11-08T14:07:10Z'),
    ('2026-11-08', '13', 'Linea 4', NULL, 11.051121, -74.853465, '2026-11-08T14:08:35Z'),
    ('2026-11-08', '14', 'Linea 4', NULL, 11.051082, -74.853501, '2026-11-08T14:10:18Z'),
    ('2026-11-08', '15', 'Linea 4', NULL, 11.051477, -74.853305, '2026-11-08T14:22:54Z'),
    ('2026-11-08', '16', 'Linea 4', NULL, 11.051498, -74.853349, '2026-11-08T14:23:48Z'),
    ('2026-11-08', '17', 'Linea 5', NULL, 11.051504, -74.853393, '2026-11-08T14:24:53Z'),
    ('2026-11-08', '18', 'Linea 5', NULL, 11.051509, -74.853437, '2026-11-08T14:25:45Z'),
    ('2026-11-08', '19', 'Linea 5', NULL, 11.051553, -74.853422, '2026-11-08T14:27:53Z'),
    ('2026-11-08', '20', 'Linea 5', NULL, 11.051599, -74.853418, '2026-11-08T14:28:38Z')
ON CONFLICT (campana, nombre) DO NOTHING;

COMMIT;
