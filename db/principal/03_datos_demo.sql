-- =====================================================================
-- IoT-Mangrove: datos de demostracion
-- Generado a partir del volcado historico (sensor_data, 54 filas de prueba)
-- y convertido al modelo normalizado lectura / medicion.
-- Las columnas del MQ-135 (descartado del hardware) no se migran.
-- Es opcional: omitir este archivo para iniciar con la base vacia.
-- =====================================================================

BEGIN;

-- El hash de la clave se reemplaza al iniciar la API con GATEWAY_API_KEY
INSERT INTO gateway (codigo, nombre, zona_id, api_key_hash)
VALUES ('0XDD', 'Gateway principal', (SELECT id FROM zona_manglar WHERE nombre = 'Manglar piloto'),
        encode(sha256('clave-provisional-reemplazada-por-la-api'::bytea), 'hex'));

INSERT INTO nodo (codigo, nombre, tipo_nodo_id, zona_id, gateway_id) VALUES
    ('0XAA', 'Nodo de agua',    (SELECT id FROM tipo_nodo WHERE codigo='WATER'), (SELECT id FROM zona_manglar WHERE nombre='Manglar piloto'), (SELECT id FROM gateway WHERE codigo='0XDD')),
    ('0XBB', 'Nodo de ambiente',(SELECT id FROM tipo_nodo WHERE codigo='AMB'),   (SELECT id FROM zona_manglar WHERE nombre='Manglar piloto'), (SELECT id FROM gateway WHERE codigo='0XDD')),
    ('0XCC', 'Nodo de suelo',   (SELECT id FROM tipo_nodo WHERE codigo='SOIL'),  (SELECT id FROM zona_manglar WHERE nombre='Manglar piloto'), (SELECT id FROM gateway WHERE codigo='0XDD'));

INSERT INTO sensor (nodo_id, variable_id, modelo)
SELECT n.id, v.id, s.modelo
FROM (VALUES
    ('0XAA','ph','Modulo pH'), ('0XAA','turbidity','Modulo de turbidez'),
    ('0XBB','temperature','BME280'), ('0XBB','humidity','BME280'),
    ('0XCC','soil_humidity','Capacitivo v1.2')
) AS s (nodo, var, modelo)
JOIN nodo n ON n.codigo = s.nodo
JOIN variable v ON v.codigo = s.var;

