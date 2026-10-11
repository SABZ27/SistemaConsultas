-- ============================================================================
-- Esquema de infraestructura fisica (MySQL 8, InnoDB, utf8mb4)
-- ============================================================================
-- Tablas: sedes, zonas, recursos_fisicos.
--
-- Todas las tablas incluyen:
--   * id             INT UNSIGNED PK AUTO_INCREMENT (llave primaria)
--   * estado         TINYINT(1) NOT NULL DEFAULT 1 (borrado logico; 0 = eliminado)
--   * creado         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
--   * actualizado    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
--                    ON UPDATE CURRENT_TIMESTAMP
--   * al menos un indice unico
--
-- Los indices unicos usan columnas generadas (nombre_activo, zona_key) que
-- valen NULL cuando la fila esta inactiva, de modo que el borrado logico
-- libera el valor unico y permite reactivar reutilizando el mismo nombre.
--
-- Estructuras de sede:
--   * BLOQUES: la sede se divide en bloques (A, B, C...); los recursos
--              cuelgan de una zona (bloque).
--   * SALONES: sin subdivision; los recursos (Salon 1..30) cuelgan de la sede.
--   * PISOS:   el edificio se divide en pisos; los recursos cuelgan de un piso.
--
-- Este archivo es idempotente (CREATE TABLE IF NOT EXISTS) y es el que monta
-- docker-compose para inicializar la base. No se siembran datos.
-- ============================================================================

CREATE TABLE IF NOT EXISTS sedes (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(100)    NOT NULL,
    tipo_estructura ENUM('BLOQUES', 'SALONES', 'PISOS') NOT NULL,
    estado          TINYINT(1)      NOT NULL DEFAULT 1,
    creado          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    nombre_activo   VARCHAR(100) GENERATED ALWAYS AS (IF(estado = 1, nombre, NULL)) STORED,
    PRIMARY KEY (id),
    UNIQUE KEY uq_sedes_nombre_activo (nombre_activo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS zonas (
    id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    sede_id       INT UNSIGNED NOT NULL,
    nombre        VARCHAR(100) NOT NULL,
    estado        TINYINT(1)   NOT NULL DEFAULT 1,
    creado        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    nombre_activo VARCHAR(100) GENERATED ALWAYS AS (IF(estado = 1, nombre, NULL)) STORED,
    PRIMARY KEY (id),
    UNIQUE KEY uq_zonas_sede_nombre_activo (sede_id, nombre_activo),
    -- Necesario para la FK compuesta de recursos_fisicos (zona_id, sede_id).
    UNIQUE KEY uq_zonas_id_sede (id, sede_id),
    CONSTRAINT fk_zonas_sede FOREIGN KEY (sede_id) REFERENCES sedes (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recursos_fisicos (
    id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    sede_id       INT UNSIGNED NOT NULL,
    zona_id       INT UNSIGNED NULL,
    nombre        VARCHAR(100) NOT NULL,
    tipo          ENUM('SALON', 'LABORATORIO', 'AUDITORIO', 'SALA', 'OFICINA')
                  NOT NULL DEFAULT 'SALON',
    estado        TINYINT(1)   NOT NULL DEFAULT 1,
    creado        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    nombre_activo VARCHAR(100) GENERATED ALWAYS AS (IF(estado = 1, nombre, NULL)) STORED,
    -- En MySQL, un indice UNIQUE normal no evita duplicados cuando hay NULL.
    -- zona_key reemplaza NULL por 0 para que el unico cubra las sedes sin zonas.
    zona_key      INT UNSIGNED GENERATED ALWAYS AS (IFNULL(zona_id, 0)) STORED,
    PRIMARY KEY (id),
    UNIQUE KEY uq_recursos_sede_zona_nombre (sede_id, zona_key, nombre_activo),
    CONSTRAINT fk_recursos_sede FOREIGN KEY (sede_id) REFERENCES sedes (id),
    -- FK compuesta: garantiza que la zona pertenece a la misma sede.
    -- Si zona_id es NULL, MySQL (MATCH SIMPLE) no evalua la restriccion.
    CONSTRAINT fk_recursos_zona_sede
        FOREIGN KEY (zona_id, sede_id) REFERENCES zonas (id, sede_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
