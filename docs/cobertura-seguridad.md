# Cobertura de seguridad y datos personales (Bloque D.c — solo informe)

Inventario inicial del Bloque D; **actualizado en el Bloque G**. En G se aplicó
la reducción de datos personales descrita en la sección 3 (sin eliminar campos
del contrato, que pasan a valer `null` según el rol). No se han modificado
validaciones de acceso ni añadido endpoints. Las propuestas que siguen abiertas
requieren aprobación explícita.

## 1. Matriz de autorización

`backend/tests/test_autorizacion_roles.py` declara una matriz explícita de los
102 endpoints HTTP de FastAPI y la contrasta con `app.routes`: si aparece un
endpoint nuevo que no esté en la matriz (o sobra una regla), el test falla.
Comprueba solo el nivel de acceso: sin token → 401, rol sin permiso → 403,
rol permitido → cualquier código distinto de 401 y 403. Los casos de recursos
ajenos usan datos reales.

`infraestructura-service/tests/autorizacion.test.js` cubre los 6 endpoints de
Express por rol y las rutas protegidas sin token.

## 2. Endpoints / validaciones no cubiertos o a vigilar

- **Autorización en la capa de servicio.** Todas las rutas de
  `/solicitudes-consultas`, `/comentarios`, `/notificaciones` y
  `/calificaciones` usan solo `get_current_user`; la pertenencia al recurso se
  decide dentro del servicio, no en una dependencia `requiere_modulo`. La
  matriz verifica el nivel de acceso, y los tests con datos reales cubren
  consultas, comentarios y notificaciones ajenas, pero las transiciones de
  estado y la calificación por rol no tienen una matriz own/gestor dedicada.
- **Lectura de catálogos por cualquier usuario autenticado** (diseño
  intencional, ver `decisiones.md`): `GET` de `/modulos`, `/programas`,
  `/periodos-academicos`, `/tipos-documento`, `/sedes`, `/zonas`,
  `/recursos-fisicos`, `/disponibilidad-docente`, `/usuarios/docentes` y
  `/docentes/{id}/calificaciones/promedio`.
- **`GET/PUT /usuarios/{id_usuario}`**: permiten el perfil propio o el módulo
  `USUARIOS`; el 403 se produce en el servicio, no en una dependencia.
- **Código muerto:** `get_current_user_optional`
  (`backend/app/api/deps.py:49`) no se usa en ningún router. **Se documenta y
  se conserva; no se elimina** en este bloque.
- **`get_bearer_token`** (`deps.py:57`) reenvía el token de usuario a Express
  desde `POST/PUT /solicitudes-consultas`. Ya se comprueba que Express exige
  `SERVICIO` en `POST /correos`; conviene vigilar que ese token no se reutilice
  en otras llamadas servicio a servicio.
- **Express:** solo `/health` es público (diseño intencional). `/festivos`,
  `/festivos/validar`, `/servicios-externos`, `/correos` y
  `DELETE /festivos/:id` exigen `autenticar`; `POST /correos` exige además
  `SERVICIO` y `DELETE /festivos/:id` exige `ADMINISTRADOR`. No hay rutas sin
  `autenticar` además de `/health`.

## 3. Revisión de datos personales (propuesta, sin aplicar)

### Qué se expone

| Modelo | Campos personales | Archivo |
|---|---|---|
| `SolicitudConsultaResponse` | `identificacionEstudiante`, `identificacionDocente`, `nombreCompletoEstudiante`, `nombreCompletoDocente`, `estudianteId`, `docenteId` | `backend/app/schemas/solicitud.py:51-71` |
| `UsuarioResponse` | `identificacion`, `correo`, `estado`, `fechaCreacion` y nombres | `backend/app/schemas/usuario.py:46-59` |
| `MeResponse` | `identificacion`, `correo` (solo del propio usuario) | `backend/app/schemas/auth.py:37-38` |
| `ComentarioResponse` | `nombreAutor`, `autorId` (sin identificación ni correo) | `backend/app/schemas/comentario.py:19-27` |
| `NotificacionResponse` | `nombreRemitente`, `nombreDestinatario`, ids (sin identificación ni correo) | `backend/app/schemas/notificacion.py:17-29` |
| `DocenteResumen` / `DocenteResumenModulo` | solo `id`, `nombre`, `apellido` | `usuario.py:62-65`, `docente_modulo.py:20-23` |

El mapper `backend/app/mappers/solicitud_consulta.py:22-26` rellena
`identificacionEstudiante` y `identificacionDocente` directamente desde las
entidades `Usuario`.

### Endpoints que devuelven datos de otros usuarios a cualquier rol autenticado