INSERT INTO lectura (id, nodo_id, gateway_id, rssi, snr, fecha_recepcion)
SELECT l.id, n.id, n.gateway_id, l.rssi, l.snr, l.fecha::timestamptz
FROM (VALUES
    (1, '0XAA', -116, 6.3, '2025-12-02 20:33:47+00'),
    (2, '0XCC', -103, 0.6, '2025-12-02 20:33:50+00'),
    (3, '0XBB', -116, -2.1, '2025-12-02 20:33:53+00'),
    (4, '0XAA', -93, 0.2, '2025-12-02 20:33:56+00'),
    (5, '0XBB', -106, 12.9, '2025-12-02 20:33:59+00'),
    (6, '0XBB', -102, 0.8, '2025-12-02 20:34:02+00'),
    (7, '0XCC', -88, 13.7, '2025-12-02 20:34:05+00'),
    (8, '0XCC', -110, 5.8, '2025-12-03 00:00:57+00'),
    (9, '0XAA', -101, 2.8, '2025-12-03 00:00:59+00'),
    (10, '0XBB', -78, 12.5, '2025-12-03 00:01:04+00'),
    (11, '0XCC', -85, 4.4, '2025-12-03 00:01:09+00'),
    (12, '0XAA', -110, -3.2, '2025-12-03 00:01:14+00'),
    (13, '0XBB', -89, 3.7, '2025-12-03 00:01:19+00'),
    (14, '0XCC', -106, 7.8, '2025-12-03 00:01:24+00'),
    (15, '0XAA', -95, 0.9, '2025-12-03 00:01:30+00'),
    (16, '0XBB', -79, -3, '2025-12-03 00:01:34+00'),
    (17, '0XCC', -89, 3.1, '2025-12-03 00:01:39+00'),
    (18, '0XAA', -75, 4.4, '2025-12-03 00:01:44+00'),
    (19, '0XBB', -115, 7.1, '2025-12-03 00:01:49+00'),
    (20, '0XCC', -91, 14.5, '2025-12-03 00:01:54+00'),
    (21, '0XAA', -85, 5.4, '2025-12-03 00:01:59+00'),
    (22, '0XBB', -104, 2.4, '2025-12-03 00:02:04+00'),
    (23, '0XCC', -89, 8.4, '2025-12-03 00:02:09+00'),
    (24, '0XAA', -83, -0.6, '2025-12-03 00:02:14+00'),
    (25, '0XBB', -98, 3.7, '2025-12-03 00:02:19+00'),
    (26, '0XCC', -106, 10.6, '2025-12-03 00:02:24+00'),
    (27, '0XAA', -74, 3.4, '2025-12-03 00:02:29+00'),
    (28, '0XBB', -90, 14.6, '2025-12-03 00:02:33+00'),
    (29, '0XCC', -85, 9.7, '2025-12-03 00:02:39+00'),
    (30, '0XAA', -107, 6.3, '2025-12-03 00:02:44+00'),
    (31, '0XBB', -82, 0.2, '2025-12-03 00:02:48+00'),
    (32, '0XCC', -92, 8.1, '2025-12-03 00:02:54+00'),
    (33, '0XAA', -117, 7.2, '2025-12-03 00:02:59+00'),
    (34, '0XBB', -117, -3.2, '2025-12-03 00:03:04+00'),
    (35, '0XCC', -96, 0.7, '2025-12-03 00:03:09+00'),
    (36, '0XAA', -113, 1.1, '2025-12-03 00:03:14+00'),
    (37, '0XBB', -113, 9.3, '2025-12-03 00:03:18+00'),
    (38, '0XCC', -99, 3, '2025-12-03 00:03:24+00'),
    (39, '0XAA', -83, -3.2, '2025-12-03 00:03:29+00'),
    (40, '0XBB', -88, 1.5, '2025-12-03 00:03:34+00'),
    (41, '0XCC', -86, -0.5, '2025-12-03 00:03:39+00'),
    (42, '0XAA', -107, -4.8, '2025-12-03 00:03:44+00'),
    (43, '0XBB', -116, 6.1, '2025-12-03 00:03:49+00'),
    (44, '0XCC', -110, 5.5, '2025-12-03 00:03:54+00'),
    (45, '0XAA', -83, 13.9, '2025-12-03 00:03:59+00'),
    (46, '0XBB', -89, 5.2, '2025-12-03 00:04:04+00'),
    (47, '0XCC', -118, 0.7, '2025-12-03 00:04:09+00'),
    (48, '0XAA', -71, 14.1, '2025-12-03 00:04:14+00'),
    (49, '0XAA', -95, 3.2, '2025-12-08 02:57:38+00'),
    (50, '0XBB', -88, 5.7, '2025-12-08 02:57:38+00'),
    (51, '0XCC', -102, 4.1, '2025-12-08 02:57:38+00'),
    (52, '0XBB', -91, 6.2, '2025-12-08 02:57:38+00'),
    (53, '0XAA', -87, 7.8, '2025-12-08 02:57:38+00'),
    (54, '0XBB', -93, 5.5, '2025-12-08 02:57:38+00')
) AS l (id, nodo, rssi, snr, fecha)
JOIN nodo n ON n.codigo = l.nodo;

