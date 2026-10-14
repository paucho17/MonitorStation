-- =====================================================================
-- IoT-Mangrove: datos iniciales (catalogos, modulos, roles y permisos)
-- El usuario administrador NO se inserta aquí: la API lo crea al iniciar
-- a partir de las variables de entorno ADMIN_USERNAME / ADMIN_PASSWORD,
-- de modo que ninguna contraseña queda escrita en el repositorio.
-- =====================================================================

BEGIN;

-- Roles ----------------------------------------------------------------
INSERT INTO rol (nombre, descripcion) VALUES
    ('admin',    'Administrador: acceso total al sistema'),
    ('operador', 'Operador: gestiona la infraestructura y atiende alertas'),
    ('consulta', 'Consulta: solo lectura del dashboard y del historial');

-- Modulos (nombre = clave de permiso; ruta = recurso en la API) --------
INSERT INTO modulo (nombre, ruta, descripcion) VALUES
    ('usuarios',   '/api/usuarios',   'Gestión de usuarios'),
    ('roles',      '/api/roles',      'Gestión de roles'),
    ('modulos',    '/api/modulos',    'Gestión de modulos del sistema'),
    ('permisos',   '/api/permisos',   'Permisos de cada rol sobre cada modulo'),
    ('zonas',      '/api/zonas',      'Zonas de manglar monitoreadas'),
    ('gateways',   '/api/gateways',   'Gateways LoRa'),
    ('tipos-nodo', '/api/tipos-nodo', 'Categorías de nodo'),
    ('nodos',      '/api/nodos',      'Nodos emisores LoRa'),
    ('unidades',   '/api/unidades',   'Unidades de medida'),
    ('variables',  '/api/variables',  'Variables ambientales'),
    ('sensores',   '/api/sensores',   'Sensores instalados en los nodos'),
    ('umbrales',   '/api/umbrales',   'Umbrales de alerta por variable'),
    ('lecturas',   '/api/lecturas',   'Tramas recibidas de los nodos'),
    ('mediciones', '/api/mediciones', 'Valores medidos'),
    ('alertas',    '/api/alertas',    'Alertas generadas'),
    ('dashboard',  '/api/dashboard',  'Últimos datos recibidos'),
    ('historial',  '/api/historial',  'Datos históricos con filtros');

-- Permisos (moduloxrol) -------------------------------------------------
-- admin: todo
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear, puede_editar, puede_eliminar)
SELECT r.id, m.id, TRUE, TRUE, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'admin';

-- operador: CRUD sobre la operación; lectura sobre catalogos y datos;
-- sin acceso a usuarios, roles, modulos, permisos ni gateways
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear, puede_editar, puede_eliminar)
SELECT r.id, m.id, TRUE, TRUE, TRUE, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'operador'
  AND m.nombre IN ('zonas', 'nodos', 'sensores', 'umbrales');

INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer, puede_crear, puede_editar, puede_eliminar)
SELECT r.id, m.id, TRUE, FALSE, TRUE, FALSE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'operador' AND m.nombre = 'alertas';

INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer)
SELECT r.id, m.id, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'operador'
  AND m.nombre IN ('tipos-nodo', 'unidades', 'variables', 'lecturas',
                   'mediciones', 'dashboard', 'historial');

-- consulta: solo lectura de datos y catalogos públicos
INSERT INTO modulo_rol (rol_id, modulo_id, puede_leer)
SELECT r.id, m.id, TRUE
FROM rol r CROSS JOIN modulo m
WHERE r.nombre = 'consulta'
  AND m.nombre IN ('zonas', 'tipos-nodo', 'nodos', 'unidades', 'variables',
                   'sensores', 'umbrales', 'lecturas', 'mediciones',
                   'alertas', 'dashboard', 'historial');

-- Tipos de nodo (categorías de la trama LoRa) ---------------------------
INSERT INTO tipo_nodo (codigo, nombre, descripcion) VALUES
    ('WATER', 'Calidad de agua',      'pH, turbidez, TDS y nivel de agua'),
    ('AMB',   'Ambiente',             'Temperatura, humedad, presión y calidad de aire'),
    ('SOIL',  'Suelo',                'Humedad del suelo');

-- Unidades de medida ----------------------------------------------------
INSERT INTO unidad_medida (simbolo, nombre) VALUES
    ('pH',  'Unidades de pH'),
    ('NTU', 'Unidades nefelometricas de turbidez'),
    ('ppm', 'Partes por millon'),
    ('ppb', 'Partes por billon'),
    ('C',   'Grados Celsius'),
    ('%',   'Porcentaje'),
    ('hPa', 'Hectopascales'),
    ('bin', 'Estado binario (0 = bajo, 1 = alto)');