- `GET /solicitudes-consultas` devuelve `SolicitudConsultaResponse`:
  - `ADMINISTRADOR`: **todas** las consultas (módulo `GESTION_SOLICITUDES`), por
    tanto la identificación de todos los estudiantes y docentes.
  - `DOCENTE`: las consultas que tiene asignadas → identificación de los
    estudiantes.
  - `ESTUDIANTE`: solo las propias → identificación del docente asignado.
- `GET /solicitudes-consultas/{id}`, `PUT`, `PATCH .../recurso-fisico`,
  `PATCH .../estado`, `PATCH .../docente` y `POST /solicitudes-consultas`
  devuelven el mismo modelo. El acceso por id está limitado a participantes o
  gestor (403 en caso contrario), pero la respuesta sigue incluyendo la
  identificación de la contraparte.
- `GET /usuarios` y `POST /usuarios` requieren el módulo `USUARIOS` (solo
  `ADMINISTRADOR`); `GET/PUT /usuarios/{id}` y `PATCH .../activar` devuelven
  `identificacion` y `correo` del propio usuario o, para el administrador, de
  cualquier usuario.
- `GET /usuarios/docentes`, `GET /modulos/{id}/docentes`, comentarios y
  notificaciones **no** exponen identificación ni correo.

### Reducción aplicada en el Bloque G

Los campos **no se eliminan del contrato**: pasan a `str | None` y se rellenan
con `null` cuando el rol que consulta no debe verlos.

- `SolicitudConsultaResponse`: `identificacionEstudiante` e
  `identificacionDocente`. Cada participante ve solo su propia identificación;
  la de la otra parte sale `null`; `ADMINISTRADOR` ve ambas. Se implementa en
  `app/mappers/solicitud_consulta.py`, que ahora recibe `usuario_actual` desde
  los 7 puntos de `app/services/solicitud_consulta.py`.
- `UsuarioResponse`: `identificacion` y `correo`. Solo el propio usuario y
  `ADMINISTRADOR` los ven; los demás roles reciben `null`. Se implementa en
  `app/mappers/usuario.py` y `app/services/usuario.py`, y las 5 rutas de
  `app/api/routes/usuarios.py` pasan el usuario de la dependencia.
- `GET /usuarios/docentes` (`DocenteResumen`) y
  `GET /modulos/{id}/docentes` (`DocenteResumenModulo`) **ya no contenían**
  identificación ni correo: solo `id/nombre/apellido`. No cambiaron; hay tests
  que lo verifican.
- `MeResponse` (`GET /auth/me`) y `LoginResponse` son del propio usuario y no
  se enmascaran.
- Tests por rol en `backend/tests/test_autorizacion_roles.py`; la matriz de
  autorización sigue en verde (no se añadieron endpoints).

### Propuestas que siguen abiertas (NO aplicadas)

1. Revisar si `estado` y `fechaCreacion` de `UsuarioResponse` son necesarios en
   el listado `/usuarios`.
2. Verificar que ningún log ni respuesta de error incluya `correo` o
   `identificacion` ajenos.
3. Decidir si se retiran definitivamente los campos enmascarados del contrato
   (hoy se conservan como `null`).

Cualquiera de estos cambios **requiere aprobación explícita**.

## 4. Limitación del registro público (Bloque G)

`POST /auth/register` permite crear cuentas con rol **`DOCENTE`** además de
`ESTUDIANTE` (diseño intencional, ver `decisiones.md`); solo `ADMINISTRADOR`
se rechaza con 403. La limitación es doble:

- **Cualquiera puede darse de alta como docente** sin intervención de un
  administrador (con `estado` y campos extra ignorados por
  `extra="ignore"`).
- Esas cuentas **aparecen en el listado de docentes** que ve un estudiante
  (`GET /usuarios/docentes` y `GET /modulos/{id}/docentes`), por lo que un
  estudiante puede enumerar sus nombres. Esos modelos solo exponen
  `id/nombre/apellido`: no incluyen identificación ni correo.

**Aclaración importante:** una cuenta `DOCENTE` auto-registrada **no recibe
consultas por sí sola**. Para que se le asignen solicitudes, un administrador
debe asignarla al módulo mediante `POST /docentes-modulos` (módulo
`ASIGNACION_DOCENTES`) y además debe tener disponibilidad horaria registrada
(`disponibilidad-docente`); la creación de una consulta valida ambas cosas
(`_validar_docente_asignado` y `_validar_disponibilidad`). Por tanto el riesgo
no es que un docente auto-registrado atienda consultas, sino el **gobierno de
cuentas** y la **enumeración de nombres** en los listados. Cerrarlo (registro
restringido o confirmación por administrador) es una decisión de producto y
requiere aprobación explícita; aquí solo se documenta.

`get_current_user_optional` (`app/api/deps.py:49`) sigue siendo **código
muerto**: se documenta y **no se elimina** en este bloque.
