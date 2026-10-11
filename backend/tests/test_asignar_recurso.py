import pytest

from app.api.deps import get_infra_cliente
from app.exceptions.errors import ServiceUnavailableException
from app.main import app
from tests.helpers import (
    auth,
    crear_admin,
    crear_modulo,
    crear_solicitud,
    crear_usuario,
)


class ClienteFalso:
    def __init__(self, respuesta=None, error=None):
        self.respuesta = respuesta
        self.error = error
        self.llamadas = []

    def obtener_recurso_fisico(self, id_recurso, token):
        self.llamadas.append((id_recurso, token))
        if self.error is not None:
            raise self.error
        return self.respuesta


def _con_cliente(cliente: ClienteFalso) -> None:
    app.dependency_overrides[get_infra_cliente] = lambda: cliente


@pytest.fixture(autouse=True)
def _limpiar_overrides():
    yield
    app.dependency_overrides.pop(get_infra_cliente, None)


def _escenario(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante = crear_usuario(client, rol="ESTUDIANTE")
    modulo = crear_modulo(client, admin["token"])
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    return admin, docente, estudiante, modulo, sol


def _asignar(client, sol_id, recurso_id, token):
    return client.patch(
        f"/solicitudes-consultas/{sol_id}/recurso-fisico",
        json={"recursoFisicoId": recurso_id},
        headers=auth(token),
    )


def test_asignar_recurso_ok(client):
    _, docente, _, _, sol = _escenario(client)
    cliente = ClienteFalso(
        respuesta={"id": 7, "estado": True, "ubicacion": "Sede A · Bloque B · Salón 3"}
    )
    _con_cliente(cliente)

    resp = _asignar(client, sol["id"], 7, docente["token"])

    assert resp.status_code == 200
    assert resp.json()["recursoFisicoId"] == 7
    assert resp.json()["nombreRecursoFisico"] == "Sede A · Bloque B · Salón 3"
    assert cliente.llamadas == [(7, docente["token"])]


def test_asignar_recurso_no_existe(client):
    _, docente, _, _, sol = _escenario(client)
    _con_cliente(ClienteFalso(respuesta=None))

    resp = _asignar(client, sol["id"], 999, docente["token"])

    assert resp.status_code == 404
    assert resp.json()["message"] == "Recurso físico no encontrado."


def test_asignar_recurso_inactivo(client):
    _, docente, _, _, sol = _escenario(client)
    _con_cliente(ClienteFalso(respuesta={"id": 7, "estado": False, "ubicacion": "X"}))

    resp = _asignar(client, sol["id"], 7, docente["token"])

    assert resp.status_code == 400
    assert resp.json()["message"] == "El recurso físico está inactivo."


def test_asignar_recurso_servicio_caido(client):
    _, docente, _, _, sol = _escenario(client)
    _con_cliente(ClienteFalso(error=ServiceUnavailableException()))

    resp = _asignar(client, sol["id"], 7, docente["token"])

    assert resp.status_code == 503
    assert resp.json()["message"] == "Servicio de infraestructura no disponible"


def test_asignar_recurso_estudiante_forbidden(client):
    _, _, estudiante, _, sol = _escenario(client)
    _con_cliente(ClienteFalso(respuesta={"id": 7, "estado": True, "ubicacion": "X"}))

    resp = _asignar(client, sol["id"], 7, estudiante["token"])

    assert resp.status_code == 403
    assert resp.json()["error"] == "Forbidden"


def test_asignar_recurso_solicitud_resuelta(client):
    _, docente, _, _, sol = _escenario(client)
    _con_cliente(ClienteFalso(respuesta={"id": 7, "estado": True, "ubicacion": "X"}))

    client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth(docente["token"]),
    )
    client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "RESUELTA"},
        headers=auth(docente["token"]),
    )

    resp = _asignar(client, sol["id"], 7, docente["token"])

    assert resp.status_code == 400
    assert resp.json()["message"] == "No se puede asignar un recurso físico a esta consulta."
