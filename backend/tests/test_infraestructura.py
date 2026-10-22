from tests.helpers import (
    auth,
    crear_admin,
    crear_recurso,
    crear_sede,
    crear_usuario,
    crear_zona,
)


def _admin(client):
    return crear_admin(client)["token"]


def _docente(client):
    return crear_usuario(client, rol="DOCENTE")["token"]


def test_crear_sede_ok(client):
    token = _admin(client)

    resp = client.post(
        "/sedes",
        json={"nombre": "Sede Norte", "tipoEstructura": "BLOQUES"},
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["nombre"] == "Sede Norte"
    assert resp.json()["tipoEstructura"] == "BLOQUES"
    assert resp.json()["estado"] is True


def test_crear_sede_sin_permisos(client):
    resp = client.post(
        "/sedes",
        json={"nombre": "Sede Norte", "tipoEstructura": "BLOQUES"},
        headers=auth(_docente(client)),
    )

    assert resp.status_code == 403


def test_crear_sede_nombre_duplicado(client):
    token = _admin(client)
    crear_sede(client, token, nombre="Sede Norte")

    resp = client.post(
        "/sedes",
        json={"nombre": "Sede Norte", "tipoEstructura": "BLOQUES"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "Ya existe una sede activa con ese nombre."


def test_crear_sede_nombre_corto(client):
    resp = client.post(
        "/sedes",
        json={"nombre": "AB", "tipoEstructura": "BLOQUES"},
        headers=auth(_admin(client)),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "Error de validación."
    assert resp.json()["errors"]["nombre"] == "El nombre debe tener al menos 3 caracteres"


def test_crear_sede_tipo_invalido(client):
    resp = client.post(
        "/sedes",
        json={"nombre": "Sede Norte", "tipoEstructura": "TORRES"},
        headers=auth(_admin(client)),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "Error de validación."
    assert "El tipo de estructura" in resp.json()["errors"]["tipoEstructura"]


def test_leer_sedes_para_cualquier_autenticado(client):
    token = _admin(client)
    crear_sede(client, token, nombre="Sede Norte")

    resp = client.get("/sedes", headers=auth(_docente(client)))

    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1


def test_leer_inactivos_exige_infraestructura(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    client.delete(f"/sedes/{sede['id']}", headers=auth(token))

    resp = client.get("/sedes?incluirInactivos=true", headers=auth(_docente(client)))

    assert resp.status_code == 403


def test_desactivar_y_reactivar_sede(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")

    desactivada = client.delete(f"/sedes/{sede['id']}", headers=auth(token))
    assert desactivada.status_code == 204, desactivada.text

    listado = client.get("/sedes", headers=auth(token))
    assert listado.json() == []

    reactivada = client.patch(f"/sedes/{sede['id']}/activar", headers=auth(token))
    assert reactivada.status_code == 200, reactivada.text
    assert reactivada.json()["estado"] is True


def test_no_se_puede_desactivar_sede_con_zona_activa(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    crear_zona(client, token, sede["id"], nombre="Bloque B")

    resp = client.delete(f"/sedes/{sede['id']}", headers=auth(token))

    assert resp.status_code == 400
    assert (
        resp.json()["message"]
        == "No se puede desactivar la sede porque tiene zonas o recursos físicos activos."
    )


def test_no_se_puede_cambiar_tipo_estructura_con_hijos(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte", tipo_estructura="BLOQUES")
    crear_zona(client, token, sede["id"], nombre="Bloque B")

    resp = client.put(
        f"/sedes/{sede['id']}",
        json={"nombre": "Sede Norte", "tipoEstructura": "SALONES"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert "tipo de estructura" in resp.json()["message"]


def test_crear_zona_ok(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")

    resp = client.post(
        "/zonas",
        json={"sedeId": sede["id"], "nombre": "Bloque B"},
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["sedeId"] == sede["id"]
    assert resp.json()["nombre"] == "Bloque B"


def test_crear_zona_en_sede_salones_falla(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte", tipo_estructura="SALONES")

    resp = client.post(
        "/zonas",
        json={"sedeId": sede["id"], "nombre": "Bloque B"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "Una sede de tipo SALONES no admite zonas."


def test_crear_zona_nombre_duplicado_en_la_misma_sede(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    crear_zona(client, token, sede["id"], nombre="Bloque B")

    resp = client.post(
        "/zonas",
        json={"sedeId": sede["id"], "nombre": "Bloque B"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "Ya existe una zona activa con ese nombre en la sede."


def test_crear_zona_mismo_nombre_en_otra_sede_ok(client):
    token = _admin(client)
    sede_a = crear_sede(client, token, nombre="Sede Norte")
    sede_b = crear_sede(client, token, nombre="Sede Sur")
    crear_zona(client, token, sede_a["id"], nombre="Bloque B")

    resp = client.post(
        "/zonas",
        json={"sedeId": sede_b["id"], "nombre": "Bloque B"},
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text


def test_crear_zona_con_sede_inexistente(client):
    resp = client.post(
        "/zonas",
        json={"sedeId": 999, "nombre": "Bloque B"},
        headers=auth(_admin(client)),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "La sede indicada no existe o está inactiva."


def test_no_se_puede_desactivar_zona_con_recurso_activo(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    zona = crear_zona(client, token, sede["id"], nombre="Bloque B")
    crear_recurso(client, token, sede["id"], zona["id"], nombre="Salón 3")

    resp = client.delete(f"/zonas/{zona['id']}", headers=auth(token))

    assert resp.status_code == 400
    assert (
        resp.json()["message"]
        == "No se puede desactivar la zona porque tiene recursos físicos activos."
    )


def test_crear_recurso_ok(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    zona = crear_zona(client, token, sede["id"], nombre="Bloque B")

    resp = client.post(
        "/recursos-fisicos",
        json={
            "sedeId": sede["id"],
            "zonaId": zona["id"],
            "nombre": "Salón 3",
            "tipo": "SALON",
        },
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["ubicacion"] == "Sede Norte · Bloque B · Salón 3"
    assert resp.json()["tipo"] == "SALON"


def test_crear_recurso_con_zona_de_otra_sede_falla(client):
    token = _admin(client)
    sede_a = crear_sede(client, token, nombre="Sede Norte")
    sede_b = crear_sede(client, token, nombre="Sede Sur")
    zona_a = crear_zona(client, token, sede_a["id"], nombre="Bloque B")

    resp = client.post(
        "/recursos-fisicos",
        json={"sedeId": sede_b["id"], "zonaId": zona_a["id"], "nombre": "Salón 3"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "La zona indicada no pertenece a la sede del recurso."


def test_crear_recurso_sin_zona_en_sede_bloques_falla(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte", tipo_estructura="BLOQUES")

    resp = client.post(
        "/recursos-fisicos",
        json={"sedeId": sede["id"], "nombre": "Salón 3"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert (
        resp.json()["message"]
        == "Debe indicar la zona del recurso para sedes de tipo BLOQUES o PISOS."
    )


def test_crear_recurso_en_sede_salones_sin_zona_ok(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte", tipo_estructura="SALONES")

    resp = client.post(
        "/recursos-fisicos",
        json={"sedeId": sede["id"], "nombre": "Salón 3"},
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["ubicacion"] == "Sede Norte · Salón 3"
    assert resp.json()["zonaId"] is None


def test_crear_recurso_con_zona_en_sede_salones_falla(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte", tipo_estructura="SALONES")

    # Una sede SALONES no admite zonas por API; se inserta directamente en la
    # base para verificar la validación defensiva del servicio.
    from app.db.session import SessionLocal
    from app.models.zona import Zona

    db = SessionLocal()
    try:
        zona = Zona(sede_id=sede["id"], nombre="Bloque B")
        db.add(zona)
        db.commit()
        zona_id = zona.id
    finally:
        db.close()

    resp = client.post(
        "/recursos-fisicos",
        json={"sedeId": sede["id"], "zonaId": zona_id, "nombre": "Salón 3"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["message"] == "Una sede de tipo SALONES no admite zonas en sus recursos."


def test_crear_recurso_duplicado_en_la_misma_zona_falla(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    zona = crear_zona(client, token, sede["id"], nombre="Bloque B")
    crear_recurso(client, token, sede["id"], zona["id"], nombre="Salón 3")

    resp = client.post(
        "/recursos-fisicos",
        json={"sedeId": sede["id"], "zonaId": zona["id"], "nombre": "Salón 3"},
        headers=auth(token),
    )

    assert resp.status_code == 400
    assert (
        resp.json()["message"]
        == "Ya existe un recurso físico activo con ese nombre en la sede o zona indicada."
    )


def test_crear_recurso_mismo_nombre_en_otra_zona_ok(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    zona_a = crear_zona(client, token, sede["id"], nombre="Bloque A")
    zona_b = crear_zona(client, token, sede["id"], nombre="Bloque B")
    crear_recurso(client, token, sede["id"], zona_a["id"], nombre="Salón 3")

    resp = client.post(
        "/recursos-fisicos",
        json={"sedeId": sede["id"], "zonaId": zona_b["id"], "nombre": "Salón 3"},
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text


def test_desactivar_y_reactivar_recurso(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    zona = crear_zona(client, token, sede["id"], nombre="Bloque B")
    recurso = crear_recurso(client, token, sede["id"], zona["id"], nombre="Salón 3")

    desactivado = client.delete(
        f"/recursos-fisicos/{recurso['id']}", headers=auth(token)
    )
    assert desactivado.status_code == 204, desactivado.text

    listado = client.get("/recursos-fisicos", headers=auth(token))
    assert listado.json() == []

    reactivado = client.patch(
        f"/recursos-fisicos/{recurso['id']}/activar", headers=auth(token)
    )
    assert reactivado.status_code == 200, reactivado.text
    assert reactivado.json()["estado"] is True


def test_listar_estructura_de_sede(client):
    token = _admin(client)
    sede = crear_sede(client, token, nombre="Sede Norte")
    zona = crear_zona(client, token, sede["id"], nombre="Bloque B")
    crear_recurso(client, token, sede["id"], zona["id"], nombre="Salón 3")

    zonas = client.get(f"/sedes/{sede['id']}/zonas", headers=auth(token))
    recursos = client.get(f"/sedes/{sede['id']}/recursos-fisicos", headers=auth(token))
    recursos_zona = client.get(f"/zonas/{zona['id']}/recursos-fisicos", headers=auth(token))

    assert zonas.status_code == 200, zonas.text
    assert len(zonas.json()) == 1
    assert len(recursos.json()) == 1
    assert len(recursos_zona.json()) == 1
