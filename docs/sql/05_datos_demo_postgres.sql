-- ============================================================================
-- 05_datos_demo_postgres.sql — datos de demostración (Fase 6 · Bloque B)
-- ============================================================================
-- AUDITADO para PostgreSQL 15+ REAL (Neon). Ejecutar DESPUES de
-- 01_postgres_schema.sql y 02_postgres_seed.sql. NO es un script de SQLite.
--
-- * Transaccion atomica: BEGIN ... COMMIT. Si algo falla no queda siembra
--   parcial.
-- * Se insertan IDs explicitos en rango alto; al FINAL se resincronizan las
--   19 secuencias SERIAL con setval(pg_get_serial_sequence(tabla,'id'), ...)
--   para que los proximos INSERT de la API no choquen con la PK.
-- * Sin sintaxis exclusiva de SQLite: sin INSERT OR IGNORE, sin AUTOINCREMENT,
--   sin PRAGMA, sin strftime(). Booleanos TRUE/FALSE y literales
--   'YYYY-MM-DD', 'HH:MM', 'YYYY-MM-DD HH:MM:SS' que PostgreSQL convierte
--   implicitamente al tipo DATE / TIME / TIMESTAMP WITHOUT TIME ZONE de cada
--   columna. Subconsultas escalares y CURRENT_TIMESTAMP son PostgreSQL puro.
-- * ON CONFLICT DO NOTHING SIN objetivo: es el unico que cubre a la vez la PK
--   (IDs explicitos), los UNIQUE simples y los 16 indices unicos PARCIALES
--   WHERE estado de 01 (ver comentario por tabla). Un objetivo explicito
--   "ON CONFLICT (nombre) WHERE estado" NO cubre las filas inactivas ni los
--   conflictos de PK y romperia la idempotencia en la segunda ejecucion.
-- * Idempotente: ejecutarlo dos veces no duplica filas (todas las filas
--   chocan con su PK) y deja las secuencias en el mismo valor.
-- * Colisiones con datos de prueba de Neon evitadas POR CONSTRUCCION: correos
--   en subdominio reservado @demo.ejemplo.edu.co, identificaciones con prefijo
--   9 (rango 90000000xx) y nombres de programas/asignaturas con prefijo
--   [DEMO]. No se consulto Neon (esta prohibido en este trabajo).
-- * Solo datos de demostracion. La contrasena de los usuarios demo NO aparece:
--   unicamente su hash bcrypt, generado desde DEMO_PASSWORD.
-- ============================================================================

BEGIN;


-- Roles: 3 canonicos (coinciden con 02) + 7 entradas de catalogo de
-- demostracion inactivas. Idempotente: si 02 ya los inserto, se omiten.

