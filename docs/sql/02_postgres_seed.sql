-- ============================================================================
-- Semilla inicial de PostgreSQL (dominio de negocio)
-- ============================================================================
-- Replica lo que inserta ejecutar_seeds() al arrancar
-- (backend/app/db/seeds.py), sobre una base vacia creada con
-- 01_postgres_schema.sql:
--   * 3 roles
--   * 15 modulos_sistema (nombre, descripcion, ruta, icono)
--   * la matriz modulos_x_rol (MATRIZ_MODULOS_X_ROL)
--   * 4 tipos_documento
--   * 1 periodo_academico vigente
--
-- NO incluye el usuario administrador: se crea por variables de entorno
-- (ADMIN_CORREO, ADMIN_PASSWORD, ADMIN_IDENTIFICACION) en _sembrar_admin().
-- No hay contraseñas, correos personales ni datos reales en este archivo.
--
-- Idempotente: cada bloque usa INSERT ... SELECT ... WHERE NOT EXISTS.
-- PostgreSQL 15+ asumido.
-- ============================================================================

-- Roles ----------------------------------------------------------------------
INSERT INTO roles (nombre)
SELECT v.nombre
FROM (VALUES
    ('ADMINISTRADOR'),
    ('DOCENTE'),
    ('ESTUDIANTE')
) AS v(nombre)
WHERE NOT EXISTS (SELECT 1 FROM roles r WHERE r.nombre = v.nombre);

-- Modulos del sistema --------------------------------------------------------
INSERT INTO modulos_sistema (nombre, descripcion, ruta, icono)
SELECT v.nombre, v.descripcion, v.ruta, v.icono
FROM (VALUES
    ('DASHBOARD', 'Panel principal', '/dashboard', 'dashboard'),
    ('PERFIL', 'Datos del perfil propio', '/perfil', 'person'),
    ('NOTIFICACIONES', 'Centro de notificaciones', '/notificaciones', 'notifications'),
    ('MIS_SOLICITUDES', 'Solicitudes de consulta propias', '/mis-solicitudes', 'assignment'),
    ('ATENCION_SOLICITUDES', 'Atencion de solicitudes asignadas', '/atender-solicitudes', 'support_agent'),
    ('GESTION_SOLICITUDES', 'Gestion global de solicitudes', '/solicitudes', 'manage_search'),
    ('USUARIOS', 'Administracion de usuarios', '/usuarios', 'group'),
    ('ROLES_PERMISOS', 'Administracion de roles y permisos', '/roles-permisos', 'security'),
    ('PROGRAMAS_ASIGNATURAS', 'Programas academicos y asignaturas', '/programas-asignaturas', 'school'),
    ('INFRAESTRUCTURA', 'Administracion de infraestructura fisica', '/infraestructura', 'location_on'),
    ('ASIGNACION_DOCENTES', 'Asignacion de docentes a modulos', '/asignacion-docentes', 'assignment_ind'),
    ('PERIODOS_ACADEMICOS', 'Periodos academicos', '/periodos-academicos', 'event'),
    ('TIPOS_DOCUMENTO', 'Tipos de documento de identidad', '/tipos-documento', 'badge'),
    ('DISPONIBILIDAD_DOCENTE', 'Disponibilidad horaria de docentes', '/disponibilidad-docente', 'schedule'),
    ('CALIFICACIONES', 'Calificaciones de consultas', '/calificaciones', 'star')
) AS v(nombre, descripcion, ruta, icono)
WHERE NOT EXISTS (
    SELECT 1 FROM modulos_sistema m WHERE m.nombre = v.nombre
);

