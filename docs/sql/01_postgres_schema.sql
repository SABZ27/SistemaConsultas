-- ============================================================================
-- Esquema PostgreSQL del dominio de negocio (19 tablas)
-- ============================================================================
-- GENERADO a partir de los modelos SQLAlchemy de backend/app/models,
-- compilando el DDL con el dialecto de PostgreSQL. NO se ha conectado a
-- ninguna base de datos para generarlo.
--
-- LA FUENTE DE VERDAD SIGUE SIENDO init_db()
-- (backend/app/db/session.py): Base.metadata.create_all() seguido de
-- _crear_triggers_actualizado_postgres(). Este archivo es una instantanea
-- para entregar a un companero; NO es una migracion incremental ni sustituye
-- a las migraciones 001-005 ni a futuros cambios de esquema. Si los modelos
-- cambian, hay que regenerar este archivo, no editarlo a mano.
--
-- Orden: Base.metadata.sorted_tables (orden topologico por claves foraneas),
-- el mismo que usa create_all(). Despues, la funcion y un trigger por tabla.
-- Idempotente donde es posible: CREATE TABLE/INDEX IF NOT EXISTS,
-- CREATE OR REPLACE FUNCTION y DROP TRIGGER IF EXISTS.
-- Unicos parciales: CREATE UNIQUE INDEX ... WHERE estado.
-- Enums: VARCHAR(50) (native_enum=False), no tipos ENUM nativos.
-- PostgreSQL 15+ asumido (Neon no fija la version en el repositorio).
-- Sin datos reales, contraseñas, correos personales ni usuario administrador.
-- ============================================================================


