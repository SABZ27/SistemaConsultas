from app.api.deps import get_infra_cliente
from app.main import app
from tests.helpers import auth, crear_solicitud, crear_usuario, escenario_completo


class ClienteFalso:
    def __init__(self, respuesta):
        self.respuesta = respuesta

    def obtener_recurso_fisico(self, id_recurso, token):
        return self.respuesta


def _cambiar_estado(client, docente, sol_id, estado):
    resp = client.patch(
        f"/solicitudes-consultas/{sol_id}/estado",
        json={"estado": estado},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_cambio_estado_genera_notificacion_visible(client):
    _, docente, estudiante, modulo = escenario_completo(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    assert client.get(
        "/notificaciones/no-leidas/count", headers=auth(estudiante["token"])
    ).json() == 0

    _cambiar_estado(client, docente, sol["id"], "EN_PROCESO")

    resp = client.get("/notificaciones", headers=auth(estudiante["token"]))
    assert resp.status_code == 200
    notifs = resp.json()
    assert len(notifs) == 1
    assert notifs[0]["tipo"] == "CAMBIO_ESTADO"
    assert notifs[0]["numeroConsulta"] == sol["numeroConsulta"]
    assert notifs[0]["leida"] is False

    assert client.get(
        "/notificaciones/no-leidas/count", headers=auth(estudiante["token"])
    ).json() == 1


def test_asignar_recurso_genera_notificacion_visible(client):
    _, docente, estudiante, modulo = escenario_completo(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    app.dependency_overrides[get_infra_cliente] = lambda: ClienteFalso(
        {"id": 7, "estado": True, "ubicacion": "Sede A · Bloque B · Salón 3"}
    )
    try:
        resp = client.patch(
            f"/solicitudes-consultas/{sol['id']}/recurso-fisico",
            json={"recursoFisicoId": 7},
            headers=auth(docente["token"]),
        )
        assert resp.status_code == 200, resp.text
    finally:
        app.dependency_overrides.pop(get_infra_cliente, None)

    notifs = client.get("/notificaciones", headers=auth(estudiante["token"])).json()
    assert len(notifs) == 1
    assert notifs[0]["tipo"] == "ASIGNACION_RECURSO"


def test_marcar_leida_baja_contador(client):
    _, docente, estudiante, modulo = escenario_completo(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    _cambiar_estado(client, docente, sol["id"], "EN_PROCESO")

    notifs = client.get("/notificaciones", headers=auth(estudiante["token"])).json()
    assert len(notifs) == 1
    assert client.get(
        "/notificaciones/no-leidas/count", headers=auth(estudiante["token"])
    ).json() == 1

    resp = client.patch(
        f"/notificaciones/{notifs[0]['id']}/leer", headers=auth(estudiante["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["leida"] is True
    assert client.get(
        "/notificaciones/no-leidas/count", headers=auth(estudiante["token"])
    ).json() == 0


def test_no_puede_ver_ni_leer_notificaciones_ajenas(client):
    _, docente, estudiante, modulo = escenario_completo(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    _cambiar_estado(client, docente, sol["id"], "EN_PROCESO")
    intruso = crear_usuario(client, rol="ESTUDIANTE")

    propias = client.get("/notificaciones", headers=auth(estudiante["token"])).json()
    assert len(propias) == 1

    assert client.get(
        "/notificaciones", headers=auth(intruso["token"])
    ).json() == []

    resp = client.patch(
        f"/notificaciones/{propias[0]['id']}/leer", headers=auth(intruso["token"])
    )
    assert resp.status_code == 400  # comportamiento actual: 400
