# Roles y módulos

## Los tres roles

Los roles activos son exactamente tres (tabla `roles`, valores del enum `Rol`):

- **ESTUDIANTE**: crea y da seguimiento a sus consultas, comenta y califica.
- **DOCENTE**: atiende las consultas asignadas, gestiona su disponibilidad,
  puede asignar recursos físicos y cambiar el estado de sus consultas.
- **ADMINISTRADOR**: administra usuarios, roles/módulos, catálogos y solicitudes.

El registro público `POST /auth/register` permite dar de alta **ESTUDIANTE** y
**DOCENTE**; crear **ADMINISTRADOR** se rechaza con **403**. El campo `estado`
y cualquier campo extra se ignoran y el usuario queda activo. Una cuenta
DOCENTE auto-registrada **no recibe consultas por sí sola**: necesita que un
administrador la asigne a un módulo (docentes-módulos) y que tenga
disponibilidad.

## `modulos` frente a `modulos_sistema`

Hay dos tablas distintas que comparten la palabra "módulo":

- `modulos`: las **asignaturas** académicas (Cálculo, Bases de Datos, ...).
  Aqui apunta `solicitudes_consultas.modulo_id` y `docentes_modulos.modulo_id`.
- `modulos_sistema`: los **módulos funcionales** de la interfaz y de los
  permisos (DASHBOARD, PERFIL, ...). Aqui apunta `modulos_x_rol.modulo_id`.

## Los 15 módulos del sistema

`DASHBOARD`, `PERFIL`, `NOTIFICACIONES`, `MIS_SOLICITUDES`,
`ATENCION_SOLICITUDES`, `GESTION_SOLICITUDES`, `USUARIOS`, `ROLES_PERMISOS`,
`PROGRAMAS_ASIGNATURAS`, `INFRAESTRUCTURA`, `ASIGNACION_DOCENTES`,
`PERIODOS_ACADEMICOS`, `TIPOS_DOCUMENTO`, `DISPONIBILIDAD_DOCENTE`,
`CALIFICACIONES`.

## Matriz rol → módulo (semilla `MATRIZ_MODULOS_X_ROL`)

- Los **tres roles**: `DASHBOARD`, `PERFIL`, `NOTIFICACIONES`, `CALIFICACIONES`.
- **ESTUDIANTE** añade: `MIS_SOLICITUDES`.
- **DOCENTE** añade: `ATENCION_SOLICITUDES`, `DISPONIBILIDAD_DOCENTE`.
- **ADMINISTRADOR** añade: `GESTION_SOLICITUDES`, `USUARIOS`,
  `ROLES_PERMISOS`, `PROGRAMAS_ASIGNATURAS`, `INFRAESTRUCTURA`,
  `ASIGNACION_DOCENTES`, `PERIODOS_ACADEMICOS`, `TIPOS_DOCUMENTO`,
  `DISPONIBILIDAD_DOCENTE`.

`GESTION_SOLICITUDES` es el permiso que, dentro de los servicios, habilita
listar todas las consultas, eliminarlas, reasignar docente, asignar recurso,
cambiar estado, ver calificaciones ajenas y borrar comentarios. En la semilla
solo lo tiene `ADMINISTRADOR`.

## Cómo se aplica la autorización

- `requiere_modulo(nombre)` comprueba en **base de datos** que exista un
  permiso activo en `modulos_x_rol` y responde **403** si el rol no lo tiene.
- El claim `modulos` del JWT es **informativo**: se devuelve en
  `POST /auth/login`, `GET /auth/me` y `GET /auth/me/modulos`, pero la
  autorización real se consulta en cada petición, no se confía en el claim.
- Los **GET de catálogos** (módulos/asignaturas, programas, periodos, tipos de
  documento, sedes, zonas, recursos físicos, disponibilidad y resumen de
  docentes) usan solo `get_current_user`: **cualquier usuario autenticado puede
  leerlos**. Las escrituras y activaciones exigen el módulo correspondiente.
  El parámetro `incluirInactivos=true` en sedes, zonas y recursos sí exige
  `INFRAESTRUCTURA`.
- El listado `GET /usuarios` exige el módulo `USUARIOS`; `GET /usuarios/{id}`
  admite al propio usuario o a quien tenga ese módulo.
