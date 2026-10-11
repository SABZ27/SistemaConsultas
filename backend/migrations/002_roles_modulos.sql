-- ============================================================================
-- Migración 002: Roles, módulos del sistema y permisos (Fase 2)
-- ============================================================================
-- Objetivo: llevar un esquema creado por las versiones previas (Fase 1) al
-- modelo de la Fase 2:
--
--   1) Nuevas tablas:
--        * roles             (roles del sistema)
--        * modulos_sistema   (módulos funcionales del sistema)
--        * modulos_x_rol     (matriz de permisos rol <-> módulo)
--      Todas con las columnas de auditoría de AuditoriaMixin
--      (estado/creado/actualizado) e índices únicos parciales WHERE estado.
--
--   2) usuarios.rol_id: nueva FK NOT NULL hacia roles.id, reemplaza la
--      antigua columna de enum "rol". Se rellena desde el valor del enum
--      existente y luego se elimina la columna antigua.
--
--   3) Siembra idempotente de:
--        * 3 roles  (ADMINISTRADOR, DOCENTE, ESTUDIANTE)
--        * 15 módulos del sistema
--        * matriz de permisos modulos_x_rol
--
--   4) Triggers BEFORE UPDATE que mantienen "actualizado" en las 3 tablas
--      nuevas (misma función set_actualizado() de la migración 001).
--
-- Características:
--   * Idioma objetivo: PostgreSQL (Neon). SQLAlchemy usa "native_enum=False",
--     por lo que los enums previos son VARCHAR.
--   * Idempotente: puede (re)aplicarse sin generar errores.
--   * NO se ejecuta automáticamente. Debe aplicarse manualmente en bases con
--     datos previos. En entornos nuevos, Base.metadata.create_all() crea las
--     tablas y app/db/seeds.py siembra los datos al arrancar la aplicación;
--     en ese caso esta migración no es necesaria.
--
-- Orden de aplicación (importante): crear primero roles/modulos_sistema y
-- sembrar roles antes de rellenar usuarios.rol_id, porque el backfill depende
-- de que los roles ya existan.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1) Tabla roles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id          serial PRIMARY KEY,
    nombre      varchar(50)  NOT NULL,
    descripcion varchar(200),
    estado      boolean      NOT NULL DEFAULT true,
    creado      timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_nombre_estado
    ON roles (nombre) WHERE estado;

-- ----------------------------------------------------------------------------
-- 2) Tabla modulos_sistema
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS modulos_sistema (
    id          serial PRIMARY KEY,
    nombre      varchar(50)  NOT NULL,
    descripcion varchar(200),
    ruta        varchar(150),
    icono       varchar(100),
    estado      boolean      NOT NULL DEFAULT true,
    creado      timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_modulos_sistema_nombre_estado
    ON modulos_sistema (nombre) WHERE estado;

-- ----------------------------------------------------------------------------
-- 3) Tabla modulos_x_rol
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS modulos_x_rol (
    id          serial PRIMARY KEY,
    rol_id      integer   NOT NULL REFERENCES roles (id),
    modulo_id   integer   NOT NULL REFERENCES modulos_sistema (id),
    estado      boolean   NOT NULL DEFAULT true,
    creado      timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_modulos_x_rol_rol_modulo
    ON modulos_x_rol (rol_id, modulo_id) WHERE estado;

-- ----------------------------------------------------------------------------
-- 4) Siembra de roles (idempotente)
-- ----------------------------------------------------------------------------
INSERT INTO roles (nombre)
SELECT v.nombre
FROM (VALUES ('ADMINISTRADOR'), ('DOCENTE'), ('ESTUDIANTE')) AS v(nombre)
WHERE NOT EXISTS (
    SELECT 1 FROM roles r WHERE r.nombre = v.nombre AND r.estado
);

