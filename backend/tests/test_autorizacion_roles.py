"""Bloque D (a): matriz de autorización por rol y recursos de otros usuarios.

La matriz se declara explícitamente y se contrasta con ``app.routes``: si
aparece un endpoint nuevo que no esté en la matriz (o sobra una entrada), el
test falla. Los usuarios y tokens se crean una sola vez por módulo para no
multiplicar el costo de bcrypt.
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal, engine
from app.main import app
from app.models import Base
from app.models.usuario import Usuario
from tests.helpers import auth, crear_admin, crear_modulo, crear_solicitud, crear_usuario

RUTAS_DOC = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
SIN_TOKEN = "SIN_TOKEN"
ROLES = ("ESTUDIANTE", "DOCENTE", "ADMINISTRADOR")

TODOS = frozenset(ROLES)
SOLO_ADMIN = frozenset({"ADMINISTRADOR"})
ADMIN_DOCENTE = frozenset({"ADMINISTRADOR", "DOCENTE"})

PUBLICO = "PUBLICO"
AUTH = "AUTH"
MODULO = "MODULO"

MATRIZ: dict[tuple[str, str], tuple[str, frozenset | None]] = {}


def _registrar(nivel, permitidos, entradas):
    for metodo, path in entradas:
        MATRIZ[(metodo, path)] = (nivel, permitidos)


# --- Endpoints públicos (sin sesión) ---------------------------------------
_registrar(
    PUBLICO,
    None,
    [
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("POST", "/auth/forgot-password"),
        ("POST", "/auth/reset-password"),
    ],
)

# --- Solo autenticación: cualquier rol autenticado --------------------------
_registrar(
    AUTH,
    TODOS,
    [
        ("GET", "/auth/me"),
        ("POST", "/auth/cambiar-password"),
        ("GET", "/docentes/{id_docente}/calificaciones/promedio"),
        ("POST", "/comentarios"),
        ("GET", "/comentarios/solicitud/{solicitud_consulta_id}"),
        ("GET", "/comentarios/{id_comentario}"),
        ("PUT", "/comentarios/{id_comentario}"),
        ("DELETE", "/comentarios/{id_comentario}"),
        ("GET", "/disponibilidad-docente"),
        ("GET", "/modulos"),
        ("GET", "/modulos/{id_modulo}"),
        ("GET", "/modulos/{id_modulo}/docentes"),
        ("GET", "/notificaciones"),
        ("GET", "/notificaciones/no-leidas/count"),
        ("PATCH", "/notificaciones/{id_notificacion}/leer"),
        ("DELETE", "/notificaciones/{id_notificacion}"),
        ("GET", "/periodos-academicos"),
        ("GET", "/periodos-academicos/{id_periodo}"),
        ("GET", "/programas"),
        ("GET", "/programas/{id_programa}"),
        ("GET", "/recursos-fisicos"),
        ("GET", "/recursos-fisicos/{id_recurso}"),
        ("GET", "/sedes"),
        ("GET", "/sedes/{id_sede}"),
        ("GET", "/sedes/{id_sede}/zonas"),
        ("GET", "/sedes/{id_sede}/recursos-fisicos"),
        ("GET", "/solicitudes-consultas"),
        ("POST", "/solicitudes-consultas"),
        ("GET", "/solicitudes-consultas/{id_solicitud}"),
        ("PUT", "/solicitudes-consultas/{id_solicitud}"),
        ("PATCH", "/solicitudes-consultas/{id_solicitud}/recurso-fisico"),
        ("PATCH", "/solicitudes-consultas/{id_solicitud}/estado"),
        ("PATCH", "/solicitudes-consultas/{id_solicitud}/docente"),
        ("DELETE", "/solicitudes-consultas/{id_solicitud}"),
        ("POST", "/solicitudes-consultas/{id_solicitud}/calificacion"),
        ("GET", "/solicitudes-consultas/{id_solicitud}/calificacion"),
        ("GET", "/tipos-documento"),
        ("GET", "/tipos-documento/{id_tipo}"),
        ("GET", "/usuarios/docentes"),
        ("GET", "/zonas"),
        ("GET", "/zonas/{id_zona}"),
        ("GET", "/zonas/{id_zona}/recursos-fisicos"),
    ],
)

# --- Módulos exclusivos de ADMINISTRADOR -----------------------------------
_registrar(
    MODULO,
    SOLO_ADMIN,
    [
        # USUARIOS (incluye "propio o módulo" en las rutas por id)
        ("GET", "/usuarios"),
        ("POST", "/usuarios"),
        ("GET", "/usuarios/{id_usuario}"),
        ("PUT", "/usuarios/{id_usuario}"),
        ("PATCH", "/usuarios/{id_usuario}/activar"),
        ("DELETE", "/usuarios/{id_usuario}"),
        # ROLES_PERMISOS
        ("GET", "/roles"),
        ("POST", "/roles"),
        ("GET", "/roles/{id_rol}"),
        ("GET", "/roles/{id_rol}/modulos"),
        ("PUT", "/roles/{id_rol}/modulos"),
        ("PUT", "/roles/{id_rol}"),
        ("PATCH", "/roles/{id_rol}/activar"),
        ("DELETE", "/roles/{id_rol}"),
        ("GET", "/modulos-sistema"),
        ("POST", "/modulos-sistema"),
        ("GET", "/modulos-sistema/{id_modulo}"),
        ("PUT", "/modulos-sistema/{id_modulo}"),
        ("PATCH", "/modulos-sistema/{id_modulo}/activar"),
        ("DELETE", "/modulos-sistema/{id_modulo}"),
        # PROGRAMAS_ASIGNATURAS
        ("POST", "/programas"),
        ("PUT", "/programas/{id_programa}"),
        ("DELETE", "/programas/{id_programa}"),
        ("POST", "/modulos"),
        ("PUT", "/modulos/{id_modulo}"),
        ("DELETE", "/modulos/{id_modulo}"),
        # INFRAESTRUCTURA
        ("POST", "/sedes"),
        ("PUT", "/sedes/{id_sede}"),
        ("DELETE", "/sedes/{id_sede}"),
        ("PATCH", "/sedes/{id_sede}/activar"),
        ("POST", "/zonas"),
        ("PUT", "/zonas/{id_zona}"),
        ("DELETE", "/zonas/{id_zona}"),
        ("PATCH", "/zonas/{id_zona}/activar"),
        ("POST", "/recursos-fisicos"),
        ("PUT", "/recursos-fisicos/{id_recurso}"),
        ("DELETE", "/recursos-fisicos/{id_recurso}"),
        ("PATCH", "/recursos-fisicos/{id_recurso}/activar"),
        # ASIGNACION_DOCENTES
        ("GET", "/docentes-modulos"),
        ("POST", "/docentes-modulos"),
        ("GET", "/docentes-modulos/{id_asignacion}"),
        ("PATCH", "/docentes-modulos/{id_asignacion}/activar"),
        ("DELETE", "/docentes-modulos/{id_asignacion}"),
        # PERIODOS_ACADEMICOS
        ("POST", "/periodos-academicos"),
        ("PUT", "/periodos-academicos/{id_periodo}"),
        ("PATCH", "/periodos-academicos/{id_periodo}/activar"),
        ("DELETE", "/periodos-academicos/{id_periodo}"),
        # TIPOS_DOCUMENTO
        ("POST", "/tipos-documento"),
        ("PUT", "/tipos-documento/{id_tipo}"),
        ("PATCH", "/tipos-documento/{id_tipo}/activar"),
        ("DELETE", "/tipos-documento/{id_tipo}"),
    ],
)

# --- DISPONIBILIDAD_DOCENTE: ADMINISTRADOR y DOCENTE -----------------------
_registrar(
    MODULO,
    ADMIN_DOCENTE,
    [
        ("POST", "/disponibilidad-docente"),
        ("GET", "/disponibilidad-docente/{id_disponibilidad}"),
        ("PUT", "/disponibilidad-docente/{id_disponibilidad}"),
        ("PATCH", "/disponibilidad-docente/{id_disponibilidad}/activar"),
        ("DELETE", "/disponibilidad-docente/{id_disponibilidad}"),
    ],
)


def _rutas_reales():
    rutas = set()
    for ruta in app.routes:
        metodos = getattr(ruta, "methods", None) or set()
        path = getattr(ruta, "path", None)
        if not path or path in RUTAS_DOC:
            continue
        for metodo in metodos:
            if metodo in {"HEAD", "OPTIONS"}:
                continue
            rutas.add((metodo, path))
    return rutas


def test_matriz_cubre_todos_los_endpoints():
    """Falla si aparece un endpoint nuevo o si la matriz queda desactualizada."""
    reales = _rutas_reales()
    faltantes = sorted(reales - set(MATRIZ))
    sobrantes = sorted(set(MATRIZ) - reales)
    assert not faltantes, f"Endpoints sin regla en la matriz: {faltantes}"
    assert not sobrantes, f"Reglas que ya no corresponden a ninguna ruta: {sobrantes}"


def _url(path):
    return re.sub(r"\{[^}]+\}", "999999", path)


def _cuerpo(metodo, path):
    if metodo not in {"POST", "PUT", "PATCH"}:
        return None
    # El PUT de usuario valida el cuerpo antes de comprobar el permiso por id;
    # se envía un cuerpo válido para que la regla de acceso sea la que decida.
    if path == "/usuarios/{id_usuario}":
        return {"nombre": "Nombre", "apellido": "Apellido", "correo": "permiso@test.com"}
    return {}


def _peticion(client, metodo, url, headers, cuerpo):
    kwargs = {"headers": headers}
    if cuerpo is not None:
        kwargs["json"] = cuerpo
    return client.request(metodo, url, **kwargs)


# --- Fixtures de alcance módulo: un solo costo de bcrypt -------------------
@pytest.fixture(scope="module", autouse=True)
def _limpiar_bd(_esquema):
    """Sobrescribe el fixture global: limpia una vez por módulo.

    Los usuarios/tokens son de alcance módulo, así que no se puede vaciar la
    base de datos en cada test.
    """
    with engine.begin() as conn:
        for tabla in reversed(Base.metadata.sorted_tables):
            conn.execute(tabla.delete())
    yield


@pytest.fixture(scope="module")
def client(_limpiar_bd):
    with TestClient(app) as c:
        yield c


def _plano(info, rol):
    return {
        "rol": rol,
        "token": info["token"],
        "headers": auth(info["token"]),
        "id": info["id_usuario"],
    }


@pytest.fixture(scope="module")
def identidades(_limpiar_bd, client):
    return {
        "ADMINISTRADOR": _plano(crear_admin(client), "ADMINISTRADOR"),
        "ESTUDIANTE": _plano(
            crear_usuario(
                client, rol="ESTUDIANTE", correo="bloqueD.est@test.com",
                identificacion="9000000101",
            ),
            "ESTUDIANTE",
        ),
        "ESTUDIANTE_OTRO": _plano(
            crear_usuario(
                client, rol="ESTUDIANTE", correo="bloqueD.otro@test.com",
                identificacion="9000000102",
            ),
            "ESTUDIANTE",
        ),
        "DOCENTE": _plano(
            crear_usuario(
                client, rol="DOCENTE", correo="bloqueD.doc@test.com",
                identificacion="9000000103",
            ),
            "DOCENTE",
        ),
        "DOCENTE_OTRO": _plano(
            crear_usuario(
                client, rol="DOCENTE", correo="bloqueD.doc2@test.com",
                identificacion="9000000104",
            ),
            "DOCENTE",
        ),
    }


@pytest.fixture(scope="module")
def cabeceras(identidades):
    return {
        SIN_TOKEN: {},
        "ESTUDIANTE": identidades["ESTUDIANTE"]["headers"],
        "DOCENTE": identidades["DOCENTE"]["headers"],
        "ADMINISTRADOR": identidades["ADMINISTRADOR"]["headers"],
    }


@pytest.mark.parametrize("metodo,path", sorted(MATRIZ))
def test_nivel_de_acceso(metodo, path, client, cabeceras):
    """Solo nivel de acceso: sin token 401; sin permiso 403; permitido != 401/403."""
    nivel, permitidos = MATRIZ[(metodo, path)]
    url = _url(path)
    cuerpo = _cuerpo(metodo, path)

    for identidad, headers in cabeceras.items():
        respuesta = _peticion(client, metodo, url, headers, cuerpo)
        codigo = respuesta.status_code

        if nivel == PUBLICO:
            esperado, correcto = "distinto de 401/403", codigo not in (401, 403)
        elif identidad == SIN_TOKEN:
            esperado, correcto = "401", codigo == 401
        elif nivel == AUTH or identidad in permitidos:
            esperado, correcto = "distinto de 401/403", codigo not in (401, 403)
        else:
            esperado, correcto = "403", codigo == 403

        assert correcto, (
            f"{metodo} {path} con {identidad}: se esperaba {esperado}, "
            f"se obtuvo {codigo} ({respuesta.text[:200]})"
        )


# --- Registro público: diseño intencional ----------------------------------
def test_registro_publico_acepta_estudiante_y_docente_e_ignora_extras(client):
    base = {
        "nombre": "Publico",
        "apellido": "Registro",
        "password": "ClaveSegura#2026",
        "estado": False,
        "rolForzado": "ADMINISTRADOR",
        "campoDesconocido": "ignorado",
    }
    estudiante = {
        **base,
        "identificacion": "9000000201",
        "correo": "bloqueD.publico.est@test.com",
        "rol": "ESTUDIANTE",
    }
    docente = {
        **base,
        "identificacion": "9000000202",
        "correo": "bloqueD.publico.doc@test.com",
        "rol": "DOCENTE",
    }

    assert client.post("/auth/register", json=estudiante).status_code == 201
    assert client.post("/auth/register", json=docente).status_code == 201

    with SessionLocal() as db:
        registrados = {
            u.correo: u
            for u in db.query(Usuario)
            .filter(Usuario.correo.in_([estudiante["correo"], docente["correo"]]))
            .all()
        }
        # ``rol`` es una propiedad que carga ``rol_rel``; debe leerse con la
        # sesión abierta para evitar DetachedInstanceError.
        assert registrados[estudiante["correo"]].estado is True
        assert registrados[estudiante["correo"]].rol.value == "ESTUDIANTE"
        assert registrados[docente["correo"]].estado is True
        assert registrados[docente["correo"]].rol.value == "DOCENTE"


def test_registro_publico_rechaza_administrador(client):
    resp = client.post(
        "/auth/register",
        json={
            "identificacion": "9000000203",
            "nombre": "Publico",
            "apellido": "Admin",
            "correo": "bloqueD.publico.admin@test.com",
            "password": "ClaveSegura#2026",
            "rol": "ADMINISTRADOR",
        },
    )
    assert resp.status_code == 403


# --- Recursos ajenos con datos reales --------------------------------------
def test_consultas_ajenas_no_se_listan_ni_se_leen(client, identidades):
    admin = identidades["ADMINISTRADOR"]
    docente = identidades["DOCENTE"]
    estudiante = identidades["ESTUDIANTE"]
    otro = identidades["ESTUDIANTE_OTRO"]
    modulo = crear_modulo(client, admin["token"], nombre="Modulo Bloque D consultas")

    propia = crear_solicitud(client, estudiante["token"], docente["id"], modulo["id"])
    ajena = crear_solicitud(client, otro["token"], docente["id"], modulo["id"])

    listado = client.get("/solicitudes-consultas", headers=estudiante["headers"])
    assert listado.status_code == 200
    assert [s["id"] for s in listado.json()] == [propia["id"]]

    assert client.get(
        f"/solicitudes-consultas/{ajena['id']}", headers=estudiante["headers"]
    ).status_code == 403


def test_comentario_ajeno_no_se_puede_modificar(client, identidades):
    admin = identidades["ADMINISTRADOR"]
    docente = identidades["DOCENTE"]
    estudiante = identidades["ESTUDIANTE"]
    otro = identidades["ESTUDIANTE_OTRO"]
    modulo = crear_modulo(client, admin["token"], nombre="Modulo Bloque D comentarios")
    sol = crear_solicitud(client, estudiante["token"], docente["id"], modulo["id"])

    # Solo se puede comentar una consulta en curso.
    cambio = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=docente["headers"],
    )
    assert cambio.status_code == 200, cambio.text

    creado = client.post(
        "/comentarios",
        json={"contenido": "Comentario propio", "solicitudConsultaId": sol["id"]},
        headers=estudiante["headers"],
    )
    assert creado.status_code == 201, creado.text
    id_comentario = creado.json()["id"]

    # Comportamiento actual del servicio: editar un comentario ajeno se
    # rechaza con 400 (BadRequestException), no con 403. Lo importante es que
    # no se modifica el contenido del otro usuario.
    ajeno = client.put(
        f"/comentarios/{id_comentario}",
        json={"contenido": "Modificado por otro"},
        headers=otro["headers"],
    )
    assert ajeno.status_code == 400
    assert client.get(
        f"/comentarios/{id_comentario}", headers=estudiante["headers"]
    ).json()["contenido"] == "Comentario propio"

    # Borrar un comentario ajeno sí responde 403.
    assert client.delete(
        f"/comentarios/{id_comentario}", headers=otro["headers"]
    ).status_code == 403


def test_notificacion_ajena_no_se_puede_marcar_como_leida(client, identidades):
    admin = identidades["ADMINISTRADOR"]
    docente = identidades["DOCENTE"]
    estudiante = identidades["ESTUDIANTE"]
    otro = identidades["ESTUDIANTE_OTRO"]
    modulo = crear_modulo(client, admin["token"], nombre="Modulo Bloque D notificaciones")
    sol = crear_solicitud(client, estudiante["token"], docente["id"], modulo["id"])

    cambio = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=docente["headers"],
    )
    assert cambio.status_code == 200, cambio.text

    propias = client.get("/notificaciones", headers=estudiante["headers"]).json()
    assert propias, "Debió generarse la notificación del cambio de estado"
    assert client.get("/notificaciones", headers=otro["headers"]).json() == []

    respuesta = client.patch(
        f"/notificaciones/{propias[0]['id']}/leer", headers=otro["headers"]
    )
    assert respuesta.status_code not in (200, 204)
