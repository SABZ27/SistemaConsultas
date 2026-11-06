-- ============================================================================
-- 06_datos_demo_mysql.sql — datos de demostración (Fase 6 · Bloque B)
-- ============================================================================
-- MySQL 8.0 / InnoDB / utf8mb4 (Aiven). Ejecutar DESPUES de
-- 03_mysql_schema.sql y 04_mysql_seed.sql. Es IDEMPOTENTE (INSERT IGNORE).
--
-- * festivos: festivos REALES de Colombia 2026 y 2027 (19 por anio), con la
--   corrección Ley Emiliani ya aplicada. Son datos reales, no sintéticos.
-- * servicios_externos: 2 proveedores reales + 8 filas de DEMOSTRACIÓN
--   inactivas (estado = 0) y marcadas en la descripción.
-- * consultas_servicio_externo y correos_enviados: NO se generaron ejecutando
--   el flujo real en local (no hay proveedor ni SMTP locales). Son filas
--   SINTÉTICAS marcadas explícitamente con el prefijo [DEMO] en detalle /
--   respuesta_proveedor y con exito = 0, codigo_http NULL y estado_envio
--   FALLIDO. Nunca se presentan como llamadas ni envíos reales.
-- Sin secretos, contraseñas ni correos personales.
-- ============================================================================


-- Proveedores reales (coinciden con 04) + 8 servicios de demostracion
-- inactivos con nombres realistas en español de Colombia (no genericos).

INSERT IGNORE INTO servicios_externos (id, nombre, url_base, descripcion, estado) VALUES
(900, 'Nager.Date', 'https://date.nager.at/api/v4', 'API pública de festivos por país', 1),
(901, 'Brevo', 'https://api.brevo.com/v3', 'API de correo transaccional', 1),
(910, '[DEMO] Simulador de Calendario de Festivos', 'https://demo.ejemplo.edu.co/servicios/1', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0),
(911, '[DEMO] Simulador de Correo Institucional', 'https://demo.ejemplo.edu.co/servicios/2', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0),
(912, '[DEMO] Consulta de Calendario Académico', 'https://demo.ejemplo.edu.co/servicios/3', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0),
(913, '[DEMO] Consulta de Matrícula Estudiantil', 'https://demo.ejemplo.edu.co/servicios/4', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0),
(914, '[DEMO] Consulta de Horarios Institucionales', 'https://demo.ejemplo.edu.co/servicios/5', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0),
(915, '[DEMO] Consulta de Catálogo Bibliográfico', 'https://demo.ejemplo.edu.co/servicios/6', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0),
(916, '[DEMO] Consulta de Bienestar Universitario', 'https://demo.ejemplo.edu.co/servicios/7', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0),
(917, '[DEMO] Consulta de Reportes de Gestión', 'https://demo.ejemplo.edu.co/servicios/8', '[DEMO] Servicio de demostración, inactivo. No se usa en ningún flujo real.', 0);

-- Festivos reales de Colombia 2026-2027 (38), con Ley Emiliani.

