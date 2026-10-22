-- ============================================================================
-- Esquema de servicios externos (MySQL 8, InnoDB, utf8mb4)
-- ============================================================================
-- Tablas: servicios_externos, consultas_servicio_externo, festivos,
--         correos_enviados.
--
-- La infraestructura fisica (sedes, zonas, recursos_fisicos) vive en
-- PostgreSQL dentro de FastAPI. Este servicio solo resuelve datos de terceros:
--   * Nager.Date -> dias festivos
--   * Brevo      -> correo transaccional (API HTTP, no SMTP)
--
-- El orden de creacion importa por las claves foraneas.
-- Es idempotente: CREATE TABLE IF NOT EXISTS.
-- ============================================================================

CREATE TABLE IF NOT EXISTS servicios_externos (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL,
  url_base VARCHAR(255) NOT NULL,
  descripcion VARCHAR(255) NULL,
  estado TINYINT(1) NOT NULL DEFAULT 1,
  creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uq_servicios_externos_nombre UNIQUE (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS consultas_servicio_externo (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  servicio_id BIGINT UNSIGNED NOT NULL,
  referencia CHAR(36) NOT NULL,
  endpoint VARCHAR(255) NOT NULL,
  codigo_http SMALLINT NULL,
  exito TINYINT(1) NOT NULL DEFAULT 0,
  duracion_ms INT UNSIGNED NULL,
  detalle VARCHAR(255) NULL,
  estado TINYINT(1) NOT NULL DEFAULT 1,
  creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uq_consultas_servicio_referencia UNIQUE (referencia),
  CONSTRAINT fk_consultas_servicio FOREIGN KEY (servicio_id)
    REFERENCES servicios_externos (id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS festivos (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  servicio_id BIGINT UNSIGNED NOT NULL,
  consulta_servicio_id BIGINT UNSIGNED NULL,
  fecha DATE NOT NULL,
  pais CHAR(2) NOT NULL DEFAULT 'CO',
  nombre VARCHAR(150) NOT NULL,
  anio SMALLINT NOT NULL,
  estado TINYINT(1) NOT NULL DEFAULT 1,
  creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uq_festivos_fecha_pais UNIQUE (fecha, pais),
  KEY idx_festivos_anio (anio),
  CONSTRAINT fk_festivos_servicio FOREIGN KEY (servicio_id)
    REFERENCES servicios_externos (id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_festivos_consulta FOREIGN KEY (consulta_servicio_id)
    REFERENCES consultas_servicio_externo (id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS correos_enviados (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  servicio_id BIGINT UNSIGNED NOT NULL,
  consulta_servicio_id BIGINT UNSIGNED NOT NULL,
  destinatario VARCHAR(150) NOT NULL,
  asunto VARCHAR(200) NOT NULL,
  estado_envio ENUM('ENVIADO','FALLIDO') NOT NULL,
  respuesta_proveedor VARCHAR(255) NULL,
  estado TINYINT(1) NOT NULL DEFAULT 1,
  creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uq_correos_consulta UNIQUE (consulta_servicio_id),
  CONSTRAINT fk_correos_servicio FOREIGN KEY (servicio_id)
    REFERENCES servicios_externos (id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_correos_consulta FOREIGN KEY (consulta_servicio_id)
    REFERENCES consultas_servicio_externo (id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
