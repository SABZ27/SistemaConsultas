-- ============================================================================
-- ia/db/crear_rol_lectura.sql — Rol de SOLO LECTURA para el componente de IA
-- ============================================================================
-- REVISAR ANTES DE EJECUTAR. El responsable lo ejecuta sobre Neon; el agente
-- NO se conecta a la BD ni ejecuta este archivo.
--
-- Objetivo: el rol "ia_lectura" solo puede hacer SELECT sobre 6 VISTAS nuevas.
-- Las vistas NO exponen: contrasenas (usuarios.password), tokens
-- (password_reset_tokens.token), correos (usuarios.correo), identificaciones
-- (usuarios.identificacion), el nombre del estudiante (join por estudiante_id)
-- ni la descripcion de la consulta (solicitudes_consultas.descripcion).
-- Tampoco se exponen otros textos libres (asunto, contenido de comentarios,
-- comentario de calificacion, titulo/mensaje de notificaciones).
-- SI exponen nombres legibles de docente, modulo/asignatura, programa, sede,
-- zona y recurso fisico.
--
-- LA CONTRASENA NO ESTA EN ESTE ARCHIVO: se pasa como variable de psql
-- :'clave_ia_lectura'. Formas de ejecutar (no pegar la clave en el historial):
--   psql "<DSN_DE_NEON>" -v ON_ERROR_STOP=1 \
--     -v clave_ia_lectura='<CLAVE>' -f ia/db/crear_rol_lectura.sql
-- o, dentro de psql interactive:  \set clave_ia_lectura '<CLAVE>'  y  \i ...
--
-- Nombres de tablas/columnas tomados de backend/app/models y de
-- docs/sql/01_postgres_schema.sql (19 tablas, VARCHAR(50) para los enums).
-- PostgreSQL 15+ asumido. Las vistas se ejecutan con los permisos de su
-- PROPIETARIO (security_invoker NO se activa), por lo que ia_lectura no
-- necesita acceso a las tablas base.
-- ============================================================================

\set ON_ERROR_STOP on

-- ----------------------------------------------------------------------------
-- 1. Rol
-- ----------------------------------------------------------------------------
-- Ejecutar una sola vez. Si el rol ya existe, comentar este CREATE ROLE.
CREATE ROLE ia_lectura
    LOGIN
    PASSWORD :'clave_ia_lectura'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    CONNECTION LIMIT 3
    VALID UNTIL 'infinity';

-- statement_timeout corto e inactividad acotada; refuerzo de solo lectura.
ALTER ROLE ia_lectura SET statement_timeout = '15s';
ALTER ROLE ia_lectura SET idle_in_transaction_session_timeout = '15s';
-- Refuerzo opcional: si el cliente requiere transacciones de escritura,
-- comentar la linea siguiente (de todas formas el rol solo tiene SELECT).
ALTER ROLE ia_lectura SET default_transaction_read_only = on;

-- ----------------------------------------------------------------------------
-- 2. REVOKE de todo lo demas (esquema public, tablas, secuencias, funciones
--    y privilegios por defecto). Solo se concedera USAGE + SELECT en las vistas.
-- ----------------------------------------------------------------------------
REVOKE ALL ON SCHEMA public FROM ia_lectura;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ia_lectura;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ia_lectura;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM ia_lectura;

-- Privilegios por defecto: los objetos que se creen en el futuro no deben
-- heredar permisos para PUBLIC ni para ia_lectura. Estas sentencias aplican a
-- los objetos creados por el rol que ejecuta este script (el propietario).
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM ia_lectura;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM ia_lectura;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM ia_lectura;

-- Opcional y MAS ESTRICTO: quitar tambien los privilegios de PUBLIC sobre el
-- esquema. REVISAR antes: otros roles no propietarios perderian USAGE y
-- necesitarian un GRANT explicito. Descomentar solo tras verificarlo:
-- REVOKE ALL ON SCHEMA public FROM PUBLIC;
--
-- Nota: PUBLIC tiene USAGE por defecto sobre public, asi que el REVOKE
-- anterior no elimina ese USAGE heredado. No por ello ia_lectura puede leer
-- tablas base: PUBLIC no tiene privilegios sobre ellas (son del propietario).
-- El UNICO permiso explicito de ia_lectura es SELECT sobre las 6 vistas y
-- USAGE sobre el esquema para poder resolverlas.

-- ----------------------------------------------------------------------------
-- 3. Vistas nuevas (solo columnas legibles y no sensibles)
-- ----------------------------------------------------------------------------

-- 3.1 Consultas: una fila por solicitud activa. El unico join a "usuarios" es
--     por docente_id (nombre/apellido del DOCENTE, permitido). NO se une por
--     estudiante_id, por lo que el nombre del estudiante nunca aparece.
CREATE OR REPLACE VIEW v_ia_consultas AS
SELECT
    s.numero_consulta,
    s.estado_consulta,
    s.prioridad,
    s.fecha_consulta,
    s.hora_consulta,
    (d.nombre || ' ' || d.apellido) AS docente_nombre,
    d.apellido                     AS docente_apellido,
    m.nombre                       AS modulo_nombre,
    pa.nombre                      AS programa_nombre,
    se.nombre                      AS sede_nombre,
    z.nombre                       AS zona_nombre,
    rf.nombre                      AS recurso_nombre,
    rf.tipo                        AS recurso_tipo
