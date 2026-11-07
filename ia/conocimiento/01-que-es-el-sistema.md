# Qué es el Sistema de Gestión de Consultas Académicas

El sistema gestiona **consultas académicas** entre estudiantes, docentes y
administradores. Un estudiante registra una solicitud de consulta para una
asignatura con un docente; el docente la atiende y el administrador gestiona
los catálogos y las solicitudes.

## Servicios del monorepo

El repositorio tiene dos servicios **previstos** para desplegarse por separado
(el despliegue está pendiente; **nada está desplegado ni probado en producción**):

| Servicio | Stack | Base de datos |
|---|---|---|
| `backend/` | FastAPI + SQLAlchemy + Uvicorn (Python 3.13) | PostgreSQL (Neon) |
| `infraestructura-service/` | Express + Node 24 | MySQL (Aiven) |

- **PostgreSQL (Neon)** contiene **19 tablas** del dominio de negocio: usuarios,
  roles, módulos (asignaturas), módulos del sistema, programas académicos,
  periodos académicos, tipos de documento, sedes, zonas, recursos físicos,
  docentes-módulos, disponibilidad docente, solicitudes de consulta,
  calificaciones, comentarios, eventos, notificaciones, tokens de recuperación
  y la matriz módulos por rol.
- **MySQL (Aiven)** contiene **4 tablas** de servicios externos:
  `servicios_externos`, `consultas_servicio_externo`, `festivos` y
  `correos_enviados`.
- **FastAPI** expone los endpoints del dominio, incluidos `/sedes`, `/zonas` y
  `/recursos-fisicos`. Valida las fechas festivas al crear y reprogramar
  solicitudes llamando al microservicio de servicios externos.
- **Express** expone `/festivos`, `/correos` y `/servicios-externos`.
  `POST /correos` solo acepta tokens con rol `SERVICIO`. Usa **Nager.Date**
  para los festivos y **Brevo** para el correo transaccional.

## Características transversales

- Autenticación **stateless** con **JWT HS256**: cada petición lleva su token;
  no hay sesiones en servidor. El token incluye `sub`, `uid`, `rol`, `modulos`,
  `iat` y `exp`, y expira a los **30 minutos** (`JWT_EXPIRATION_MINUTES`).
- Autorización combinada por **rol** y por **módulos** asignados a ese rol.
- **Borrado lógico**: las entidades usan una columna booleana `estado` en lugar
  de `DELETE` físico, para conservar trazabilidad.
- Errores con un sobre JSON común: `timestamp`, `status`, `error`, `message`,
  `errors`. Códigos usados: 200/201/204, 400, 401, 403, 404, 413, 429, 500,
  502 y 503.
- Límite de cuerpo de **1 MiB** (respuesta 413), CORS por lista blanca sin `*`
  y cabeceras de seguridad en todas las respuestas.
- La documentación interactiva la genera FastAPI en `/docs` y `/openapi.json`.

## Catálogos

El sistema trabaja con nombres legibles (no pide IDs al usuario final en los
selectores): programas académicos, asignaturas (tabla `modulos`), periodos
académicos, tipos de documento, sedes, zonas y recursos físicos. La jerarquía
física es **Sede → Zona/Bloque → Recurso físico**.

## Alcance de esta documentación

Describe únicamente el código del repositorio y la documentación verificada
contra él. No incluye datos personales, contraseñas, correos reales, tokens ni
secretos. No hay usuarios de ejemplo con datos reales en estos documentos.
