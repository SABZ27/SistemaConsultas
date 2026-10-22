from datetime import date, timedelta

import httpx
import jwt as pyjwt
import pytest

from app.clients import servicios_externos
from app.clients.servicios_externos import ServiciosExternosClient
from app.core.config import settings
from app.exceptions.errors import ServiceUnavailableException
from tests.helpers import (
    asignar_docente_modulo,
    auth,
    asegurar_periodo_cubre,
    crear_admin,
    crear_docente,
    crear_estudiante,
    crear_modulo,
    escenario_completo,
)

# La fixture global simula el microservicio; estas son las implementaciones
# reales y se usan en las pruebas unitarias del cliente.
VALIDAR_FESTIVO_ORIGINAL = ServiciosExternosClient.validar_festivo
ENVIAR_CORREO_ORIGINAL = ServiciosExternosClient.enviar_correo

FESTIVO = {
    "id": 7,
    "fecha": "2026-07-20",
    "pais": "CO",
    "esFestivo": True,
    "nombre": "Día de la Independencia",
}


class _Respuesta:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class _ClienteHttpFalso:
    """Mock acotado de httpx.Client para las pruebas del cliente."""

    def __init__(self, respuestas):
        self._respuestas = respuestas
        self.llamadas = []
        self.timeouts = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def get(self, url, params=None, headers=None):
        self.llamadas.append(("GET", url, params, headers))
        resultado = self._respuestas.pop(0)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    def post(self, url, json=None, headers=None):
        self.llamadas.append(("POST", url, json, headers))
        resultado = self._respuestas.pop(0)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado


def _parchear(monkeypatch, respuestas):
    """Instala el mock de httpx y devuelve la lista de clientes creados."""
    creados = []

    def fabrica(*_args, **kwargs):
        cliente = _ClienteHttpFalso(respuestas)
        cliente.timeouts.append(kwargs.get("timeout"))
        creados.append(cliente)
        return cliente

    monkeypatch.setattr(servicios_externos.httpx, "Client", fabrica)
    return creados


@pytest.fixture()
def cliente_real(monkeypatch):
    """Restaura los métodos reales del cliente (la fixture global los simula)."""
    monkeypatch.setattr(
        ServiciosExternosClient, "validar_festivo", VALIDAR_FESTIVO_ORIGINAL
    )
    monkeypatch.setattr(ServiciosExternosClient, "enviar_correo", ENVIAR_CORREO_ORIGINAL)


# ---------------------------------------------------------------------------
# Cliente de servicios externos
# ---------------------------------------------------------------------------


def test_validar_festivo_ok_reenvia_el_bearer(cliente_real, monkeypatch):
    creados = _parchear(monkeypatch, [_Respuesta(200, FESTIVO)])

    datos = ServiciosExternosClient().validar_festivo(date(2026, 7, 20), "token-abc")

    assert datos == FESTIVO
    metodo, url, params, headers = creados[0].llamadas[0]
    assert metodo == "GET"
    assert url.endswith("/festivos/validar")
    assert params == {"fecha": "2026-07-20", "pais": "CO"}
    assert headers == {"Authorization": "Bearer token-abc"}


def test_validar_festivo_usa_timeout_corto_de_15_segundos(cliente_real, monkeypatch):
    creados = _parchear(monkeypatch, [_Respuesta(200, FESTIVO)])

    ServiciosExternosClient().validar_festivo(date(2026, 7, 20), "token")

    assert creados[0].timeouts == [15.0]


def test_validar_festivo_reintenta_una_vez_si_responde_5xx(cliente_real, monkeypatch):
    creados = _parchear(monkeypatch, [_Respuesta(500), _Respuesta(500)])

    with pytest.raises(ServiceUnavailableException):
        ServiciosExternosClient().validar_festivo(date(2026, 7, 20), "token")

    assert len(creados) == 2


def test_validar_festivo_reintenta_una_vez_si_falla_la_red(cliente_real, monkeypatch):
    creados = _parchear(monkeypatch, [httpx.ConnectError("caído")] * 2)

    with pytest.raises(ServiceUnavailableException) as error:
        ServiciosExternosClient().validar_festivo(date(2026, 7, 20), "token")

    assert len(creados) == 2
    assert error.value.causa == "ConnectError"


def test_validar_festivo_conserva_el_codigo_http_401(cliente_real, monkeypatch):
    _parchear(monkeypatch, [_Respuesta(401, {"message": "Token inválido o expirado."})])

    with pytest.raises(ServiceUnavailableException) as error:
        ServiciosExternosClient().validar_festivo(date(2026, 7, 20), "token")

    assert error.value.codigo_http == 401