INSERT INTO medicion (lectura_id, variable_id, valor)
SELECT m.lectura_id, v.id, m.valor
FROM (VALUES
    (1, 'ph', 7.68),
    (1, 'turbidity', 19.8),
    (2, 'soil_humidity', 63),
    (3, 'humidity', 54),
    (3, 'temperature', 29.7),
    (4, 'ph', 6.43),
    (4, 'turbidity', 23.76),
    (5, 'humidity', 75.4),
    (5, 'temperature', 33.4),
    (6, 'humidity', 41.3),
    (6, 'temperature', 32),
    (7, 'soil_humidity', 22),
    (8, 'soil_humidity', 60),
    (9, 'ph', 7.69),
    (9, 'turbidity', 57.53),
    (10, 'humidity', 79.5),
    (10, 'temperature', 34.6),
    (11, 'soil_humidity', 78),
    (12, 'ph', 6.51),
    (12, 'turbidity', 51.68),
    (13, 'humidity', 74.9),
    (13, 'temperature', 33),
    (14, 'soil_humidity', 73),
    (15, 'ph', 7.76),
    (15, 'turbidity', 23.31),
    (16, 'humidity', 43.5),
    (16, 'temperature', 21.5),
    (17, 'soil_humidity', 71),
    (18, 'ph', 8.32),
    (18, 'turbidity', 9.79),
    (19, 'humidity', 44.9),
    (19, 'temperature', 23.2),
    (20, 'soil_humidity', 79),
    (21, 'ph', 6.36),
    (21, 'turbidity', 79.06),
    (22, 'humidity', 54.8),
    (22, 'temperature', 21.7),
    (23, 'soil_humidity', 81),
    (24, 'ph', 6.11),
    (24, 'turbidity', 4.12),
    (25, 'humidity', 41.8),
    (25, 'temperature', 32.8),
    (26, 'soil_humidity', 39),
    (27, 'ph', 7.79),
    (27, 'turbidity', 29.91),
    (28, 'humidity', 55.8),
    (28, 'temperature', 18),
    (29, 'soil_humidity', 48),
    (30, 'ph', 6.95),
    (30, 'turbidity', 92.1),
    (31, 'humidity', 77.1),
    (31, 'temperature', 23.4),
    (32, 'soil_humidity', 50),
    (33, 'ph', 7.29),
    (33, 'turbidity', 60.48),
    (34, 'humidity', 49.1),
    (34, 'temperature', 34.1),
    (35, 'soil_humidity', 21),
    (36, 'ph', 6.74),
    (36, 'turbidity', 80.43),
    (37, 'humidity', 72.5),
    (37, 'temperature', 24.1),
    (38, 'soil_humidity', 23),
    (39, 'ph', 6.2),
    (39, 'turbidity', 77.53),
    (40, 'humidity', 50.2),
    (40, 'temperature', 32.1),
    (41, 'soil_humidity', 59),
    (42, 'ph', 7.37),
    (42, 'turbidity', 69.94),
    (43, 'humidity', 75.6),
    (43, 'temperature', 29.7),
    (44, 'soil_humidity', 54),
    (45, 'ph', 8.39),
    (45, 'turbidity', 57.5),
    (46, 'humidity', 65.8),
    (46, 'temperature', 23.3),
    (47, 'soil_humidity', 45),
    (48, 'ph', 6.94),
    (48, 'turbidity', 64.86),
    (49, 'ph', 7.45),
    (49, 'turbidity', 45.32),
    (50, 'humidity', 65.5),
    (50, 'temperature', 28.3),
    (51, 'soil_humidity', 68),
    (52, 'humidity', 72.8),
    (52, 'temperature', 31.5),
    (53, 'ph', 6.89),
    (53, 'turbidity', 38.67),
    (54, 'humidity', 68.2),
    (54, 'temperature', 29.8)
) AS m (lectura_id, var, valor)
JOIN variable v ON v.codigo = m.var;

SELECT setval(pg_get_serial_sequence('lectura','id'), (SELECT MAX(id) FROM lectura));

COMMIT;