-- Matriz modulo x rol (se resuelve por nombre, sin IDs fijos) ----------------
INSERT INTO modulos_x_rol (rol_id, modulo_id)
SELECT r.id, m.id
FROM roles r
CROSS JOIN modulos_sistema m
JOIN (VALUES
    ('DASHBOARD', 'ADMINISTRADOR'),
    ('DASHBOARD', 'DOCENTE'),
    ('DASHBOARD', 'ESTUDIANTE'),
    ('PERFIL', 'ADMINISTRADOR'),
    ('PERFIL', 'DOCENTE'),
    ('PERFIL', 'ESTUDIANTE'),
    ('NOTIFICACIONES', 'ADMINISTRADOR'),
    ('NOTIFICACIONES', 'DOCENTE'),
    ('NOTIFICACIONES', 'ESTUDIANTE'),
    ('MIS_SOLICITUDES', 'ESTUDIANTE'),
    ('ATENCION_SOLICITUDES', 'DOCENTE'),
    ('GESTION_SOLICITUDES', 'ADMINISTRADOR'),
    ('USUARIOS', 'ADMINISTRADOR'),
    ('ROLES_PERMISOS', 'ADMINISTRADOR'),
    ('PROGRAMAS_ASIGNATURAS', 'ADMINISTRADOR'),
    ('INFRAESTRUCTURA', 'ADMINISTRADOR'),
    ('ASIGNACION_DOCENTES', 'ADMINISTRADOR'),
    ('PERIODOS_ACADEMICOS', 'ADMINISTRADOR'),
    ('TIPOS_DOCUMENTO', 'ADMINISTRADOR'),
    ('DISPONIBILIDAD_DOCENTE', 'ADMINISTRADOR'),
    ('DISPONIBILIDAD_DOCENTE', 'DOCENTE'),
    ('CALIFICACIONES', 'ADMINISTRADOR'),
    ('CALIFICACIONES', 'DOCENTE'),
    ('CALIFICACIONES', 'ESTUDIANTE')
) AS matriz(nombre_modulo, nombre_rol)
  ON matriz.nombre_modulo = m.nombre AND matriz.nombre_rol = r.nombre
WHERE NOT EXISTS (
    SELECT 1 FROM modulos_x_rol mxr
    WHERE mxr.rol_id = r.id AND mxr.modulo_id = m.id
);

-- Tipos de documento ---------------------------------------------------------
INSERT INTO tipos_documento (nombre, sigla)
SELECT v.nombre, v.sigla
FROM (VALUES
    ('Cedula de Ciudadania', 'CC'),
    ('Tarjeta de Identidad', 'TI'),
    ('Cedula de Extranjeria', 'CE'),
    ('Pasaporte', 'PAS')
) AS v(nombre, sigla)
WHERE NOT EXISTS (
    SELECT 1 FROM tipos_documento t WHERE t.nombre = v.nombre
);

-- Periodo academico vigente --------------------------------------------------
-- AJUSTAR: ejecutar_seeds() usa el anio en curso con el nombre '<anio>-1' y
-- el rango 1 de enero a 31 de diciembre. Esas fechas cubren el semestre
-- actual (2026-2, julio-diciembre de 2026), pero deben ajustarse al
-- calendario academico real (nombre, fecha_inicio y fecha_fin) antes de
-- ejecutar este script en un entorno definitivo. Se respeta ademas la
-- comprobacion de solape de _sembrar_periodo_vigente().
INSERT INTO periodos_academicos (nombre, fecha_inicio, fecha_fin)
SELECT '2026-1', DATE '2026-01-01', DATE '2026-12-31'
WHERE NOT EXISTS (
    SELECT 1 FROM periodos_academicos p WHERE p.nombre = '2026-1'
)
AND NOT EXISTS (
    SELECT 1 FROM periodos_academicos p
    WHERE p.fecha_inicio <= DATE '2026-12-31'
      AND p.fecha_fin >= DATE '2026-01-01'
);

-- Comprobacion (descomentar para ejecutar):
--   SELECT (SELECT COUNT(*) FROM roles) AS roles,
--          (SELECT COUNT(*) FROM modulos_sistema) AS modulos,
--          (SELECT COUNT(*) FROM modulos_x_rol) AS matriz,
--          (SELECT COUNT(*) FROM tipos_documento) AS tipos_documento,
--          (SELECT COUNT(*) FROM periodos_academicos) AS periodos;
-- Esperado: 3, 15, 24, 4, 1.
