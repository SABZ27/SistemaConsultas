from tests.helpers import (
    auth,
    crear_recurso,
    crear_sede,
    crear_solicitud,
    crear_zona,
    escenario_completo,
)


def _escenario(client):
    admin, docente, estudiante, modulo = escenario_completo(client)
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
    admin, docente, _, _, sol = _escenario(client)
    sede = crear_sede(client, admin["token"], nombre="Sede A")
    zona = crear_zona(client, admin["token"], sede["id"], nombre="Bloque B")
    recurso = crear_recurso(
        client, admin["token"], sede["id"], zona["id"], nombre="Salón 3"
    )

    resp = _asignar(client, sol["id"], recurso["id"], docente["token"])

    assert resp.status_code == 200
    assert resp.json()["recursoFisicoId"] == recurso["id"]
    assert resp.json()["nombreRecursoFisico"] == "Sede A · Bloque B · Salón 3"


def test_asignar_recurso_no_existe(client):
    _, docente, _, _, sol = _escenario(client)

    resp = _asignar(client, sol["id"], 999, docente["token"])

    assert resp.status_code == 404
    assert resp.json()["message"] == "Recurso físico no encontrado."


def test_asignar_recurso_inactivo(client):
    admin, docente, _, _, sol = _escenario(client)
    sede = crear_sede(client, admin["token"], nombre="Sede A")
    zona = crear_zona(client, admin["token"], sede["id"], nombre="Bloque B")
    recurso = crear_recurso(
        client, admin["token"], sede["id"], zona["id"], nombre="Salón 3"
    )
    desactivado = client.delete(
        f"/recursos-fisicos/{recurso['id']}", headers=auth(admin["token"])
    )
    assert desactivado.status_code == 204, desactivado.text

    resp = _asignar(client, sol["id"], recurso["id"], docente["token"])

    assert resp.status_code == 400
    assert resp.json()["message"] == "El recurso físico está inactivo."


def test_asignar_recurso_estudiante_forbidden(client):
    _, _, estudiante, _, sol = _escenario(client)

    resp = _asignar(client, sol["id"], 7, estudiante["token"])

    assert resp.status_code == 403
    assert resp.json()["error"] == "Forbidden"


def test_asignar_recurso_solicitud_resuelta(client):
    _, docente, _, _, sol = _escenario(client)

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


def test_asignar_recurso_actualiza_nombre_guardado(client):
    admin, docente, _, _, sol = _escenario(client)
    sede = crear_sede(client, admin["token"], nombre="Sede Norte")
    zona = crear_zona(client, admin["token"], sede["id"], nombre="Piso 2")
    recurso = crear_recurso(
        client, admin["token"], sede["id"], zona["id"], nombre="Lab 1"
    )

    _asignar(client, sol["id"], recurso["id"], docente["token"])

    consulta = client.get(
        f"/solicitudes-consultas/{sol['id']}", headers=auth(docente["token"])
    )
    assert consulta.status_code == 200, consulta.text
    assert consulta.json()["nombreRecursoFisico"] == "Sede Norte · Piso 2 · Lab 1"
