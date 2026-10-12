-- ========================================================
-- MIGRACIÓN 004: Tablas nuevas (Fase 5)
-- ========================================================
--
-- Objetivo: Crear las tablas docentes_modulos, tipos_documento,
-- calificaciones_consulta, periodos_academicos y disponibilidad_docente
-- con los campos de auditoría y restricciones parciales idempotentes.
-- Esta migración NO se ejecuta (solo se documenta).
-- ========================================================
--
-- Notas:
-- - Se asume PostgreSQL. Para SQLite se mantiene la misma semántica lógica.
-- - Índices únicos parciales usan "WHERE estado" para permitir reactivación.
-- - Se incluyen CHECKs y claves foráneas.
--
-- ========================================================

-- 1. TIPOS_DOCUMENTO
CREATE TABLE IF NOT EXISTS tipos_documento (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    sigla VARCHAR(10) NOT NULL,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_tipos_documento_nombre_estado
    ON tipos_documento (nombre)
    WHERE estado;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tipos_documento_sigla_estado
    ON tipos_documento (sigla)
    WHERE estado;

-- 2. DOCENTES_MODULOS
CREATE TABLE IF NOT EXISTS docentes_modulos (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id),
    modulo_id INTEGER NOT NULL REFERENCES modulos(id),
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_docentes_modulos_docente_modulo
    ON docentes_modulos (docente_id, modulo_id)
    WHERE estado;

-- 3. PERIODOS_ACADEMICOS
CREATE TABLE IF NOT EXISTS periodos_academicos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_periodos_academicos_rango CHECK (fecha_fin > fecha_inicio)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_periodos_academicos_nombre_estado
    ON periodos_academicos (nombre)
    WHERE estado;

-- 4. DISPONIBILIDAD_DOCENTE
CREATE TABLE IF NOT EXISTS disponibilidad_docente (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id),
    dia_semana SMALLINT NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_disponibilidad_docente_dia_semana CHECK (dia_semana >= 1 AND dia_semana <= 7),
    CONSTRAINT ck_disponibilidad_docente_horas CHECK (hora_fin > hora_inicio)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_disponibilidad_docente_docente_dia_hora
    ON disponibilidad_docente (docente_id, dia_semana, hora_inicio)
    WHERE estado;

-- 5. CALIFICACIONES_CONSULTA
CREATE TABLE IF NOT EXISTS calificaciones_consulta (
    id SERIAL PRIMARY KEY,
    solicitud_id INTEGER NOT NULL REFERENCES solicitudes_consultas(id),
    puntaje SMALLINT NOT NULL,
    comentario TEXT,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_calificaciones_consulta_puntaje CHECK (puntaje >= 1 AND puntaje <= 5)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_calificaciones_consulta_solicitud
    ON calificaciones_consulta (solicitud_id)
    WHERE estado;

-- 6. COLUNNA USUARIOS
-- Se agrega tipo_documento_id a usuarios (nullable)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'usuarios'
          AND column_name = 'tipo_documento_id'
    ) THEN
        ALTER TABLE usuarios
            ADD COLUMN tipo_documento_id INTEGER REFERENCES tipos_documento(id);
    END IF;
END
$$;

-- ========================================================
-- FIN MIGRACIÓN 004
-- ========================================================
