# Cobertura de seguridad y datos personales (Bloque D.c — solo informe)

Inventario de solo lectura. **No se ha modificado ningún endpoint, esquema de
respuesta ni validación.** Las propuestas de reducción de datos requieren
aprobación explícita antes de aplicarse.

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

### Propuesta de reducción (NO aplicada)

1. Confirmar con el frontend si `identificacionEstudiante` e
   `identificacionDocente` se usan. Si no, retirarlos de
   `SolicitudConsultaResponse` y del mapper, conservando los ids y los nombres.
2. Si sí se usan, devolverlos únicamente cuando el solicitante tenga el módulo
   `GESTION_SOLICITUDES` (o un endpoint de detalle separado), y omitirlos en el
   listado general.
3. Revisar si `estado` y `fechaCreacion` de `UsuarioResponse` son necesarios en
   el listado `/usuarios`.
4. Verificar que ningún log ni respuesta de error incluya `correo` o
   `identificacion` ajenos.

Cualquiera de estos cambios modifica contratos de respuesta y **requiere
aprobación explícita**; este bloque solo documenta el hallazgo.