FROM solicitudes_consultas s
JOIN usuarios d              ON d.id = s.docente_id
JOIN modulos m               ON m.id = s.modulo_id
LEFT JOIN programas_academicos pa ON pa.id = d.programa_id
LEFT JOIN recursos_fisicos rf     ON rf.id = s.recurso_fisico_id
LEFT JOIN sedes se                ON se.id = rf.sede_id
LEFT JOIN zonas z                 ON z.id = rf.zona_id
WHERE s.estado = TRUE
  AND d.estado = TRUE
  AND m.estado = TRUE;

-- 3.2 Docentes (una fila por docente, con su programa academico).
CREATE OR REPLACE VIEW v_ia_docentes AS
SELECT
    (u.nombre || ' ' || u.apellido) AS docente_nombre,
    u.apellido                     AS docente_apellido,
    pa.nombre                      AS programa_nombre
FROM usuarios u
JOIN roles r          ON r.id = u.rol_id
LEFT JOIN programas_academicos pa ON pa.id = u.programa_id
WHERE u.estado = TRUE
  AND r.estado = TRUE
  AND r.nombre = 'DOCENTE';

-- 3.3 Disponibilidad horaria de los docentes.
CREATE OR REPLACE VIEW v_ia_disponibilidad AS
SELECT
    (u.nombre || ' ' || u.apellido) AS docente_nombre,
    u.apellido                     AS docente_apellido,
    dd.dia_semana,
    CASE dd.dia_semana
        WHEN 1 THEN 'Lunes'
        WHEN 2 THEN 'Martes'
        WHEN 3 THEN 'Miercoles'
        WHEN 4 THEN 'Jueves'
        WHEN 5 THEN 'Viernes'
        WHEN 6 THEN 'Sabado'
        WHEN 7 THEN 'Domingo'
    END                            AS dia_nombre,
    dd.hora_inicio,
    dd.hora_fin
FROM disponibilidad_docente dd
JOIN usuarios u ON u.id = dd.docente_id
JOIN roles r    ON r.id = u.rol_id AND r.nombre = 'DOCENTE'
WHERE dd.estado = TRUE
  AND u.estado = TRUE;

-- 3.4 Modulos/asignaturas con el docente que las imparte.
CREATE OR REPLACE VIEW v_ia_modulos AS
SELECT
    m.nombre                       AS modulo_nombre,
    (u.nombre || ' ' || u.apellido) AS docente_nombre,
    u.apellido                     AS docente_apellido,
    pa.nombre                      AS programa_nombre
FROM modulos m
LEFT JOIN docentes_modulos dm ON dm.modulo_id = m.id AND dm.estado = TRUE
LEFT JOIN usuarios u          ON u.id = dm.docente_id AND u.estado = TRUE
LEFT JOIN programas_academicos pa ON pa.id = u.programa_id
WHERE m.estado = TRUE;

-- 3.5 Recursos fisicos por sede y zona.
CREATE OR REPLACE VIEW v_ia_recursos AS
SELECT
    se.nombre       AS sede_nombre,
    se.tipo_estructura,
    z.nombre        AS zona_nombre,
    rf.nombre       AS recurso_nombre,
    rf.tipo         AS recurso_tipo
FROM recursos_fisicos rf
JOIN sedes se   ON se.id = rf.sede_id
LEFT JOIN zonas z ON z.id = rf.zona_id
WHERE rf.estado = TRUE
  AND se.estado = TRUE;

-- 3.6 Calificaciones: solo puntaje, estado y nombres legibles. Se excluye el
--     comentario (texto libre) y cualquier dato del estudiante.
CREATE OR REPLACE VIEW v_ia_calificaciones AS
SELECT
    c.puntaje,
    s.numero_consulta,
    s.estado_consulta,
    (d.nombre || ' ' || d.apellido) AS docente_nombre,
    d.apellido                     AS docente_apellido,
    m.nombre                       AS modulo_nombre,
    c.creado                       AS fecha_calificacion
FROM calificaciones_consulta c
JOIN solicitudes_consultas s ON s.id = c.solicitud_id AND s.estado = TRUE
JOIN usuarios d              ON d.id = s.docente_id AND d.estado = TRUE
JOIN modulos m               ON m.id = s.modulo_id
WHERE c.estado = TRUE;

-- ----------------------------------------------------------------------------
-- 4. Unicos permisos del rol: USAGE en el esquema (necesario para resolver
--    las vistas) y SELECT sobre las 6 vistas. Nada mas.
-- ----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO ia_lectura;
GRANT SELECT ON
    v_ia_consultas,
    v_ia_docentes,
    v_ia_disponibilidad,
    v_ia_modulos,
    v_ia_recursos,
    v_ia_calificaciones
TO ia_lectura;

-- ----------------------------------------------------------------------------
-- 5. Comprobaciones (descomentar para verificar despues de ejecutar)
-- ----------------------------------------------------------------------------
-- SELECT rolname, rolconnlimit, rolconfig FROM pg_roles WHERE rolname = 'ia_lectura';
-- SELECT table_name, privilege_type FROM information_schema.role_table_grants
--   WHERE grantee = 'ia_lectura' ORDER BY table_name, privilege_type;
-- SET ROLE ia_lectura;
-- SELECT COUNT(*) FROM v_ia_consultas;                 -- debe funcionar
-- SELECT * FROM usuarios LIMIT 1;                     -- debe dar permission denied
-- SELECT * FROM solicitudes_consultas LIMIT 1;        -- debe dar permission denied
-- RESET ROLE;
