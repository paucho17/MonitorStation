-- =====================================================================
-- IoT-Mangrove: migracion 05, notificaciones de alertas y rol "vivero"
--
--   * usuario.notificar_alertas / notificar_nivel : preferencia por usuario.
--   * notificacion : bitacora de avisos enviados por alerta (canal, destino,
--                    resultado). Un canal nuevo (WhatsApp, SMS) es un valor
--                    nuevo de "canal"; no cambia el esquema.
--   * rol "vivero" : opera el riego y atiende alertas, sin administrar
--                    la infraestructura del manglar.
--
-- Idempotente: puede ejecutarse varias veces (scripts/migrar_db.sh).
-- Requiere las migraciones 01 a 04.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Preferencias de aviso por usuario
-- ---------------------------------------------------------------------
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS notificar_alertas BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS notificar_nivel VARCHAR(15) NOT NULL DEFAULT 'CRITICO';
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_usuario_notificar_nivel') THEN
        ALTER TABLE usuario ADD CONSTRAINT chk_usuario_notificar_nivel
            CHECK (notificar_nivel IN ('ADVERTENCIA', 'CRITICO'));
    END IF;
END $$;

-- ---------------------------------------------------------------------
-- Bitacora de notificaciones
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notificacion (
    id           SERIAL PRIMARY KEY,
    alerta_id    INTEGER      NOT NULL REFERENCES alerta (id),
    usuario_id   INTEGER      NOT NULL REFERENCES usuario (id),
    canal        VARCHAR(20)  NOT NULL DEFAULT 'EMAIL',
    destino      VARCHAR(150),
    situacion    VARCHAR(12)  NOT NULL DEFAULT 'PENDIENTE'
                 CHECK (situacion IN ('PENDIENTE', 'ENVIADA', 'FALLIDA', 'OMITIDA')),
    detalle      VARCHAR(255),
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    creado       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (alerta_id, usuario_id, canal)
);
CREATE INDEX IF NOT EXISTS idx_notificacion_usuario ON notificacion (usuario_id, canal, situacion, creado);

-- Trigger de auditoria (mismo que el resto de las tablas)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_actualizado' AND tgrelid = 'notificacion'::regclass
    ) THEN
        CREATE TRIGGER trg_actualizado BEFORE UPDATE ON notificacion
            FOR EACH ROW EXECUTE FUNCTION fn_set_actualizado();
    END IF;
END $$;

-- ---------------------------------------------------------------------
-- Modulo de permisos y rol "vivero"
-- ---------------------------------------------------------------------
INSERT INTO modulo (nombre, ruta, descripcion) VALUES
    ('notificaciones', '/api/notificaciones', 'Bitacora de avisos de alertas y envio de prueba')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO rol (nombre, descripcion) VALUES
    ('vivero', 'Vivero: opera el riego y atiende alertas del vivero')
ON CONFLICT (nombre) DO NOTHING;

-- admin ya tiene acceso implicito; se registra el modulo nuevo por coherencia
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear, puede_editar, puede_eliminar)
SELECT r.id, m.id, TRUE, TRUE, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'admin' AND m.nombre = 'notificaciones'
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

-- operador: lee la bitacora y puede enviar la prueba
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear)
SELECT r.id, m.id, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'operador' AND m.nombre = 'notificaciones'
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

-- vivero: opera riego y programas, atiende alertas, lee datos y catalogos
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear, puede_editar, puede_eliminar)
SELECT r.id, m.id, TRUE, TRUE, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'vivero' AND m.nombre IN ('riego', 'zonas-riego', 'actuadores', 'programas-riego')
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_editar)
SELECT r.id, m.id, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'vivero' AND m.nombre = 'alertas'
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer)
SELECT r.id, m.id, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'vivero'
  AND m.nombre IN ('dashboard', 'historial', 'ambitos', 'comandos-riego', 'eventos-riego',
                   'nodos', 'variables', 'unidades', 'umbrales', 'zonas')
ON CONFLICT (rol_id, modulo_id) DO NOTHING;

COMMIT;
