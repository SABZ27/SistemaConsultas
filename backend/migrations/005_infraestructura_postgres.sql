-- 005_infraestructura_postgres.sql
-- Fase 1: sedes, zonas y recursos_fisicos pasan del microservicio Express (MySQL)
-- a PostgreSQL (FastAPI).
-- Archivo de referencia: la aplicación NO lo ejecuta. Aplicarlo a mano (psql) antes
-- o después del despliegue; es autocontenido e idempotente (se puede correr N veces).

BEGIN;

-- (a) Tablas nuevas + índices únicos + trigger de actualizado
CREATE TABLE IF NOT EXISTS sedes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo_estructura VARCHAR(50) NOT NULL DEFAULT 'BLOQUES',
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sedes_nombre_estado
    ON sedes (nombre) WHERE estado;

CREATE TABLE IF NOT EXISTS zonas (
    id SERIAL PRIMARY KEY,
    sede_id INTEGER NOT NULL REFERENCES sedes (id) ON UPDATE CASCADE ON DELETE RESTRICT,
    nombre VARCHAR(100) NOT NULL,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_zonas_sede_nombre_estado
    ON zonas (sede_id, nombre) WHERE estado;

CREATE TABLE IF NOT EXISTS recursos_fisicos (
    id SERIAL PRIMARY KEY,
    sede_id INTEGER NOT NULL REFERENCES sedes (id) ON UPDATE CASCADE ON DELETE RESTRICT,
    zona_id INTEGER REFERENCES zonas (id) ON UPDATE CASCADE ON DELETE RESTRICT,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'SALON',
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_recursos_sede_zona_nombre_estado
    ON recursos_fisicos (sede_id, zona_id, nombre) WHERE estado;

CREATE OR REPLACE FUNCTION set_actualizado()
RETURNS trigger AS $$
BEGIN
    NEW.actualizado = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sedes_actualizado ON sedes;
CREATE TRIGGER trg_sedes_actualizado
    BEFORE UPDATE ON sedes FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_zonas_actualizado ON zonas;
CREATE TRIGGER trg_zonas_actualizado
    BEFORE UPDATE ON zonas FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_recursos_fisicos_actualizado ON recursos_fisicos;
CREATE TRIGGER trg_recursos_fisicos_actualizado
    BEFORE UPDATE ON recursos_fisicos FOR EACH ROW EXECUTE FUNCTION set_actualizado();

-- (b) Los ids de recurso apuntaban a recursos del microservicio Express (MySQL),
-- que ya no existen: se limpian el id y la copia de la ubicación.
UPDATE solicitudes_consultas
SET recurso_fisico_id = NULL,
    recurso_fisico_nombre = NULL
WHERE recurso_fisico_id IS NOT NULL
   OR recurso_fisico_nombre IS NOT NULL;

-- (c) FK real de solicitudes_consultas.recurso_fisico_id (solo si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_solicitudes_recurso_fisico'
          AND conrelid = 'solicitudes_consultas'::regclass
    ) THEN
        ALTER TABLE solicitudes_consultas
            ADD CONSTRAINT fk_solicitudes_recurso_fisico
            FOREIGN KEY (recurso_fisico_id) REFERENCES recursos_fisicos (id)
            ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;
END $$;

COMMIT;
