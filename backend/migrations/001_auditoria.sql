-- ============================================================================
-- Migración 001: Auditoría, estados y unicidad parcial
-- ============================================================================
-- Objetivo: llevar un esquema creado por las versiones previas del backend
-- FastAPI al modelo de la Fase 1:
--
--   1) solicitudes_consultas.estado            -> estado_consulta
--   2) activo -> estado                          (demás tablas que tenían activo)
--   3) fecha_creacion -> creado                  (con los valores ya existentes)
--   4) columnas faltantes de auditoría (estado/creado/actualizado)
--      y columna codigo (UUID v4) en comentarios, notificaciones y
--      eventos_solicitud
--   5) backfill de codigo con gen_random_uuid()
--   6) índices únicos parciales WHERE estado = true
--   7) función set_actualizado() y triggers BEFORE UPDATE por tabla
--
-- Características:
--   * Idioma objetivo: PostgreSQL (Neon). SQLAlchemy de la aplicación usa
--     "native_enum=False", por lo que las columnas de enums son VARCHAR.
--   * Idempotente: se puede (re)aplicar varias veces sin generar errores.
--   * NO se ejecuta automáticamente. Debe aplicarse manualmente en la base de
--     datos antes de desplegar el código de la Fase 1, o bien crearse el
--     esquema limpio con Base.metadata.create_all() y aplicar solo los pasos
--     finales (índices y triggers) para un entorno nuevo.
--   * En entornos nuevos, create_all() genera las columnas de AuditoriaMixin
--     (estado/creado/actualizado) y los índices parciales directamente; la
--     migración es necesaria únicamente para bases con datos previos.
--   * gen_random_uuid() está disponible en PostgreSQL 13+ de forma nativa.
--
-- Orden de aplicación (importante): se renombra primero el enum de estado de
-- solicitudes_consultas para que, al agregar después la columna booleana
-- "estado" de AuditoriaMixin, no exista conflicto de nombres.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1) solicitudes_consultas: estado (enum del flujo) -> estado_consulta
--    Se ejecuta ANTES de agregar el booleano "estado" de AuditoriaMixin.
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'solicitudes_consultas'
          AND column_name = 'estado'
    ) THEN
        ALTER TABLE solicitudes_consultas RENAME COLUMN estado TO estado_consulta;
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 2) activo -> estado en las tablas que hoy lo usan
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'programas_academicos' AND column_name = 'activo'
    ) THEN
        ALTER TABLE programas_academicos RENAME COLUMN activo TO estado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'usuarios' AND column_name = 'activo'
    ) THEN
        ALTER TABLE usuarios RENAME COLUMN activo TO estado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'modulos' AND column_name = 'activo'
    ) THEN
        ALTER TABLE modulos RENAME COLUMN activo TO estado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'sedes' AND column_name = 'activo'
    ) THEN
        ALTER TABLE sedes RENAME COLUMN activo TO estado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'bloques' AND column_name = 'activo'
    ) THEN
        ALTER TABLE bloques RENAME COLUMN activo TO estado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'recursos_fisicos' AND column_name = 'activo'
    ) THEN
        ALTER TABLE recursos_fisicos RENAME COLUMN activo TO estado;
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 3) fecha_creacion -> creado (conserva los valores existentes)
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'usuarios' AND column_name = 'fecha_creacion'
    ) THEN
        ALTER TABLE usuarios RENAME COLUMN fecha_creacion TO creado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'solicitudes_consultas' AND column_name = 'fecha_creacion'
    ) THEN
        ALTER TABLE solicitudes_consultas RENAME COLUMN fecha_creacion TO creado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'comentarios' AND column_name = 'fecha_creacion'
    ) THEN
        ALTER TABLE comentarios RENAME COLUMN fecha_creacion TO creado;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'notificaciones' AND column_name = 'fecha_creacion'
    ) THEN
        ALTER TABLE notificaciones RENAME COLUMN fecha_creacion TO creado;
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 4) Columnas faltantes de AuditoriaMixin en las 11 tablas
--    (estado/creado/actualizado). "ADD COLUMN IF NOT EXISTS" es idempotente.
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'programas_academicos',
        'usuarios',
        'modulos',
        'sedes',
        'bloques',
        'recursos_fisicos',
        'solicitudes_consultas',
        'comentarios',
        'eventos_solicitud',
        'notificaciones',
        'password_reset_tokens'
    ]
    LOOP
        EXECUTE format(
            'ALTER TABLE %I ADD COLUMN IF NOT EXISTS estado boolean NOT NULL DEFAULT true', t
        );
        EXECUTE format(
            'ALTER TABLE %I ADD COLUMN IF NOT EXISTS creado timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP', t
        );
        EXECUTE format(
            'ALTER TABLE %I ADD COLUMN IF NOT EXISTS actualizado timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP', t
        );
    END LOOP;