def test_enviar_correo_ok_no_reintenta(cliente_real, monkeypatch):
    creados = _parchear(
        monkeypatch, [_Respuesta(201, {"id": 3, "messageId": "abc", "estadoEnvio": "ENVIADO"})]
    )

    datos = ServiciosExternosClient().enviar_correo(
        para="docente@test.com",
        asunto="Nueva solicitud de consulta",
        contenido="Contenido",
        token="token-servicio",
        para_nombre="Docente Prueba",
    )

    assert datos["estadoEnvio"] == "ENVIADO"
    metodo, url, cuerpo, headers = creados[0].llamadas[0]
    assert metodo == "POST"
    assert url.endswith("/correos")
    assert cuerpo == {
        "para": "docente@test.com",
        "asunto": "Nueva solicitud de consulta",
        "contenido": "Contenido",
        "paraNombre": "Docente Prueba",
    }
    assert headers == {"Authorization": "Bearer token-servicio"}
    assert len(creados) == 1


def test_enviar_correo_usa_el_timeout_general(cliente_real, monkeypatch):
    creados = _parchear(monkeypatch, [_Respuesta(201, {"id": 1})])

    ServiciosExternosClient().enviar_correo(
        para="docente@test.com", asunto="a", contenido="c", token="token"
    )

    assert creados[0].timeouts == [settings.infra_timeout]


def test_enviar_correo_fallido_no_reintenta(cliente_real, monkeypatch):
    creados = _parchear(monkeypatch, [_Respuesta(502, {"message": "No se pudo enviar"})])

    with pytest.raises(ServiceUnavailableException) as error:
        ServiciosExternosClient().enviar_correo(
            para="docente@test.com", asunto="a", contenido="c", token="token"
        )

    assert len(creados) == 1
    assert error.value.codigo_http == 502


# ---------------------------------------------------------------------------
# Integración: creación y reprogramación de solicitudes
# ---------------------------------------------------------------------------


def _payload(fecha, docente_id, modulo_id):
    return {
        "prioridad": "MEDIA",
        "asunto": "Asunto",
        "descripcion": "Descripción",
        "fechaConsulta": fecha.isoformat(),
        "horaConsulta": "06:30",
        "docenteId": docente_id,
        "moduloId": modulo_id,
    }


def _festivo(monkeypatch):
    def _validar(self, fecha, token):
        return {**FESTIVO, "fecha": fecha.isoformat()}

    monkeypatch.setattr(ServiciosExternosClient, "validar_festivo", _validar)


def _express_caido(monkeypatch):
    def _validar(self, fecha, token):
        raise ServiceUnavailableException(causa="ConnectError")

    monkeypatch.setattr(ServiciosExternosClient, "validar_festivo", _validar)