-- ----------------------------------------------------------------------------
-- 5) Siembra de módulos del sistema (idempotente)
-- ----------------------------------------------------------------------------
INSERT INTO modulos_sistema (nombre, descripcion, ruta, icono)
SELECT v.nombre, v.descripcion, v.ruta, v.icono
FROM (VALUES
    ('DASHBOARD',              'Panel principal',                        '/dashboard',              'dashboard'),
    ('PERFIL',                 'Datos del perfil propio',                '/perfil',                 'person'),
    ('NOTIFICACIONES',         'Centro de notificaciones',               '/notificaciones',         'notifications'),
    ('MIS_SOLICITUDES',        'Solicitudes de consulta propias',        '/mis-solicitudes',        'assignment'),
    ('ATENCION_SOLICITUDES',   'Atención de solicitudes asignadas',      '/atender-solicitudes',    'support_agent'),
    ('GESTION_SOLICITUDES',    'Gestión global de solicitudes',          '/solicitudes',            'manage_search'),
    ('USUARIOS',               'Administración de usuarios',             '/usuarios',               'group'),
    ('ROLES_PERMISOS',         'Administración de roles y permisos',     '/roles-permisos',         'security'),
    ('PROGRAMAS_ASIGNATURAS',  'Programas académicos y asignaturas',     '/programas-asignaturas',  'school'),
    ('INFRAESTRUCTURA',        'Administración de infraestructura física', '/infraestructura',      'location_on'),
    ('ASIGNACION_DOCENTES',    'Asignación de docentes a módulos',       '/asignacion-docentes',    'assignment_ind'),
    ('PERIODOS_ACADEMICOS',    'Periodos académicos',                    '/periodos-academicos',    'event'),
    ('TIPOS_DOCUMENTO',        'Tipos de documento de identidad',        '/tipos-documento',        'badge'),
    ('DISPONIBILIDAD_DOCENTE', 'Disponibilidad horaria de docentes',     '/disponibilidad-docente', 'schedule'),
    ('CALIFICACIONES',         'Calificaciones de consultas',            '/calificaciones',         'star')
) AS v(nombre, descripcion, ruta, icono)
WHERE NOT EXISTS (
    SELECT 1 FROM modulos_sistema m WHERE m.nombre = v.nombre
);

-- ----------------------------------------------------------------------------
-- 6) Siembra de la matriz modulos_x_rol (idempotente)
--    ADMINISTRADOR: DASHBOARD, PERFIL, NOTIFICACIONES, GESTION_SOLICITUDES,
--                   USUARIOS, ROLES_PERMISOS, PROGRAMAS_ASIGNATURAS,
--                   INFRAESTRUCTURA, ASIGNACION_DOCENTES, PERIODOS_ACADEMICOS,
--                   TIPOS_DOCUMENTO, DISPONIBILIDAD_DOCENTE, CALIFICACIONES
--    DOCENTE:       DASHBOARD, PERFIL, NOTIFICACIONES, ATENCION_SOLICITUDES,
--                   DISPONIBILIDAD_DOCENTE, CALIFICACIONES
--    ESTUDIANTE:    DASHBOARD, PERFIL, NOTIFICACIONES, MIS_SOLICITUDES,
--                   CALIFICACIONES
-- ----------------------------------------------------------------------------
INSERT INTO modulos_x_rol (rol_id, modulo_id)
SELECT r.id, m.id
FROM (VALUES
    ('ADMINISTRADOR', 'DASHBOARD'),
    ('ADMINISTRADOR', 'PERFIL'),
    ('ADMINISTRADOR', 'NOTIFICACIONES'),
    ('ADMINISTRADOR', 'GESTION_SOLICITUDES'),
    ('ADMINISTRADOR', 'USUARIOS'),
    ('ADMINISTRADOR', 'ROLES_PERMISOS'),
    ('ADMINISTRADOR', 'PROGRAMAS_ASIGNATURAS'),
    ('ADMINISTRADOR', 'INFRAESTRUCTURA'),
    ('ADMINISTRADOR', 'ASIGNACION_DOCENTES'),
    ('ADMINISTRADOR', 'PERIODOS_ACADEMICOS'),
    ('ADMINISTRADOR', 'TIPOS_DOCUMENTO'),
    ('ADMINISTRADOR', 'DISPONIBILIDAD_DOCENTE'),
    ('ADMINISTRADOR', 'CALIFICACIONES'),
    ('DOCENTE',       'DASHBOARD'),
    ('DOCENTE',       'PERFIL'),
    ('DOCENTE',       'NOTIFICACIONES'),
    ('DOCENTE',       'ATENCION_SOLICITUDES'),
    ('DOCENTE',       'DISPONIBILIDAD_DOCENTE'),
    ('DOCENTE',       'CALIFICACIONES'),
    ('ESTUDIANTE',    'DASHBOARD'),
    ('ESTUDIANTE',    'PERFIL'),
    ('ESTUDIANTE',    'NOTIFICACIONES'),
    ('ESTUDIANTE',    'MIS_SOLICITUDES'),
    ('ESTUDIANTE',    'CALIFICACIONES')
) AS v(rol_nombre, modulo_nombre)
JOIN roles r           ON r.nombre = v.rol_nombre
JOIN modulos_sistema m ON m.nombre = v.modulo_nombre
WHERE NOT EXISTS (
    SELECT 1 FROM modulos_x_rol mxr
    WHERE mxr.rol_id = r.id AND mxr.modulo_id = m.id AND mxr.estado
);