-- Variables --------------------------------------------------------------
INSERT INTO variable (codigo, nombre, descripcion, unidad_id, tipo_nodo_id, rango_min, rango_max)
SELECT v.codigo, v.nombre, v.descripcion,
       (SELECT id FROM unidad_medida WHERE simbolo = v.unidad),
       (SELECT id FROM tipo_nodo     WHERE codigo  = v.tipo),
       v.rmin, v.rmax
FROM (VALUES
    ('ph',            'pH del agua',            'Acidez o alcalinidad del agua',                 'pH',  'WATER',   0,    14),
    ('turbidity',     'Turbidez',               'Material en suspension en el agua',             'NTU', 'WATER',   0,  3000),
    ('tds',           'Solidos disueltos (TDS)', 'Solidos totales disueltos en el agua',         'ppm', 'WATER',   0,  5000),
    ('water_level',   'Nivel de agua',          'Flotador magnetico: 1 = nivel alcanzado',       'bin', 'WATER',   0,     1),
    ('temperature',   'Temperatura ambiente',   'Temperatura del aire (BME280)',                 'C',   'AMB',   -40,    85),
    ('humidity',      'Humedad relativa',       'Humedad relativa del aire (BME280)',            '%',   'AMB',     0,   100),
    ('pressure',      'Presión atmosférica',    'Presión barometrica (BME280)',                  'hPa', 'AMB',   300,  1100),
    ('eco2',          'eCO2',                   'Dioxido de carbono equivalente (SGP30)',        'ppm', 'AMB',   400, 60000),
    ('tvoc',          'TVOC',                   'Compuestos orgánicos volátiles totales (SGP30)','ppb', 'AMB',     0, 60000),
    ('soil_humidity', 'Humedad del suelo',      'Sensor capacitivo v1.2',                        '%',   'SOIL',    0,   100)
) AS v (codigo, nombre, descripcion, unidad, tipo, rmin, rmax);

-- Umbrales de referencia (ajustables desde la API segun la bibliografia) --
INSERT INTO umbral (variable_id, nivel, minimo, maximo, mensaje)
SELECT (SELECT id FROM variable WHERE codigo = u.codigo), u.nivel, u.minimo, u.maximo, u.mensaje
FROM (VALUES
    ('ph',            'ADVERTENCIA', 6.5,  8.5,  'pH fuera del rango recomendado para agua de manglar'),
    ('ph',            'CRITICO',     6.0,  9.0,  'pH en rango crítico para la fauna acuatica'),
    ('turbidity',     'ADVERTENCIA', NULL, 50,   'Turbidez elevada'),
    ('turbidity',     'CRITICO',     NULL, 100,  'Turbidez crítica'),
    ('tds',           'ADVERTENCIA', NULL, 1000, 'Solidos disueltos elevados'),
    ('tds',           'CRITICO',     NULL, 2000, 'Solidos disueltos críticos'),
    ('temperature',   'ADVERTENCIA', 15,   35,   'Temperatura ambiente fuera del rango habitual'),
    ('temperature',   'CRITICO',     10,   40,   'Temperatura ambiente extrema'),
    ('humidity',      'ADVERTENCIA', 30,   90,   'Humedad relativa fuera del rango habitual'),
    ('humidity',      'CRITICO',     15,   98,   'Humedad relativa extrema'),
    ('pressure',      'ADVERTENCIA', 980,  1030, 'Presión atmosférica atipica'),
    ('pressure',      'CRITICO',     950,  1050, 'Presión atmosférica extrema'),
    ('eco2',          'ADVERTENCIA', NULL, 1000, 'eCO2 elevado'),
    ('eco2',          'CRITICO',     NULL, 2000, 'eCO2 crítico'),
    ('tvoc',          'ADVERTENCIA', NULL, 220,  'TVOC elevado'),
    ('tvoc',          'CRITICO',     NULL, 660,  'TVOC crítico'),
    ('soil_humidity', 'ADVERTENCIA', 20,   90,   'Humedad del suelo fuera del rango habitual'),
    ('soil_humidity', 'CRITICO',     10,   98,   'Humedad del suelo extrema')
) AS u (codigo, nivel, minimo, maximo, mensaje);

-- Zona de ejemplo ----------------------------------------------------------
INSERT INTO zona_manglar (nombre, descripcion, municipio)
VALUES ('Manglar piloto', 'Zona inicial de pruebas del prototipo', NULL);

COMMIT;