-- modulos
CREATE TABLE IF NOT EXISTS modulos (
	id SERIAL NOT NULL, 
	nombre VARCHAR(150) NOT NULL, 
	descripcion VARCHAR(500), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_modulos_nombre_estado ON modulos (nombre) WHERE estado;

-- modulos_sistema
CREATE TABLE IF NOT EXISTS modulos_sistema (
	id SERIAL NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	descripcion VARCHAR(200), 
	ruta VARCHAR(150), 
	icono VARCHAR(100), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_modulos_sistema_nombre_estado ON modulos_sistema (nombre) WHERE estado;

-- periodos_academicos
CREATE TABLE IF NOT EXISTS periodos_academicos (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	fecha_inicio DATE NOT NULL, 
	fecha_fin DATE NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_periodos_academicos_rango CHECK (fecha_fin > fecha_inicio)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_periodos_academicos_nombre_estado ON periodos_academicos (nombre) WHERE estado;

-- programas_academicos
CREATE TABLE IF NOT EXISTS programas_academicos (
	id SERIAL NOT NULL, 
	nombre VARCHAR(150) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_programas_academicos_nombre_estado ON programas_academicos (nombre) WHERE estado;

-- roles
CREATE TABLE IF NOT EXISTS roles (
	id SERIAL NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	descripcion VARCHAR(200), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_nombre_estado ON roles (nombre) WHERE estado;

-- sedes
CREATE TABLE IF NOT EXISTS sedes (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	tipo_estructura VARCHAR(50) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sedes_nombre_estado ON sedes (nombre) WHERE estado;

-- tipos_documento
CREATE TABLE IF NOT EXISTS tipos_documento (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	sigla VARCHAR(10) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_tipos_documento_nombre_estado ON tipos_documento (nombre) WHERE estado;
CREATE UNIQUE INDEX IF NOT EXISTS uq_tipos_documento_sigla_estado ON tipos_documento (sigla) WHERE estado;

-- modulos_x_rol
CREATE TABLE IF NOT EXISTS modulos_x_rol (
	id SERIAL NOT NULL, 
	rol_id INTEGER NOT NULL, 
	modulo_id INTEGER NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rol_id) REFERENCES roles (id), 
	FOREIGN KEY(modulo_id) REFERENCES modulos_sistema (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_modulos_x_rol_rol_modulo ON modulos_x_rol (rol_id, modulo_id) WHERE estado;

-- usuarios
CREATE TABLE IF NOT EXISTS usuarios (
	id SERIAL NOT NULL, 
	identificacion VARCHAR(20) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	apellido VARCHAR(100) NOT NULL, 
	correo VARCHAR(150) NOT NULL, 
	password VARCHAR(255) NOT NULL, 
	rol_id INTEGER NOT NULL, 
	programa_id INTEGER, 
	tipo_documento_id INTEGER, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rol_id) REFERENCES roles (id), 
	FOREIGN KEY(programa_id) REFERENCES programas_academicos (id), 
	FOREIGN KEY(tipo_documento_id) REFERENCES tipos_documento (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_correo_estado ON usuarios (correo) WHERE estado;
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_identificacion_estado ON usuarios (identificacion) WHERE estado;

-- zonas
CREATE TABLE IF NOT EXISTS zonas (
	id SERIAL NOT NULL, 
	sede_id INTEGER NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sede_id) REFERENCES sedes (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_zonas_sede_nombre_estado ON zonas (sede_id, nombre) WHERE estado;

-- disponibilidad_docente
CREATE TABLE IF NOT EXISTS disponibilidad_docente (
	id SERIAL NOT NULL, 
	docente_id INTEGER NOT NULL, 
	dia_semana SMALLINT NOT NULL, 
	hora_inicio TIME WITHOUT TIME ZONE NOT NULL, 
	hora_fin TIME WITHOUT TIME ZONE NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_disponibilidad_docente_dia_semana CHECK (dia_semana >= 1 AND dia_semana <= 7), 
	CONSTRAINT ck_disponibilidad_docente_horas CHECK (hora_fin > hora_inicio), 
	FOREIGN KEY(docente_id) REFERENCES usuarios (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_disponibilidad_docente_docente_dia_hora ON disponibilidad_docente (docente_id, dia_semana, hora_inicio) WHERE estado;

-- docentes_modulos
CREATE TABLE IF NOT EXISTS docentes_modulos (
	id SERIAL NOT NULL, 
	docente_id INTEGER NOT NULL, 
	modulo_id INTEGER NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(docente_id) REFERENCES usuarios (id), 
	FOREIGN KEY(modulo_id) REFERENCES modulos (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_docentes_modulos_docente_modulo ON docentes_modulos (docente_id, modulo_id) WHERE estado;

-- password_reset_tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
	id SERIAL NOT NULL, 
	token VARCHAR(255) NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	fecha_expiracion TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	utilizado BOOLEAN NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (token), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

-- recursos_fisicos
CREATE TABLE IF NOT EXISTS recursos_fisicos (
	id SERIAL NOT NULL, 
	sede_id INTEGER NOT NULL, 
	zona_id INTEGER, 
	nombre VARCHAR(100) NOT NULL, 
	tipo VARCHAR(50) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sede_id) REFERENCES sedes (id), 
	FOREIGN KEY(zona_id) REFERENCES zonas (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_recursos_sede_zona_nombre_estado ON recursos_fisicos (sede_id, zona_id, nombre) WHERE estado;

-- solicitudes_consultas
CREATE TABLE IF NOT EXISTS solicitudes_consultas (
	id SERIAL NOT NULL, 
	numero_consulta VARCHAR(30) NOT NULL, 
	estado_consulta VARCHAR(50) NOT NULL, 
	prioridad VARCHAR(50) NOT NULL, 
	asunto VARCHAR(200) NOT NULL, 
	descripcion TEXT NOT NULL, 
	fecha_consulta DATE NOT NULL, 
	hora_consulta TIME WITHOUT TIME ZONE NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	docente_id INTEGER NOT NULL, 
	modulo_id INTEGER NOT NULL, 
	recurso_fisico_id INTEGER, 
	recurso_fisico_nombre VARCHAR(200), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (numero_consulta), 
	FOREIGN KEY(estudiante_id) REFERENCES usuarios (id), 
	FOREIGN KEY(docente_id) REFERENCES usuarios (id), 
	FOREIGN KEY(modulo_id) REFERENCES modulos (id), 
	FOREIGN KEY(recurso_fisico_id) REFERENCES recursos_fisicos (id)
);

-- calificaciones_consulta
CREATE TABLE IF NOT EXISTS calificaciones_consulta (
	id SERIAL NOT NULL, 
	solicitud_id INTEGER NOT NULL, 
	puntaje SMALLINT NOT NULL, 
	comentario TEXT, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_calificaciones_consulta_puntaje CHECK (puntaje >= 1 AND puntaje <= 5), 
	FOREIGN KEY(solicitud_id) REFERENCES solicitudes_consultas (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_calificaciones_consulta_solicitud ON calificaciones_consulta (solicitud_id) WHERE estado;

-- comentarios
CREATE TABLE IF NOT EXISTS comentarios (
	id SERIAL NOT NULL, 
	codigo VARCHAR(36) NOT NULL, 
	contenido TEXT NOT NULL, 
	editado BOOLEAN, 
	autor_id INTEGER NOT NULL, 
	solicitud_id INTEGER NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo), 
	FOREIGN KEY(autor_id) REFERENCES usuarios (id), 
	FOREIGN KEY(solicitud_id) REFERENCES solicitudes_consultas (id)
);

-- eventos_solicitud
CREATE TABLE IF NOT EXISTS eventos_solicitud (
	id SERIAL NOT NULL, 
	codigo VARCHAR(36) NOT NULL, 
	solicitud_id INTEGER NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	tipo_evento VARCHAR(50) NOT NULL, 
	descripcion VARCHAR(500) NOT NULL, 
	fecha_evento TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo), 
	FOREIGN KEY(solicitud_id) REFERENCES solicitudes_consultas (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

-- notificaciones
CREATE TABLE IF NOT EXISTS notificaciones (
	id SERIAL NOT NULL, 
	codigo VARCHAR(36) NOT NULL, 
	remitente_id INTEGER NOT NULL, 
	destinatario_id INTEGER NOT NULL, 
	solicitud_consulta_id INTEGER NOT NULL, 
	tipo VARCHAR(50) NOT NULL, 
	titulo VARCHAR(255) NOT NULL, 
	mensaje VARCHAR(500) NOT NULL, 
	leida BOOLEAN NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actualizado TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo), 
	FOREIGN KEY(remitente_id) REFERENCES usuarios (id), 
	FOREIGN KEY(destinatario_id) REFERENCES usuarios (id), 
	FOREIGN KEY(solicitud_consulta_id) REFERENCES solicitudes_consultas (id)
);

-- Funcion y triggers de auditoria, tal como los crea init_db() en PostgreSQL.
CREATE OR REPLACE FUNCTION set_actualizado()
RETURNS trigger AS $$
BEGIN
    NEW.actualizado = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Triggers: uno por tabla, en el mismo orden que init_db().

DROP TRIGGER IF EXISTS trg_modulos_actualizado ON modulos;
CREATE TRIGGER trg_modulos_actualizado BEFORE UPDATE ON modulos FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_modulos_sistema_actualizado ON modulos_sistema;
CREATE TRIGGER trg_modulos_sistema_actualizado BEFORE UPDATE ON modulos_sistema FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_periodos_academicos_actualizado ON periodos_academicos;
CREATE TRIGGER trg_periodos_academicos_actualizado BEFORE UPDATE ON periodos_academicos FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_programas_academicos_actualizado ON programas_academicos;
CREATE TRIGGER trg_programas_academicos_actualizado BEFORE UPDATE ON programas_academicos FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_roles_actualizado ON roles;
CREATE TRIGGER trg_roles_actualizado BEFORE UPDATE ON roles FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_sedes_actualizado ON sedes;
CREATE TRIGGER trg_sedes_actualizado BEFORE UPDATE ON sedes FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_tipos_documento_actualizado ON tipos_documento;
CREATE TRIGGER trg_tipos_documento_actualizado BEFORE UPDATE ON tipos_documento FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_modulos_x_rol_actualizado ON modulos_x_rol;
CREATE TRIGGER trg_modulos_x_rol_actualizado BEFORE UPDATE ON modulos_x_rol FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_usuarios_actualizado ON usuarios;
CREATE TRIGGER trg_usuarios_actualizado BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_zonas_actualizado ON zonas;
CREATE TRIGGER trg_zonas_actualizado BEFORE UPDATE ON zonas FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_disponibilidad_docente_actualizado ON disponibilidad_docente;
CREATE TRIGGER trg_disponibilidad_docente_actualizado BEFORE UPDATE ON disponibilidad_docente FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_docentes_modulos_actualizado ON docentes_modulos;
CREATE TRIGGER trg_docentes_modulos_actualizado BEFORE UPDATE ON docentes_modulos FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_password_reset_tokens_actualizado ON password_reset_tokens;
CREATE TRIGGER trg_password_reset_tokens_actualizado BEFORE UPDATE ON password_reset_tokens FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_recursos_fisicos_actualizado ON recursos_fisicos;
CREATE TRIGGER trg_recursos_fisicos_actualizado BEFORE UPDATE ON recursos_fisicos FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_solicitudes_consultas_actualizado ON solicitudes_consultas;
CREATE TRIGGER trg_solicitudes_consultas_actualizado BEFORE UPDATE ON solicitudes_consultas FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_calificaciones_consulta_actualizado ON calificaciones_consulta;
CREATE TRIGGER trg_calificaciones_consulta_actualizado BEFORE UPDATE ON calificaciones_consulta FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_comentarios_actualizado ON comentarios;
CREATE TRIGGER trg_comentarios_actualizado BEFORE UPDATE ON comentarios FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_eventos_solicitud_actualizado ON eventos_solicitud;
CREATE TRIGGER trg_eventos_solicitud_actualizado BEFORE UPDATE ON eventos_solicitud FOR EACH ROW EXECUTE FUNCTION set_actualizado();
DROP TRIGGER IF EXISTS trg_notificaciones_actualizado ON notificaciones;
CREATE TRIGGER trg_notificaciones_actualizado BEFORE UPDATE ON notificaciones FOR EACH ROW EXECUTE FUNCTION set_actualizado();

-- ----------------------------------------------------------------------------
-- Comprobacion (descomentar para ejecutar sobre una base vacia recien creada):
--   SELECT COUNT(*) AS tablas
--   FROM information_schema.tables
--   WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
-- Debe devolver 19.
-- ----------------------------------------------------------------------------