-- ----------------------------------------------------------------------------
-- 7) usuarios.rol_id: agregar, rellenar desde el enum antiguo y validar
-- ----------------------------------------------------------------------------
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol_id integer;

-- Backfill desde la columna de enum previa (si aún existe).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'usuarios' AND column_name = 'rol'
    ) THEN
        EXECUTE '
            UPDATE usuarios u
            SET rol_id = r.id
            FROM roles r
            WHERE u.rol_id IS NULL AND r.nombre = u.rol::text';
    END IF;
END $$;

-- Respaldo: cualquier usuario sin rol se asigna a ESTUDIANTE.
UPDATE usuarios u
SET rol_id = r.id
FROM roles r
WHERE u.rol_id IS NULL AND r.nombre = 'ESTUDIANTE';

ALTER TABLE usuarios ALTER COLUMN rol_id SET NOT NULL;

-- FK hacia roles (solo si no existe ya).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_schema = current_schema()
          AND table_name = 'usuarios'
          AND constraint_type = 'FOREIGN KEY'
          AND constraint_name = 'fk_usuarios_rol'
    ) THEN
        ALTER TABLE usuarios
            ADD CONSTRAINT fk_usuarios_rol FOREIGN KEY (rol_id) REFERENCES roles (id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_usuarios_rol_id ON usuarios (rol_id);

-- Eliminar la columna de enum antigua (ya reemplazada por rol_id).
ALTER TABLE usuarios DROP COLUMN IF EXISTS rol;

-- ----------------------------------------------------------------------------
-- 8) Triggers de actualizado para las nuevas tablas (reusa set_actualizado())
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['roles', 'modulos_sistema', 'modulos_x_rol']
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%s_actualizado ON %I', t, t);
        EXECUTE format(
            'CREATE TRIGGER trg_%s_actualizado BEFORE UPDATE ON %I '
            'FOR EACH ROW EXECUTE FUNCTION set_actualizado()',
            t, t
        );
    END LOOP;
END $$;

-- ----------------------------------------------------------------------------
-- Verificación sugerida:
--   SELECT nombre FROM roles ORDER BY id;
--   SELECT nombre FROM modulos_sistema ORDER BY id;
--   SELECT r.nombre AS rol, m.nombre AS modulo
--     FROM modulos_x_rol mxr
--     JOIN roles r ON r.id = mxr.rol_id
--     JOIN modulos_sistema m ON m.id = mxr.modulo_id
--    ORDER BY r.nombre, m.nombre;
--   SELECT u.id, u.correo, r.nombre AS rol
--     FROM usuarios u JOIN roles r ON r.id = u.rol_id ORDER BY u.id;
--
-- Rollback (devuelve el estado previo, sin ejecutar automáticamente):
--   - ALTER TABLE usuarios ADD COLUMN rol varchar(20);
--   - UPDATE usuarios u SET rol = r.nombre FROM roles r WHERE r.id = u.rol_id;
--   - ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS fk_usuarios_rol;
--   - ALTER TABLE usuarios DROP COLUMN IF EXISTS rol_id;
--   - DROP TABLE IF EXISTS modulos_x_rol, modulos_sistema, roles;
-- ============================================================================

COMMIT;