def test_crear_solicitud_en_fecha_festiva_devuelve_400(client, monkeypatch):
    admin, docente, estudiante, modulo = escenario_completo(client)
    _festivo(monkeypatch)
    fecha = date.today() + timedelta(days=1)
    asegurar_periodo_cubre(client, admin["token"], fecha)

    resp = client.post(
        "/solicitudes-consultas",
        json=_payload(fecha, docente["id_usuario"], modulo["id"]),
        headers=auth(estudiante["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert (
        resp.json()["message"]
        == "La fecha seleccionada es festivo: Día de la Independencia"
    )


def test_crear_solicitud_en_fecha_no_festiva_crea_la_solicitud(client):
    admin, docente, estudiante, modulo = escenario_completo(client)
    fecha = date.today() + timedelta(days=1)
    asegurar_periodo_cubre(client, admin["token"], fecha)

    resp = client.post(
        "/solicitudes-consultas",
        json=_payload(fecha, docente["id_usuario"], modulo["id"]),
        headers=auth(estudiante["token"]),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["fechaConsulta"] == fecha.isoformat()


def test_crear_solicitud_con_el_microservicio_caido_igual_crea(client, monkeypatch, caplog):
    admin, docente, estudiante, modulo = escenario_completo(client)
    _express_caido(monkeypatch)
    fecha = date.today() + timedelta(days=1)
    asegurar_periodo_cubre(client, admin["token"], fecha)

    with caplog.at_level("WARNING"):
        resp = client.post(
            "/solicitudes-consultas",
            json=_payload(fecha, docente["id_usuario"], modulo["id"]),
            headers=auth(estudiante["token"]),
        )

    assert resp.status_code == 201, resp.text
    assert "No se pudo validar el carácter festivo" in caplog.text
    assert fecha.isoformat() in caplog.text
    # El aviso no lleva datos personales.
    assert estudiante["correo"] not in caplog.text
    assert docente["correo"] not in caplog.text


def test_reprogramar_a_una_fecha_festiva_devuelve_400(client, monkeypatch):
    admin, docente, estudiante, modulo = escenario_completo(client)
    fecha = date.today() + timedelta(days=1)
    asegurar_periodo_cubre(client, admin["token"], fecha)
    creada = client.post(
        "/solicitudes-consultas",
        json=_payload(fecha, docente["id_usuario"], modulo["id"]),
        headers=auth(estudiante["token"]),
    )
    assert creada.status_code == 201, creada.text

    _festivo(monkeypatch)
    nueva_fecha = fecha + timedelta(days=1)
    asegurar_periodo_cubre(client, admin["token"], nueva_fecha)

    resp = client.put(
        f"/solicitudes-consultas/{creada.json()['id']}",
        json={
            "prioridad": "MEDIA",
            "asunto": "Asunto",
            "descripcion": "Descripción",
            "fechaConsulta": nueva_fecha.isoformat(),
            "horaConsulta": "06:30",
            "moduloId": modulo["id"],
            "motivo": "Cambio de agenda",
        },
        headers=auth(estudiante["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert (
        resp.json()["message"]
        == "La fecha seleccionada es festivo: Día de la Independencia"
    )


def test_el_festivo_se_valida_antes_que_la_disponibilidad_del_docente(client, monkeypatch):
    admin = crear_admin(client)
    docente = crear_docente(client, admin["token"])
    estudiante = crear_estudiante(client, admin["token"])
    modulo = crear_modulo(client, admin["token"])
    asignar_docente_modulo(client, admin["token"], docente["id_usuario"], modulo["id"])
    # El docente NO tiene disponibilidad registrada.
    fecha = date.today() + timedelta(days=1)
    asegurar_periodo_cubre(client, admin["token"], fecha)
    _festivo(monkeypatch)

    resp = client.post(
        "/solicitudes-consultas",
        json=_payload(fecha, docente["id_usuario"], modulo["id"]),
        headers=auth(estudiante["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert (
        resp.json()["message"]
        == "La fecha seleccionada es festivo: Día de la Independencia"
    )


# ---------------------------------------------------------------------------
# Integración: envío de correos
# ---------------------------------------------------------------------------


def test_crear_solicitud_envia_el_correo_al_docente(client, servicios_externos):
    _, docente, estudiante, modulo = escenario_completo(client)
    fecha = date.today() + timedelta(days=1)

    resp = client.post(
        "/solicitudes-consultas",
        json=_payload(fecha, docente["id_usuario"], modulo["id"]),
        headers=auth(estudiante["token"]),
    )

    assert resp.status_code == 201, resp.text
    assert len(servicios_externos["correos"]) == 1
    correo = servicios_externos["correos"][0]
    assert correo["para"] == docente["correo"]
    assert correo["asunto"] == "Nueva solicitud de consulta"
    assert correo["paraNombre"] == docente["nombre"]
    # El correo va con el token interno (servicio), no con el del usuario.
    payload = pyjwt.decode(correo["token"], settings.jwt_secret, algorithms=["HS256"])
    assert payload["rol"] == "SERVICIO"
    assert correo["token"] != estudiante["token"]


def test_un_correo_fallido_no_rompe_el_flujo(client, monkeypatch, servicios_externos):
    _, docente, estudiante, modulo = escenario_completo(client)
    fecha = date.today() + timedelta(days=1)

    def _enviar(self, para, asunto, contenido, token, para_nombre=None):
        raise ServiceUnavailableException(causa="ConnectError")

    monkeypatch.setattr(ServiciosExternosClient, "enviar_correo", _enviar)

    resp = client.post(
        "/solicitudes-consultas",
        json=_payload(fecha, docente["id_usuario"], modulo["id"]),
        headers=auth(estudiante["token"]),
    )

    assert resp.status_code == 201, resp.text
    assert servicios_externos["correos"] == []
    # La notificación en base de datos sí quedó registrada.
    notificaciones = client.get("/notificaciones", headers=auth(docente["token"]))
    assert notificaciones.status_code == 200
    assert len(notificaciones.json()) == 1
