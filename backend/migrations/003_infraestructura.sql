-- ============================================================================
-- Migración 003: Infraestructura como servicio externo (Fase 4)
-- ============================================================================
-- Contexto: la infraestructura física (sedes, bloques/zonas y recursos) deja
-- de vivir en PostgreSQL (FastAPI) y pasa a un microservicio aparte
-- (Express + MySQL, carpeta infraestructura-service). Por eso:
--
--   1) solicitudes_consultas.recurso_fisico_id deja de tener FK: el recurso
--      ahora pertenece a otra base de datos (MySQL), por lo que no puede
--      existir integridad referencial entre ambos motores.
--
--   2) Se agrega solicitudes_consultas.recurso_fisico_nombre, que guarda una
--      COPIA de la ubicación completa del recurso (formato
--      "Sede · Bloque · Recurso") al momento de asignarlo. Decisión
--      deliberada: evita llamar al servicio externo al listar solicitudes y
--      conserva el historial aunque el recurso cambie o desaparezca
--      ("Salón 3" solo es ambiguo entre sedes).
--
--   3) Se rellenan (backfill) las solicitudes existentes que ya tengan
--      recurso_fisico_id, recomponiendo la ubicación por JOIN con las tablas
--      antiguas de infraestructura (que aún existen cuando corre esta
--      migración).
--
--   4) Se documenta, SIN ejecutar, el DROP final de las 3 tablas de
--      infraestructura de PostgreSQL. Ese paso es MANUAL y debe hacerse solo
--      tras respaldar la base y una vez que el microservicio esté operativo.
--
-- Características:
--   * Idioma objetivo: PostgreSQL (Neon).
--   * Idempotente: puede (re)aplicarse sin generar errores (usa to_regclass
--     para no fallar si las tablas antiguas ya fueron eliminadas).
--   * NO se ejecuta automáticamente. En un entorno nuevo,
--     Base.metadata.create_all() ya crea la columna recurso_fisico_nombre y
--     el recurso_fisico_id SIN FK (el modelo no declara ForeignKey), por lo
--     que esta migración solo es necesaria en bases con datos previos.
--   * La infraestructura nace VACÍA en MySQL: no se exportan datos de
--     PostgreSQL a MySQL desde esta migración.
--
-- Rutas retiradas: /sedes, /bloques y /recursos-fisicos de FastAPI dejan de
-- existir. Los clientes antiguos que usaban /bloques deben migrar a /zonas
-- del microservicio de infraestructura (Express).
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1) Nombre/ubicación del recurso físico (copia al asignar)
-- ----------------------------------------------------------------------------
ALTER TABLE solicitudes_consultas
    ADD COLUMN IF NOT EXISTS recurso_fisico_nombre varchar(200);

-- Backfill: "Sede · Bloque · Recurso" para las solicitudes que ya tenían un
-- recurso asignado. concat_ws omite los NULL automáticamente.
DO $$
BEGIN
    IF to_regclass('recursos_fisicos') IS NOT NULL
       AND to_regclass('bloques') IS NOT NULL
       AND to_regclass('sedes') IS NOT NULL THEN
        EXECUTE '
            UPDATE solicitudes_consultas s
            SET recurso_fisico_nombre =
                concat_ws('' · '', sd.nombre, b.nombre, rf.nombre)
            FROM recursos_fisicos rf
            JOIN bloques b ON b.id = rf.bloque_id
            JOIN sedes sd  ON sd.id = b.sede_id
            WHERE s.recurso_fisico_id = rf.id
              AND s.recurso_fisico_nombre IS NULL';
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 2) Eliminar la FK de solicitudes_consultas.recurso_fisico_id
--    (la columna se conserva: entero nullable sin integridad referencial)
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    fk text;
BEGIN
    IF to_regclass('recursos_fisicos') IS NOT NULL THEN
        FOR fk IN
            SELECT con.conname
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = current_schema()
              AND rel.relname = 'solicitudes_consultas'
              AND con.contype = 'f'
              AND con.confrelid = to_regclass('recursos_fisicos')
        LOOP
            EXECUTE format(
                'ALTER TABLE solicitudes_consultas DROP CONSTRAINT %I', fk
            );
        END LOOP;
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 3) DROP de las 3 tablas antiguas de infraestructura en PostgreSQL.
--    ¡NO EJECUTAR AÚN! Es un paso MANUAL, SOLO tras respaldar la base de
--    datos y confirmar que el microservicio (Express + MySQL) está operativo.
--    Se deja documentado y comentado a propósito; la infraestructura se
--    administra desde MySQL a partir de la Fase 3.
-- ----------------------------------------------------------------------------
-- BACKUP PREVIO OBLIGATORIO (ejemplo):
--   pg_dump "$DB_URL" -t sedes -t bloques -t recursos_fisicos -f infra_pg.sql
--
-- Luego, el paso final manual (descomentar y ejecutar aparte, NO aquí):
--   DROP TABLE IF EXISTS recursos_fisicos, bloques, sedes;

-- ----------------------------------------------------------------------------
-- Verificación sugerida:
--   SELECT column_name FROM information_schema.columns
--    WHERE table_schema = current_schema()
--      AND table_name = 'solicitudes_consultas'
--      AND column_name = 'recurso_fisico_nombre';
--
--   -- Debe devolver 0 filas: ya no hay FK hacia recursos_fisicos.
--   SELECT con.conname
--     FROM pg_constraint con
--     JOIN pg_class rel ON rel.oid = con.conrelid
--    WHERE rel.relname = 'solicitudes_consultas'
--      AND con.contype = 'f'
--      AND con.confrelid = to_regclass('recursos_fisicos');
--
--   SELECT id, recurso_fisico_id, recurso_fisico_nombre
--     FROM solicitudes_consultas
--    WHERE recurso_fisico_id IS NOT NULL;
--
-- Rollback (devuelve el estado previo, sin ejecutar automáticamente):
--   - ALTER TABLE solicitudes_consultas
--       ADD CONSTRAINT fk_solicitudes_recurso_fisico
--       FOREIGN KEY (recurso_fisico_id) REFERENCES recursos_fisicos (id);
--   - ALTER TABLE solicitudes_consultas DROP COLUMN IF EXISTS recurso_fisico_nombre;
-- ============================================================================

COMMIT;