-- Conflictos cubiertos (01): PK(id) y uq_roles_nombre_estado (parcial WHERE estado).
INSERT INTO roles (id, nombre, descripcion, estado, creado, actualizado) VALUES
(1900, 'ADMINISTRADOR', NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1901, 'DOCENTE', NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1902, 'ESTUDIANTE', NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1000, 'Decano de Facultad', NULL, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1001, 'Coordinador de Programa Académico', NULL, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1002, 'Secretario Académico', NULL, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1003, 'Monitor Académico', NULL, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1004, 'Coordinador de Biblioteca', NULL, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1005, 'Coordinador de Bienestar Universitario', NULL, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1006, 'Coordinador de Evaluación Docente', NULL, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Modulos del sistema de demostracion (10).

-- Conflictos cubiertos (01): PK(id) y uq_modulos_sistema_nombre_estado (parcial WHERE estado).
INSERT INTO modulos_sistema (id, nombre, descripcion, ruta, icono, estado, creado, actualizado) VALUES
(1100, 'Reportes de Desempeño Académico', 'Indicadores de rendimiento por programa', '/reportes-desempeno', 'assessment', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1101, 'Consulta de Horarios', 'Horarios de clase y asesorías', '/consulta-horarios', 'schedule', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1102, 'Gestión de Matrícula', 'Matrícula académica y financiera', '/gestion-matricula', 'how_to_reg', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1103, 'Catálogo Bibliográfico', 'Consulta del catálogo de la biblioteca', '/catalogo-bibliografico', 'local_library', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1104, 'Programas de Bienestar', 'Oferta de bienestar universitario', '/programas-bienestar', 'volunteer_activism', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1105, 'Encuesta de Evaluación Docente', 'Evaluación del desempeño docente', '/encuesta-evaluacion', 'fact_check', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1106, 'Malla Curricular', 'Consulta de planes de estudio', '/malla-curricular', 'account_tree', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1107, 'Seguimiento Académico', 'Seguimiento al rendimiento estudiantil', '/seguimiento-academico', 'trending_up', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1108, 'Encuestas Institucionales', 'Encuestas de percepción institucional', '/encuestas-institucionales', 'poll', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1109, 'Tablero de Indicadores', 'Indicadores de gestión para la dirección', '/tablero-indicadores', 'campaign', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Matriz modulo x rol de demostracion (10), solo roles de catalogo.

-- Conflictos cubiertos (01): PK(id) y uq_modulos_x_rol_rol_modulo (parcial WHERE estado).
INSERT INTO modulos_x_rol (id, rol_id, modulo_id, estado, creado, actualizado) VALUES
(1200, 1000, 1100, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1201, 1001, 1101, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1202, 1002, 1102, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1203, 1003, 1103, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1204, 1004, 1104, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1205, 1005, 1105, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1206, 1006, 1106, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1207, 1000, 1107, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1208, 1001, 1108, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1209, 1002, 1109, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Tipos de documento de demostracion (6).

-- Conflictos cubiertos (01): PK(id), uq_tipos_documento_nombre_estado y uq_tipos_documento_sigla_estado (parciales WHERE estado).
INSERT INTO tipos_documento (id, nombre, sigla, estado, creado, actualizado) VALUES
(1300, 'Registro Civil de Nacimiento', 'RC', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1301, 'Cédula de Ciudadanía Digital', 'CCD', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1302, 'Pasaporte Diplomático', 'PD', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1303, 'Permiso Especial de Permanencia', 'PEP', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1304, 'Salvoconducto de Permanencia', 'SP', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1305, 'Visa de Residencia Estudiantil', 'VRE', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Periodos academicos (10); 2026-1 coincide con la semilla base.

-- Conflictos cubiertos (01): PK(id) y uq_periodos_academicos_nombre_estado (parcial WHERE estado).
INSERT INTO periodos_academicos (id, nombre, fecha_inicio, fecha_fin, estado, creado, actualizado) VALUES
(1400, '2023-1', '2023-01-01', '2023-06-30', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1401, '2023-2', '2023-07-01', '2023-12-31', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1402, '2024-1', '2024-01-01', '2024-06-30', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1403, '2024-2', '2024-07-01', '2024-12-31', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1404, '2025-1', '2025-01-01', '2025-06-30', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1405, '2025-2', '2025-07-01', '2025-12-31', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1406, '2026-1', '2026-01-01', '2026-12-31', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1407, '2027-1', '2027-01-01', '2027-06-30', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1408, '2027-2', '2027-07-01', '2027-12-31', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1409, '2028-1', '2028-01-01', '2028-06-30', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Programas academicos (20), nombres reales de educación superior en Colombia.
-- Prefijo [DEMO]: evita colisionar con el programa de prueba de Neon.

-- Conflictos cubiertos (01): PK(id) y uq_programas_academicos_nombre_estado (parcial WHERE estado).
INSERT INTO programas_academicos (id, nombre, estado, creado, actualizado) VALUES
(1500, '[DEMO] Ingeniería de Sistemas', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1501, '[DEMO] Ingeniería Industrial', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1502, '[DEMO] Administración de Empresas', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1503, '[DEMO] Contaduría Pública', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1504, '[DEMO] Derecho', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1505, '[DEMO] Medicina', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1506, '[DEMO] Enfermería', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1507, '[DEMO] Psicología', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1508, '[DEMO] Arquitectura', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1509, '[DEMO] Ingeniería Civil', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1510, '[DEMO] Economía', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1511, '[DEMO] Comunicación Social', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1512, '[DEMO] Diseño Gráfico', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1513, '[DEMO] Licenciatura en Matemáticas', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1514, '[DEMO] Licenciatura en Lenguas Modernas', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1515, '[DEMO] Trabajo Social', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1516, '[DEMO] Biología', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1517, '[DEMO] Química', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1518, '[DEMO] Física', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1519, '[DEMO] Estadística', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Asignaturas (20) con descripcion. Prefijo [DEMO] por el mismo motivo.

-- Conflictos cubiertos (01): PK(id) y uq_modulos_nombre_estado (parcial WHERE estado).
INSERT INTO modulos (id, nombre, descripcion, estado, creado, actualizado) VALUES
(1600, '[DEMO] Cálculo Diferencial', 'Límites, derivadas y aplicaciones en funciones de una variable.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1601, '[DEMO] Álgebra Lineal', 'Espacios vectoriales, matrices, determinantes y transformaciones lineales.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1602, '[DEMO] Programación I', 'Algoritmos, estructuras de control y fundamentos de Python.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1603, '[DEMO] Estructuras de Datos', 'Listas, pilas, colas, árboles y grafos con análisis de complejidad.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1604, '[DEMO] Bases de Datos', 'Modelo relacional, normalización y consultas SQL.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1605, '[DEMO] Ingeniería de Software', 'Ciclo de vida, requisitos, diseño y pruebas de software.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1606, '[DEMO] Redes de Computadores', 'Modelo TCP/IP, direccionamiento y protocolos de aplicación.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1607, '[DEMO] Sistemas Operativos', 'Procesos, concurrencia, memoria y sistemas de archivos.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1608, '[DEMO] Algoritmos y Complejidad', 'Diseño de algoritmos, recursión y análisis asintótico.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1609, '[DEMO] Matemáticas Discretas', 'Lógica proposicional, conjuntos, combinatoria y teoría de grafos.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1610, '[DEMO] Física Mecánica', 'Cinemática, dinámica, trabajo, energía y momentum.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1611, '[DEMO] Química General', 'Estructura atómica, enlaces, estequiometría y reacciones.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1612, '[DEMO] Estadística Descriptiva', 'Distribuciones de frecuencia, medidas de tendencia y dispersión.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1613, '[DEMO] Microeconomía', 'Oferta, demanda, elasticidad y equilibrio del consumidor.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1614, '[DEMO] Contabilidad Financiera', 'Estados financieros, partida doble y normas contables.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1615, '[DEMO] Derecho Constitucional', 'Constitución, derechos fundamentales y organización del Estado.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1616, '[DEMO] Anatomía Humana', 'Sistemas del cuerpo humano y terminología anatómica.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1617, '[DEMO] Metodología de la Investigación', 'Planteamiento del problema, marco teórico y diseño de investigación.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1618, '[DEMO] Ética Profesional', 'Responsabilidad profesional y códigos de ética en el ejercicio.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1619, '[DEMO] Gestión de Proyectos', 'Planificación, cronogramas, riesgos y seguimiento de proyectos.', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Usuarios de demostracion (20): 12 estudiantes, 6 docentes, 2 administradores.

-- Conflictos cubiertos (01): PK(id), uq_usuarios_correo_estado y uq_usuarios_identificacion_estado (parciales WHERE estado).
INSERT INTO usuarios (id, identificacion, nombre, apellido, correo, password, rol_id, programa_id, tipo_documento_id, estado, creado, actualizado) VALUES
(1700, '9000000001', 'Juan Sebastián', 'Rodríguez', 'estudiante01@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1500, 1300, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1701, '9000000002', 'María Fernanda', 'Gómez', 'estudiante02@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1501, 1301, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1702, '9000000003', 'Andrés Felipe', 'Martínez', 'estudiante03@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1502, 1302, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1703, '9000000004', 'Laura Valentina', 'Hernández', 'estudiante04@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1503, 1303, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1704, '9000000005', 'Santiago', 'García', 'estudiante05@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1504, 1304, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1705, '9000000006', 'Daniela', 'López', 'estudiante06@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1505, 1305, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1706, '9000000007', 'Carlos Andrés', 'Pérez', 'estudiante07@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1506, 1300, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1707, '9000000008', 'Camila', 'Sánchez', 'estudiante08@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1507, 1301, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1708, '9000000009', 'Juan David', 'Ramírez', 'estudiante09@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1508, 1302, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1709, '9000000010', 'Valentina', 'Torres', 'estudiante10@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1509, 1303, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1710, '9000000011', 'Nicolás', 'Díaz', 'estudiante11@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1510, 1304, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1711, '9000000012', 'Isabella', 'Castro', 'estudiante12@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ESTUDIANTE' AND estado = TRUE LIMIT 1), 1511, 1305, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1712, '9000000013', 'Mateo', 'Moreno', 'docente13@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'DOCENTE' AND estado = TRUE LIMIT 1), 1512, 1300, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1713, '9000000014', 'Sofía', 'Ríos', 'docente14@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'DOCENTE' AND estado = TRUE LIMIT 1), 1513, 1301, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1714, '9000000015', 'Alejandro', 'Vargas', 'docente15@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'DOCENTE' AND estado = TRUE LIMIT 1), 1514, 1302, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1715, '9000000016', 'Mariana', 'Mendoza', 'docente16@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'DOCENTE' AND estado = TRUE LIMIT 1), 1515, 1303, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1716, '9000000017', 'Emilio', 'Ospina', 'docente17@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'DOCENTE' AND estado = TRUE LIMIT 1), 1516, 1304, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1717, '9000000018', 'Gabriela', 'Restrepo', 'docente18@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'DOCENTE' AND estado = TRUE LIMIT 1), 1517, 1305, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1718, '9000000019', 'Tomás', 'Cárdenas', 'administrador19@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ADMINISTRADOR' AND estado = TRUE LIMIT 1), 1518, 1300, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1719, '9000000020', 'Lucía', 'Valencia', 'administrador20@demo.ejemplo.edu.co', '$2b$12$mlqlHwS3WdJbglSSKc4fYOw.YJ1If4AuGU.hw4UIw6YdUjk9x2/yi', (SELECT id FROM roles WHERE nombre = 'ADMINISTRADOR' AND estado = TRUE LIMIT 1), 1519, 1301, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Sedes (20).

-- Conflictos cubiertos (01): PK(id) y uq_sedes_nombre_estado (parcial WHERE estado).
INSERT INTO sedes (id, nombre, tipo_estructura, estado, creado, actualizado) VALUES
(1800, 'Sede Central', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1801, 'Sede Norte', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1802, 'Sede Sur', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1803, 'Sede Occidente', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1804, 'Sede Centro Histórico', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1805, 'Sede La Candelaria', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1806, 'Sede Chapinero', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1807, 'Sede Usaquén', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1808, 'Sede Suba', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1809, 'Sede Engativá', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1810, 'Sede Kennedy', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1811, 'Sede Bosa', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1812, 'Sede Fontibón', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1813, 'Sede Ciudad Bolívar', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1814, 'Sede Sumapaz', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1815, 'Sede Teusaquillo', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1816, 'Sede Puente Aranda', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1817, 'Sede Los Mártires', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1818, 'Sede Antonio Nariño', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1819, 'Sede Rafael Uribe', 'BLOQUES', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Zonas (20), una por sede.

-- Conflictos cubiertos (01): PK(id) y uq_zonas_sede_nombre_estado (parcial WHERE estado).
INSERT INTO zonas (id, sede_id, nombre, estado, creado, actualizado) VALUES
(1900, 1800, 'Bloque Académico A', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1901, 1801, 'Bloque de Laboratorios', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1902, 1802, 'Bloque Administrativo', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1903, 1803, 'Bloque de Posgrados', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1904, 1804, 'Bloque de Bienestar', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1905, 1805, 'Bloque de Biblioteca', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1906, 1806, 'Bloque de Auditorios', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1907, 1807, 'Bloque de Investigación', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1908, 1808, 'Bloque de Aulas Norte', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1909, 1809, 'Bloque de Aulas Sur', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1910, 1810, 'Bloque de Cómputo', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1911, 1811, 'Bloque de Talleres', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1912, 1812, 'Bloque de Consultorios', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1913, 1813, 'Bloque de Studios', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1914, 1814, 'Bloque Deportivo', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1915, 1815, 'Bloque de Servicios', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1916, 1816, 'Bloque de Extensión', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1917, 1817, 'Bloque de Archivo', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1918, 1818, 'Bloque de Cafetería', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1919, 1819, 'Bloque de Parqueaderos', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Recursos fisicos (20) con sede y zona coherentes.

-- Conflictos cubiertos (01): PK(id) y uq_recursos_sede_zona_nombre_estado (parcial WHERE estado).
INSERT INTO recursos_fisicos (id, sede_id, zona_id, nombre, tipo, estado, creado, actualizado) VALUES
(2000, 1800, 1900, 'Salón 101', 'SALON', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2001, 1801, 1901, 'Laboratorio de Cómputo 1', 'LABORATORIO', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2002, 1802, 1902, 'Auditorio Principal', 'AUDITORIO', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2003, 1803, 1903, 'Sala de Juntas 2', 'SALA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2004, 1804, 1904, 'Oficina de Coordinación', 'OFICINA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2005, 1805, 1905, 'Salón 202', 'SALON', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2006, 1806, 1906, 'Laboratorio de Física', 'LABORATORIO', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2007, 1807, 1907, 'Sala de Estudio 3', 'SALA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2008, 1808, 1908, 'Salón 303', 'SALON', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2009, 1809, 1909, 'Sala de Profesores', 'SALA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2010, 1810, 1910, 'Salón 104', 'SALON', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2011, 1811, 1911, 'Laboratorio de Química', 'LABORATORIO', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2012, 1812, 1912, 'Auditorio Menor', 'AUDITORIO', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2013, 1813, 1913, 'Sala de Tutorías', 'SALA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2014, 1814, 1914, 'Oficina de Decanatura', 'OFICINA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2015, 1815, 1915, 'Salón 205', 'SALON', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2016, 1816, 1916, 'Laboratorio de idiomas', 'LABORATORIO', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2017, 1817, 1917, 'Sala de Videoconferencia', 'SALA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2018, 1818, 1918, 'Salón 306', 'SALON', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2019, 1819, 1919, 'Sala de Lectura', 'SALA', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Asignacion docente-asignatura (20 pares distintos).

-- Conflictos cubiertos (01): PK(id) y uq_docentes_modulos_docente_modulo (parcial WHERE estado).
INSERT INTO docentes_modulos (id, docente_id, modulo_id, estado, creado, actualizado) VALUES
(2100, 1712, 1600, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2101, 1713, 1607, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2102, 1714, 1614, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2103, 1715, 1601, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2104, 1716, 1608, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2105, 1717, 1615, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2106, 1712, 1602, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2107, 1713, 1609, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2108, 1714, 1616, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2109, 1715, 1603, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2110, 1716, 1610, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2111, 1717, 1617, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2112, 1712, 1604, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2113, 1713, 1611, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2114, 1714, 1618, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2115, 1715, 1605, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2116, 1716, 1612, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2117, 1717, 1619, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2118, 1712, 1606, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2119, 1713, 1613, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Disponibilidad horaria (20), sin solapes por docente/dia/hora.

-- Conflictos cubiertos (01): PK(id) y uq_disponibilidad_docente_docente_dia_hora (parcial WHERE estado).
INSERT INTO disponibilidad_docente (id, docente_id, dia_semana, hora_inicio, hora_fin, estado, creado, actualizado) VALUES
(2200, 1712, 1, '07:00', '09:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2201, 1713, 2, '07:00', '09:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2202, 1714, 3, '07:00', '09:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2203, 1715, 4, '07:00', '09:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2204, 1716, 5, '07:00', '09:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2205, 1717, 1, '10:00', '12:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2206, 1712, 2, '10:00', '12:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2207, 1713, 3, '10:00', '12:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2208, 1714, 4, '10:00', '12:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2209, 1715, 5, '10:00', '12:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2210, 1716, 1, '14:00', '16:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2211, 1717, 2, '14:00', '16:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2212, 1712, 3, '14:00', '16:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2213, 1713, 4, '14:00', '16:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2214, 1714, 5, '14:00', '16:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2215, 1715, 1, '16:00', '18:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2216, 1716, 2, '16:00', '18:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2217, 1717, 3, '16:00', '18:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2218, 1712, 4, '16:00', '18:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2219, 1713, 5, '16:00', '18:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Solicitudes (20): fechas ni domingo ni festivo colombiano de 2026.

-- Conflictos cubiertos (01): PK(id) y UNIQUE(numero_consulta).
INSERT INTO solicitudes_consultas (id, numero_consulta, estado_consulta, prioridad, asunto, descripcion, fecha_consulta, hora_consulta, estudiante_id, docente_id, modulo_id, recurso_fisico_id, recurso_fisico_nombre, estado, creado, actualizado) VALUES
(2300, 'SC-2026-900001', 'RESUELTA', 'MEDIA', 'Duda sobre el teorema del binomio', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-02', '08:00', 1700, 1712, 1600, 2000, 'Sede Central · Bloque Académico A · Salón 101', TRUE, '2026-01-28 09:00:00', '2026-02-01 09:00:00'),
(2301, 'SC-2026-900002', 'RESUELTA', 'ALTA', 'Aclaración de la nota del primer parcial', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-03', '08:00', 1701, 1713, 1601, 2001, 'Sede Norte · Bloque de Laboratorios · Laboratorio de Cómputo 1', TRUE, '2026-01-29 09:00:00', '2026-02-02 09:00:00'),
(2302, 'SC-2026-900003', 'RESUELTA', 'BAJA', 'Orientación para el marco teórico del trabajo final', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-04', '08:00', 1702, 1714, 1602, 2002, 'Sede Sur · Bloque Administrativo · Auditorio Principal', TRUE, '2026-01-30 09:00:00', '2026-02-03 09:00:00'),
(2303, 'SC-2026-900004', 'RESUELTA', 'MEDIA', 'Consulta sobre la fecha de entrega del laboratorio', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-05', '08:00', 1703, 1715, 1603, 2003, 'Sede Occidente · Bloque de Posgrados · Sala de Juntas 2', TRUE, '2026-01-31 09:00:00', '2026-02-04 09:00:00'),
(2304, 'SC-2026-900005', 'RESUELTA', 'ALTA', 'Revisión del ejercicio de derivadas implícitas', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-06', '08:00', 1704, 1716, 1604, 2004, 'Sede Centro Histórico · Bloque de Bienestar · Oficina de Coordinación', TRUE, '2026-02-01 09:00:00', '2026-02-05 09:00:00'),
(2305, 'SC-2026-900006', 'RESUELTA', 'BAJA', 'Duda sobre la normalización de la base de datos', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-07', '08:00', 1705, 1717, 1605, 2005, 'Sede La Candelaria · Bloque de Biblioteca · Salón 202', TRUE, '2026-02-02 09:00:00', '2026-02-06 09:00:00'),
(2306, 'SC-2026-900007', 'RESUELTA', 'MEDIA', 'Solicitud de reposición de la clase práctica', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-09', '08:00', 1706, 1712, 1606, 2006, 'Sede Chapinero · Bloque de Auditorios · Laboratorio de Física', TRUE, '2026-02-04 09:00:00', '2026-02-08 09:00:00'),
(2307, 'SC-2026-900008', 'RESUELTA', 'ALTA', 'Aclaración del criterio de evaluación del proyecto', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-10', '08:00', 1707, 1713, 1607, 2007, 'Sede Usaquén · Bloque de Investigación · Sala de Estudio 3', TRUE, '2026-02-05 09:00:00', '2026-02-09 09:00:00'),
(2308, 'SC-2026-900009', 'RESUELTA', 'BAJA', 'Consulta sobre la bibliografía del módulo', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-11', '08:00', 1708, 1714, 1608, NULL, NULL, TRUE, '2026-02-06 09:00:00', '2026-02-10 09:00:00'),
(2309, 'SC-2026-900010', 'RESUELTA', 'MEDIA', 'Duda sobre el uso de índices en las consultas', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-12', '08:00', 1709, 1715, 1609, NULL, NULL, TRUE, '2026-02-07 09:00:00', '2026-02-11 09:00:00'),
(2310, 'SC-2026-900011', 'EN_PROCESO', 'ALTA', 'Orientación en el planteamiento del problema de investigación', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-13', '08:00', 1710, 1716, 1610, NULL, NULL, TRUE, '2026-02-08 09:00:00', '2026-02-12 09:00:00'),
(2311, 'SC-2026-900012', 'EN_PROCESO', 'BAJA', 'Revisión del diagrama de clases entregado', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-14', '08:00', 1711, 1717, 1611, NULL, NULL, TRUE, '2026-02-09 09:00:00', '2026-02-13 09:00:00'),
(2312, 'SC-2026-900013', 'EN_PROCESO', 'MEDIA', 'Consulta sobre el cronograma del semestre', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-16', '08:00', 1700, 1712, 1612, NULL, NULL, TRUE, '2026-02-11 09:00:00', '2026-02-15 09:00:00'),
(2313, 'SC-2026-900014', 'EN_PROCESO', 'ALTA', 'Aclaración sobre la política de asistencia', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-17', '08:00', 1701, 1713, 1613, NULL, NULL, TRUE, '2026-02-12 09:00:00', '2026-02-16 09:00:00'),
(2314, 'SC-2026-900015', 'EN_PROCESO', 'BAJA', 'Duda sobre el cálculo de la media ponderada', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-18', '08:00', 1702, 1714, 1614, NULL, NULL, TRUE, '2026-02-13 09:00:00', '2026-02-17 09:00:00'),
(2315, 'SC-2026-900016', 'PENDIENTE', 'MEDIA', 'Solicitud de retroalimentación del ensayo', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-19', '08:00', 1703, 1715, 1615, NULL, NULL, TRUE, '2026-02-14 09:00:00', '2026-02-18 09:00:00'),
(2316, 'SC-2026-900017', 'PENDIENTE', 'ALTA', 'Consulta sobre el protocolo de laboratorio', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-20', '08:00', 1704, 1716, 1616, NULL, NULL, TRUE, '2026-02-15 09:00:00', '2026-02-19 09:00:00'),
(2317, 'SC-2026-900018', 'PENDIENTE', 'BAJA', 'Aclaración de los requisitos de matrícula', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-21', '08:00', 1705, 1717, 1617, NULL, NULL, TRUE, '2026-02-16 09:00:00', '2026-02-20 09:00:00'),
(2318, 'SC-2026-900019', 'CANCELADA', 'MEDIA', 'Duda sobre la escala de calificación institucional', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-23', '08:00', 1706, 1712, 1618, NULL, NULL, TRUE, '2026-02-18 09:00:00', '2026-02-22 09:00:00'),
(2319, 'SC-2026-900020', 'RECHAZADA', 'ALTA', 'Orientación sobre el examen final', 'Solicitud de asesoría académica registrada para el taller.', '2026-02-24', '08:00', 1707, 1713, 1619, NULL, NULL, TRUE, '2026-02-19 09:00:00', '2026-02-23 09:00:00')
ON CONFLICT DO NOTHING;

-- Calificaciones (10): SOLO sobre consultas RESUELTAS, una por solicitud.

-- Conflictos cubiertos (01): PK(id) y uq_calificaciones_consulta_solicitud (parcial WHERE estado).
INSERT INTO calificaciones_consulta (id, solicitud_id, puntaje, comentario, estado, creado, actualizado) VALUES
(2500, 2300, 3, 'Valoración de la asesoría: buena atención.', TRUE, '2026-02-03 09:00:00', '2026-02-03 09:00:00'),
(2501, 2301, 4, 'Valoración de la asesoría: muy buena atención.', TRUE, '2026-02-04 09:00:00', '2026-02-04 09:00:00'),
(2502, 2302, 5, 'Valoración de la asesoría: excelente atención.', TRUE, '2026-02-05 09:00:00', '2026-02-05 09:00:00'),
(2503, 2303, 3, 'Valoración de la asesoría: buena atención.', TRUE, '2026-02-06 09:00:00', '2026-02-06 09:00:00'),
(2504, 2304, 4, 'Valoración de la asesoría: muy buena atención.', TRUE, '2026-02-07 09:00:00', '2026-02-07 09:00:00'),
(2505, 2305, 5, 'Valoración de la asesoría: excelente atención.', TRUE, '2026-02-08 09:00:00', '2026-02-08 09:00:00'),
(2506, 2306, 3, 'Valoración de la asesoría: buena atención.', TRUE, '2026-02-10 09:00:00', '2026-02-10 09:00:00'),
(2507, 2307, 4, 'Valoración de la asesoría: muy buena atención.', TRUE, '2026-02-11 09:00:00', '2026-02-11 09:00:00'),
(2508, 2308, 5, 'Valoración de la asesoría: excelente atención.', TRUE, '2026-02-12 09:00:00', '2026-02-12 09:00:00'),
(2509, 2309, 3, 'Valoración de la asesoría: buena atención.', TRUE, '2026-02-13 09:00:00', '2026-02-13 09:00:00')
ON CONFLICT DO NOTHING;

-- Comentarios (20): 15 de retroalimentacion del docente asignado + 5 del estudiante.

-- Conflictos cubiertos (01): PK(id) y UNIQUE(codigo).
INSERT INTO comentarios (id, codigo, contenido, editado, autor_id, solicitud_id, estado, creado, actualizado) VALUES
(2400, 'DEMO-COM-0001', 'Revise la unidad 3 y traiga el ejercicio resuelto a la próxima asesoría.', FALSE, 1712, 2300, TRUE, '2026-02-03 10:00:00', '2026-02-03 10:00:00'),
(2401, 'DEMO-COM-0002', 'Su planteamiento es correcto, profundice en la justificación teórica.', FALSE, 1713, 2301, TRUE, '2026-02-04 10:00:00', '2026-02-04 10:00:00'),
(2402, 'DEMO-COM-0003', 'Le sugiero contrastar las dos fuentes antes de concluir.', FALSE, 1714, 2302, TRUE, '2026-02-05 10:00:00', '2026-02-05 10:00:00'),
(2403, 'DEMO-COM-0004', 'La entrega cumple, corrija únicamente las referencias bibliográficas.', FALSE, 1715, 2303, TRUE, '2026-02-06 10:00:00', '2026-02-06 10:00:00'),
(2404, 'DEMO-COM-0005', 'Practique los casos límite antes del examen parcial.', FALSE, 1716, 2304, TRUE, '2026-02-07 10:00:00', '2026-02-07 10:00:00'),
(2405, 'DEMO-COM-0006', 'El procedimiento es válido, pero documente cada paso.', FALSE, 1717, 2305, TRUE, '2026-02-08 10:00:00', '2026-02-08 10:00:00'),
(2406, 'DEMO-COM-0007', 'Compare su resultado con el ejemplo de la guía y comente la diferencia.', FALSE, 1712, 2306, TRUE, '2026-02-10 10:00:00', '2026-02-10 10:00:00'),
(2407, 'DEMO-COM-0008', 'Buen avance, no olvide citar la norma consultada.', FALSE, 1713, 2307, TRUE, '2026-02-11 10:00:00', '2026-02-11 10:00:00'),
(2408, 'DEMO-COM-0009', 'La duda se resuelve con la definición vista en clase, vuelva a leerla.', FALSE, 1714, 2308, TRUE, '2026-02-12 10:00:00', '2026-02-12 10:00:00'),
(2409, 'DEMO-COM-0010', 'Ajuste el formato de entrega según el lineamiento del programa.', FALSE, 1715, 2309, TRUE, '2026-02-13 10:00:00', '2026-02-13 10:00:00'),
(2410, 'DEMO-COM-0011', 'Su análisis cualitativo necesita un soporte cuantitativo.', FALSE, 1716, 2310, TRUE, '2026-02-14 10:00:00', '2026-02-14 10:00:00'),
(2411, 'DEMO-COM-0012', 'Coordine con el monitor para la sesión de repaso.', FALSE, 1717, 2311, TRUE, '2026-02-15 10:00:00', '2026-02-15 10:00:00'),
(2412, 'DEMO-COM-0013', 'El error está en el signo del tercer término, corríjalo.', FALSE, 1712, 2312, TRUE, '2026-02-17 10:00:00', '2026-02-17 10:00:00'),
(2413, 'DEMO-COM-0014', 'La consulta queda atendida, puede cerrar la solicitud.', FALSE, 1713, 2313, TRUE, '2026-02-18 10:00:00', '2026-02-18 10:00:00'),
(2414, 'DEMO-COM-0015', 'Consulte el repositorio de ejemplos del curso.', FALSE, 1714, 2314, TRUE, '2026-02-19 10:00:00', '2026-02-19 10:00:00'),
(2415, 'DEMO-COM-0016', 'Gracias, la explicación quedó muy clara.', FALSE, 1700, 2300, TRUE, '2026-02-03 11:00:00', '2026-02-03 11:00:00'),
(2416, 'DEMO-COM-0017', 'Aplicaré la recomendación en la próxima entrega.', FALSE, 1701, 2301, TRUE, '2026-02-04 11:00:00', '2026-02-04 11:00:00'),
(2417, 'DEMO-COM-0018', 'Quedo atento a la sesión de repaso.', FALSE, 1702, 2302, TRUE, '2026-02-05 11:00:00', '2026-02-05 11:00:00'),
(2418, 'DEMO-COM-0019', 'Ya ajusté el documento con sus observaciones.', FALSE, 1703, 2303, TRUE, '2026-02-06 11:00:00', '2026-02-06 11:00:00'),
(2419, 'DEMO-COM-0020', 'Perfecto, ya no tengo dudas sobre el tema.', FALSE, 1704, 2304, TRUE, '2026-02-07 11:00:00', '2026-02-07 11:00:00')
ON CONFLICT DO NOTHING;

-- Notificaciones (20) coherentes con el estado de cada consulta.

-- Conflictos cubiertos (01): PK(id) y UNIQUE(codigo).
INSERT INTO notificaciones (id, codigo, remitente_id, destinatario_id, solicitud_consulta_id, tipo, titulo, mensaje, leida, estado, creado, actualizado) VALUES
(2600, 'DEMO-NOT-0001', 1712, 1700, 2300, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', TRUE, TRUE, '2026-02-02 12:00:00', '2026-02-02 12:00:00'),
(2601, 'DEMO-NOT-0002', 1713, 1701, 2301, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', FALSE, TRUE, '2026-02-03 12:00:00', '2026-02-03 12:00:00'),
(2602, 'DEMO-NOT-0003', 1714, 1702, 2302, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', FALSE, TRUE, '2026-02-04 12:00:00', '2026-02-04 12:00:00'),
(2603, 'DEMO-NOT-0004', 1715, 1703, 2303, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', TRUE, TRUE, '2026-02-05 12:00:00', '2026-02-05 12:00:00'),
(2604, 'DEMO-NOT-0005', 1716, 1704, 2304, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', FALSE, TRUE, '2026-02-06 12:00:00', '2026-02-06 12:00:00'),
(2605, 'DEMO-NOT-0006', 1717, 1705, 2305, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', FALSE, TRUE, '2026-02-07 12:00:00', '2026-02-07 12:00:00'),
(2606, 'DEMO-NOT-0007', 1712, 1706, 2306, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', TRUE, TRUE, '2026-02-09 12:00:00', '2026-02-09 12:00:00'),
(2607, 'DEMO-NOT-0008', 1713, 1707, 2307, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', FALSE, TRUE, '2026-02-10 12:00:00', '2026-02-10 12:00:00'),
(2608, 'DEMO-NOT-0009', 1714, 1708, 2308, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', FALSE, TRUE, '2026-02-11 12:00:00', '2026-02-11 12:00:00'),
(2609, 'DEMO-NOT-0010', 1715, 1709, 2309, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a RESUELTA.', TRUE, TRUE, '2026-02-12 12:00:00', '2026-02-12 12:00:00'),
(2610, 'DEMO-NOT-0011', 1716, 1710, 2310, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a EN_PROCESO.', FALSE, TRUE, '2026-02-13 12:00:00', '2026-02-13 12:00:00'),
(2611, 'DEMO-NOT-0012', 1717, 1711, 2311, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a EN_PROCESO.', FALSE, TRUE, '2026-02-14 12:00:00', '2026-02-14 12:00:00'),
(2612, 'DEMO-NOT-0013', 1712, 1700, 2312, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a EN_PROCESO.', TRUE, TRUE, '2026-02-16 12:00:00', '2026-02-16 12:00:00'),
(2613, 'DEMO-NOT-0014', 1713, 1701, 2313, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a EN_PROCESO.', FALSE, TRUE, '2026-02-17 12:00:00', '2026-02-17 12:00:00'),
(2614, 'DEMO-NOT-0015', 1714, 1702, 2314, 'CAMBIO_ESTADO', 'Actualización del estado de su consulta', 'Su consulta cambió a EN_PROCESO.', FALSE, TRUE, '2026-02-18 12:00:00', '2026-02-18 12:00:00'),
(2615, 'DEMO-NOT-0016', 1703, 1715, 2315, 'NUEVA_SOLICITUD', 'Nueva solicitud de consulta', 'Se registró una nueva solicitud de consulta académica.', TRUE, TRUE, '2026-02-19 12:00:00', '2026-02-19 12:00:00'),
(2616, 'DEMO-NOT-0017', 1704, 1716, 2316, 'NUEVA_SOLICITUD', 'Nueva solicitud de consulta', 'Se registró una nueva solicitud de consulta académica.', FALSE, TRUE, '2026-02-20 12:00:00', '2026-02-20 12:00:00'),
(2617, 'DEMO-NOT-0018', 1705, 1717, 2317, 'NUEVA_SOLICITUD', 'Nueva solicitud de consulta', 'Se registró una nueva solicitud de consulta académica.', FALSE, TRUE, '2026-02-21 12:00:00', '2026-02-21 12:00:00'),
(2618, 'DEMO-NOT-0019', 1706, 1712, 2318, 'NUEVA_SOLICITUD', 'Nueva solicitud de consulta', 'Se registró una nueva solicitud de consulta académica.', TRUE, TRUE, '2026-02-23 12:00:00', '2026-02-23 12:00:00'),
(2619, 'DEMO-NOT-0020', 1707, 1713, 2319, 'NUEVA_SOLICITUD', 'Nueva solicitud de consulta', 'Se registró una nueva solicitud de consulta académica.', FALSE, TRUE, '2026-02-24 12:00:00', '2026-02-24 12:00:00')
ON CONFLICT DO NOTHING;

-- Eventos de solicitud (20) coherentes con el estado.

-- Conflictos cubiertos (01): PK(id) y UNIQUE(codigo).
INSERT INTO eventos_solicitud (id, codigo, solicitud_id, usuario_id, tipo_evento, descripcion, fecha_evento, estado, creado, actualizado) VALUES
(2700, 'DEMO-EVE-0001', 2300, 1712, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-02.', '2026-02-02 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2701, 'DEMO-EVE-0002', 2301, 1713, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-03.', '2026-02-03 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2702, 'DEMO-EVE-0003', 2302, 1714, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-04.', '2026-02-04 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2703, 'DEMO-EVE-0004', 2303, 1715, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-05.', '2026-02-05 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2704, 'DEMO-EVE-0005', 2304, 1716, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-06.', '2026-02-06 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2705, 'DEMO-EVE-0006', 2305, 1717, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-07.', '2026-02-07 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2706, 'DEMO-EVE-0007', 2306, 1712, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-09.', '2026-02-09 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2707, 'DEMO-EVE-0008', 2307, 1713, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-10.', '2026-02-10 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2708, 'DEMO-EVE-0009', 2308, 1714, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-11.', '2026-02-11 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2709, 'DEMO-EVE-0010', 2309, 1715, 'CAMBIO_ESTADO', '[DEMO] Consulta marcada RESUELTA para 2026-02-12.', '2026-02-12 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2710, 'DEMO-EVE-0011', 2310, 1716, 'CAMBIO_ESTADO', '[DEMO] Consulta puesta EN_PROCESO para 2026-02-13.', '2026-02-13 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2711, 'DEMO-EVE-0012', 2311, 1717, 'CAMBIO_ESTADO', '[DEMO] Consulta puesta EN_PROCESO para 2026-02-14.', '2026-02-14 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2712, 'DEMO-EVE-0013', 2312, 1712, 'CAMBIO_ESTADO', '[DEMO] Consulta puesta EN_PROCESO para 2026-02-16.', '2026-02-16 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2713, 'DEMO-EVE-0014', 2313, 1713, 'CAMBIO_ESTADO', '[DEMO] Consulta puesta EN_PROCESO para 2026-02-17.', '2026-02-17 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2714, 'DEMO-EVE-0015', 2314, 1714, 'CAMBIO_ESTADO', '[DEMO] Consulta puesta EN_PROCESO para 2026-02-18.', '2026-02-18 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2715, 'DEMO-EVE-0016', 2315, 1703, 'CREACION', '[DEMO] Creación de la solicitud para 2026-02-19.', '2026-02-19 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2716, 'DEMO-EVE-0017', 2316, 1704, 'CREACION', '[DEMO] Creación de la solicitud para 2026-02-20.', '2026-02-20 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2717, 'DEMO-EVE-0018', 2317, 1705, 'CREACION', '[DEMO] Creación de la solicitud para 2026-02-21.', '2026-02-21 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2718, 'DEMO-EVE-0019', 2318, 1706, 'CANCELACION', '[DEMO] Consulta cancelada para 2026-02-23.', '2026-02-23 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2719, 'DEMO-EVE-0020', 2319, 1713, 'RECHAZO', '[DEMO] Consulta rechazada para 2026-02-24.', '2026-02-24 08:30:00', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Tokens de recuperacion (10): solo hashes, sin contrasenas.

-- Conflictos cubiertos (01): PK(id) y UNIQUE(token).
INSERT INTO password_reset_tokens (id, token, usuario_id, fecha_expiracion, utilizado, estado, creado, actualizado) VALUES
(2800, '12cf273e424ca21e7c7d389b50086346fe20bfe9b5f283c458e8b4010433dcb8', 1700, '2026-01-10 08:00:00', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2801, '53a946bab7abdf06273df5b317ab194a8c9581a8e188f8e7b97d2529c95265c6', 1701, '2026-01-11 08:00:00', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2802, 'bdf252399a2f76b8450bb68831ba2d24c4dbf1437354fa193fb8502a13c2f371', 1702, '2026-01-12 08:00:00', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2803, '3b037e73a539be086820673749a185e82df22f268e42dedaf0206266c5eb1a98', 1703, '2026-01-13 08:00:00', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2804, '28afd370b968744de4b2562d111eab71a1eb21ff1bd818c675745393dab7add1', 1704, '2026-01-14 08:00:00', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2805, 'cba6249db165946eabb93ec50b026ab7affb089cf87d93a1f636b17a4c1fdb7d', 1705, '2026-01-15 08:00:00', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2806, '6f15f43d3ee3641e498e2b72be2668d4ae133eb56dd2d001e239a6ad7df4678b', 1706, '2026-01-16 08:00:00', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2807, '3af839e0cc0e396da575ce5cae1a56921d061422051b7af31568ab0a55f3662d', 1707, '2026-01-17 08:00:00', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2808, '1545dec48587867a273c66abb8a151fc7ef6784ed3cf680191a2e9a2b9f9f945', 1708, '2026-01-18 08:00:00', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2809, 'feb722e9dc832a3324283b73e0bbb2e086733c39424794320c676e28dd2f8d63', 1709, '2026-01-19 08:00:00', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- Resincroniza TODAS las secuencias SERIAL tras insertar IDs explicitos.
-- pg_get_serial_sequence() localiza la secuencia por la relacion OWNED BY
-- del SERIAL de 01. La forma de 3 argumentos deja is_called = FALSE cuando
-- la tabla esta vacia, asi el primer nextval() devuelve 1 y no 2.
-- Reejecutar el script deja exactamente los mismos valores.
-- ---------------------------------------------------------------------------


SELECT setval(pg_get_serial_sequence('modulos', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM modulos;


SELECT setval(pg_get_serial_sequence('modulos_sistema', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM modulos_sistema;


SELECT setval(pg_get_serial_sequence('periodos_academicos', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM periodos_academicos;


SELECT setval(pg_get_serial_sequence('programas_academicos', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM programas_academicos;


SELECT setval(pg_get_serial_sequence('roles', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM roles;


SELECT setval(pg_get_serial_sequence('sedes', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM sedes;


SELECT setval(pg_get_serial_sequence('tipos_documento', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM tipos_documento;


SELECT setval(pg_get_serial_sequence('modulos_x_rol', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM modulos_x_rol;


SELECT setval(pg_get_serial_sequence('usuarios', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM usuarios;


SELECT setval(pg_get_serial_sequence('zonas', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM zonas;


SELECT setval(pg_get_serial_sequence('disponibilidad_docente', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM disponibilidad_docente;


SELECT setval(pg_get_serial_sequence('docentes_modulos', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM docentes_modulos;


SELECT setval(pg_get_serial_sequence('password_reset_tokens', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM password_reset_tokens;


SELECT setval(pg_get_serial_sequence('recursos_fisicos', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM recursos_fisicos;


SELECT setval(pg_get_serial_sequence('solicitudes_consultas', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM solicitudes_consultas;


SELECT setval(pg_get_serial_sequence('calificaciones_consulta', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM calificaciones_consulta;


SELECT setval(pg_get_serial_sequence('comentarios', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM comentarios;


SELECT setval(pg_get_serial_sequence('eventos_solicitud', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM eventos_solicitud;


SELECT setval(pg_get_serial_sequence('notificaciones', 'id'),
              COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
FROM notificaciones;


COMMIT;