INSERT IGNORE INTO festivos (id, servicio_id, consulta_servicio_id, fecha, pais, nombre, anio, estado) VALUES
(1000, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-01-01', 'CO', 'Año Nuevo', 2026, 1),
(1001, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-01-12', 'CO', 'Día de los Reyes Magos', 2026, 1),
(1002, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-03-23', 'CO', 'Día de San José', 2026, 1),
(1003, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-04-02', 'CO', 'Jueves Santo', 2026, 1),
(1004, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-04-03', 'CO', 'Viernes Santo', 2026, 1),
(1005, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-05-01', 'CO', 'Día del Trabajo', 2026, 1),
(1006, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-05-18', 'CO', 'Ascensión del Señor', 2026, 1),
(1007, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-06-08', 'CO', 'Corpus Christi', 2026, 1),
(1008, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-06-15', 'CO', 'Sagrado Corazón', 2026, 1),
(1009, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-06-29', 'CO', 'San Pedro y San Pablo', 2026, 1),
(1010, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-07-13', 'CO', 'Virgen de Chiquinquirá', 2026, 1),
(1011, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-07-20', 'CO', 'Día de la Independencia', 2026, 1),
(1012, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-08-07', 'CO', 'Batalla de Boyacá', 2026, 1),
(1013, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-08-17', 'CO', 'Asunción de la Virgen', 2026, 1),
(1014, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-10-12', 'CO', 'Día de la Diversidad Étnica y Cultural', 2026, 1),
(1015, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-11-02', 'CO', 'Todos los Santos', 2026, 1),
(1016, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-11-16', 'CO', 'Independencia de Cartagena', 2026, 1),
(1017, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-12-08', 'CO', 'Inmaculada Concepción', 2026, 1),
(1018, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2026-12-25', 'CO', 'Navidad', 2026, 1),
(1019, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-01-01', 'CO', 'Año Nuevo', 2027, 1),
(1020, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-01-11', 'CO', 'Día de los Reyes Magos', 2027, 1),
(1021, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-03-22', 'CO', 'Día de San José', 2027, 1),
(1022, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-03-25', 'CO', 'Jueves Santo', 2027, 1),
(1023, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-03-26', 'CO', 'Viernes Santo', 2027, 1),
(1024, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-05-01', 'CO', 'Día del Trabajo', 2027, 1),
(1025, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-05-10', 'CO', 'Ascensión del Señor', 2027, 1),
(1026, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-05-31', 'CO', 'Corpus Christi', 2027, 1),
(1027, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-06-07', 'CO', 'Sagrado Corazón', 2027, 1),
(1028, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-07-05', 'CO', 'San Pedro y San Pablo', 2027, 1),
(1029, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-07-12', 'CO', 'Virgen de Chiquinquirá', 2027, 1),
(1030, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-07-20', 'CO', 'Día de la Independencia', 2027, 1),
(1031, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-08-07', 'CO', 'Batalla de Boyacá', 2027, 1),
(1032, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-08-16', 'CO', 'Asunción de la Virgen', 2027, 1),
(1033, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-10-18', 'CO', 'Día de la Diversidad Étnica y Cultural', 2027, 1),
(1034, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-11-01', 'CO', 'Todos los Santos', 2027, 1),
(1035, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-11-15', 'CO', 'Independencia de Cartagena', 2027, 1),
(1036, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-12-08', 'CO', 'Inmaculada Concepción', 2027, 1),
(1037, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), NULL, '2027-12-25', 'CO', 'Navidad', 2027, 1);

-- [DEMO] Bitacoras sinteticas: NO son llamadas reales.

INSERT IGNORE INTO consultas_servicio_externo (id, servicio_id, referencia, endpoint, codigo_http, exito, duracion_ms, detalle, estado) VALUES
(2000, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0001', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2001, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0002', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2002, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0003', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2003, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0004', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2004, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0005', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2005, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0006', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2006, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0007', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2007, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0008', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2008, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0009', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2009, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0010', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2010, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0011', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2011, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0012', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2012, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0013', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2013, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0014', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2014, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0015', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2015, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0016', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2016, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0017', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2017, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0018', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2018, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0019', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1),
(2019, (SELECT id FROM servicios_externos WHERE nombre = 'Nager.Date' ORDER BY id LIMIT 1), 'DEMO-CONSULTA-0020', '[DEMO] sin endpoint real', NULL, 0, NULL, '[DEMO] Registro sintético de demostración. No corresponde a una llamada real.', 1);

-- [DEMO] Correos sinteticos: NO son envios reales.

INSERT IGNORE INTO correos_enviados (id, servicio_id, consulta_servicio_id, destinatario, asunto, estado_envio, respuesta_proveedor, estado) VALUES
(3000, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2000, 'estudiante01@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3001, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2001, 'estudiante02@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3002, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2002, 'estudiante03@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3003, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2003, 'estudiante04@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3004, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2004, 'estudiante05@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3005, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2005, 'estudiante06@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3006, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2006, 'estudiante07@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3007, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2007, 'estudiante08@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3008, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2008, 'estudiante09@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3009, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2009, 'estudiante10@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3010, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2010, 'estudiante11@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3011, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2011, 'estudiante12@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3012, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2012, 'estudiante13@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3013, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2013, 'estudiante14@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3014, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2014, 'estudiante15@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3015, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2015, 'estudiante16@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3016, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2016, 'estudiante17@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3017, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2017, 'estudiante18@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3018, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2018, 'estudiante19@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1),
(3019, (SELECT id FROM servicios_externos WHERE nombre = 'Brevo' ORDER BY id LIMIT 1), 2019, 'estudiante20@demo.ejemplo.edu.co', '[DEMO] Correo de demostración', 'FALLIDO', '[DEMO] Sin envío real. Fila sintética de demostración.', 1);