END $$;

-- ----------------------------------------------------------------------------
-- 5) codigo (UUID v4, String(36)) en comentarios, notificaciones y
--    eventos_solicitud, con backfill de los registros existentes.
-- ----------------------------------------------------------------------------
ALTER TABLE comentarios ADD COLUMN IF NOT EXISTS codigo varchar(36);
UPDATE comentarios SET codigo = gen_random_uuid()::text WHERE codigo IS NULL;
ALTER TABLE comentarios ALTER COLUMN codigo SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_comentarios_codigo ON comentarios (codigo);

ALTER TABLE notificaciones ADD COLUMN IF NOT EXISTS codigo varchar(36);
UPDATE notificaciones SET codigo = gen_random_uuid()::text WHERE codigo IS NULL;
ALTER TABLE notificaciones ALTER COLUMN codigo SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_notificaciones_codigo ON notificaciones (codigo);

ALTER TABLE eventos_solicitud ADD COLUMN IF NOT EXISTS codigo varchar(36);
UPDATE eventos_solicitud SET codigo = gen_random_uuid()::text WHERE codigo IS NULL;
ALTER TABLE eventos_solicitud ALTER COLUMN codigo SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_eventos_solicitud_codigo ON eventos_solicitud (codigo);

-- ----------------------------------------------------------------------------
-- 6) Índices únicos parciales: permiten "reutilizar" nombre/correo/
--    identificación de registros desactivados (estado = false).
-- ----------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS uq_programas_academicos_nombre_estado
    ON programas_academicos (nombre) WHERE estado;
CREATE UNIQUE INDEX IF NOT EXISTS uq_modulos_nombre_estado
    ON modulos (nombre) WHERE estado;
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_correo_estado
    ON usuarios (correo) WHERE estado;
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_identificacion_estado
    ON usuarios (identificacion) WHERE estado;

-- ----------------------------------------------------------------------------
-- 7) Función y triggers que mantienen "actualizado" a nivel de base de datos.
--    Aplica a las 11 tablas actuales y a cualquier tabla futura que se agregue
--    arrancando la aplicación (ver app/db/session.py: init_db).
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_actualizado()
RETURNS trigger AS $$
BEGIN
    NEW.actualizado = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'programas_academicos',
        'usuarios',
        'modulos',
        'sedes',
        'bloques',
        'recursos_fisicos',
        'solicitudes_consultas',
        'comentarios',
        'eventos_solicitud',
        'notificaciones',
        'password_reset_tokens'
    ]
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
--   SELECT table_name, column_name FROM information_schema.columns
--   WHERE table_schema = current_schema()
--     AND column_name IN ('estado','creado','actualizado','estado_consulta')
--   ORDER BY table_name, column_name;
--
-- Rollback (devuelve el estado previo, sin ejecutar automáticamente):
--   - Renombrar de vuelta "estado_consulta"/"estado"/"creado" y eliminar las
--     columnas agregadas y los índices creados manualmente.
-- ============================================================================

COMMIT;