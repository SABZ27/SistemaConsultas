from tests.helpers import (
    auth,
    crear_admin,
    crear_bloque,
    crear_modulo,
    crear_programa,
    crear_recurso,
    crear_sede,
    crear_usuario,
)


def test_crud_programas(client):
    admin = crear_admin(client)
    prog = crear_programa(client, admin["token"])
    assert prog["estado"] is True
    assert prog["nombre"]

    resp = client.post(
        "/programas", json={"nombre": prog["nombre"]}, headers=auth(admin["token"])
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "Ya existe un programa académico con ese nombre."

    resp = client.get("/programas", headers=auth(admin["token"]))
    assert resp.status_code == 200
    assert any(p["id"] == prog["id"] for p in resp.json())

    resp = client.put(
        f"/programas/{prog['id']}",
        json={"nombre": "Programa Renombrado"},
        headers=auth(admin["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Programa Renombrado"

    resp = client.delete(f"/programas/{prog['id']}", headers=auth(admin["token"]))
    assert resp.status_code == 204

    resp = client.get("/programas", headers=auth(admin["token"]))
    assert all(p["id"] != prog["id"] for p in resp.json())

    resp = client.get("/programas/99999", headers=auth(admin["token"]))
    assert resp.status_code == 404
    assert resp.json()["message"] == "Programa académico no encontrado."


def test_crud_modulos(client):
    admin = crear_admin(client)
    mod = crear_modulo(client, admin["token"])
    assert mod["estado"] is True

    resp = client.put(
        f"/modulos/{mod['id']}",
        json={"nombre": "Módulo Actualizado", "descripcion": "Nueva descripción larga"},
        headers=auth(admin["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Módulo Actualizado"

    resp = client.post(
        "/modulos",
        json={
            "nombre": "Módulo Actualizado",
            "descripcion": "Descripción de prueba larga",
        },
        headers=auth(admin["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "Ya existe un módulo con ese nombre"

    resp = client.delete(f"/modulos/{mod['id']}", headers=auth(admin["token"]))
    assert resp.status_code == 204

    resp = client.get("/modulos/99999", headers=auth(admin["token"]))
    assert resp.status_code == 404
    assert resp.json()["message"] == "Módulo no encontrado."


def test_crud_sedes_bloques_recursos(client):
    admin = crear_admin(client)
    sede = crear_sede(client, admin["token"])
    bloque = crear_bloque(client, admin["token"], sede["id"])
    recurso = crear_recurso(client, admin["token"], bloque["id"])

    assert bloque["sedeId"] == sede["id"]
    assert bloque["sedeNombre"] == sede["nombre"]
    assert recurso["bloqueId"] == bloque["id"]
    assert recurso["bloqueNombre"] == bloque["nombre"]
    assert recurso["tipo"] == "SALON"

    resp = client.get("/bloques", headers=auth(admin["token"]))
    assert resp.status_code == 200
    assert any(b["id"] == bloque["id"] for b in resp.json())

    resp = client.get("/recursos-fisicos", headers=auth(admin["token"]))
    assert resp.status_code == 200
    assert any(r["id"] == recurso["id"] for r in resp.json())

    resp = client.put(
        f"/recursos-fisicos/{recurso['id']}",
        json={"nombre": "Recurso Renombrado"},
        headers=auth(admin["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Recurso Renombrado"

    resp = client.delete(
        f"/recursos-fisicos/{recurso['id']}", headers=auth(admin["token"])
    )
    assert resp.status_code == 204

    resp = client.get("/recursos-fisicos/99999", headers=auth(admin["token"]))
    assert resp.status_code == 404
    assert resp.json()["message"] == "Recurso físico no encontrado."

    resp = client.get("/bloques/99999", headers=auth(admin["token"]))
    assert resp.status_code == 404
    assert resp.json()["message"] == "Bloque no encontrado."

    resp = client.delete(f"/bloques/{bloque['id']}", headers=auth(admin["token"]))
    assert resp.status_code == 204


def test_rutas_sin_token(client):
    resp = client.post("/programas", json={"nombre": "No autorizado"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "Unauthorized"


def test_crear_programa_estudiante_forbidden(client):
    estudiante = crear_usuario(client)
    resp = client.post(
        "/programas",
        json={"nombre": "Programa estudiante"},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "Forbidden"