from tests.helpers import (
    auth,
    crear_admin,
    crear_modulo,
    crear_programa,
    crear_solicitud,
    crear_usuario,
    escenario_completo,
    mañana,
)


def _solicitud_payload(docente_id, modulo_id):
    return {
        "prioridad": "MEDIA",
        "asunto": "Asunto",
        "descripcion": "Descripción",
        "fechaConsulta": mañana(),
        "horaConsulta": "06:30",
        "docenteId": docente_id,
        "moduloId": modulo_id,
    }


def test_login_devuelve_modulos(client):
    estudiante = crear_usuario(client)
    assert isinstance(estudiante["modulos"], list)
    nombres = {m["nombre"] for m in estudiante["modulos"]}
    assert "MIS_SOLICITUDES" in nombres
    assert all("nombre" in m and "ruta" in m and "icono" in m for m in estudiante["modulos"])


def test_auth_me(client):
    docente = crear_usuario(client, rol="DOCENTE")
    resp = client.get("/auth/me", headers=auth(docente["token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["rol"] == "DOCENTE"
    nombres = {m["nombre"] for m in body["modulos"]}
    assert "ATENCION_SOLICITUDES" in nombres
    assert "USUARIOS" not in nombres


def test_rutas_protegidas_sin_token(client):
    assert client.get("/usuarios").status_code == 401
    assert client.get("/roles").status_code == 401
    assert client.get("/modulos-sistema").status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_roles_requiere_modulo(client):
    estudiante = crear_usuario(client)
    resp = client.post("/roles", json={"nombre": "NUEVO_ROL"}, headers=auth(estudiante["token"]))
    assert resp.status_code == 403
    assert resp.json()["error"] == "Forbidden"


def test_crud_roles_y_asignacion_modulos(client):
    admin = crear_admin(client)
    token = admin["token"]

    roles = client.get("/roles", headers=auth(token)).json()
    nombres = {r["nombre"] for r in roles}
    assert {"ADMINISTRADOR", "DOCENTE", "ESTUDIANTE"} <= nombres

    resp = client.post(
        "/roles",
        json={"nombre": "AUXILIAR", "descripcion": "Rol auxiliar"},
        headers=auth(token),
    )
    assert resp.status_code == 201
    rol = resp.json()

    resp = client.post(
        "/roles",
        json={"nombre": "AUXILIAR"},
        headers=auth(token),
    )
    assert resp.status_code == 400

    modulos = client.get("/modulos-sistema", headers=auth(token)).json()
    ids = [m["id"] for m in modulos[:3]]

    resp = client.put(
        f"/roles/{rol['id']}/modulos", json={"moduloIds": ids}, headers=auth(token)
    )
    assert resp.status_code == 200
    assert {m["id"] for m in resp.json()} == set(ids)

    resp = client.get(f"/roles/{rol['id']}/modulos", headers=auth(token))
    assert {m["id"] for m in resp.json()} == set(ids)

    resp = client.put(
        f"/roles/{rol['id']}/modulos", json={"moduloIds": ids[:1]}, headers=auth(token)
    )
    assert {m["id"] for m in resp.json()} == {ids[0]}

    resp = client.delete(f"/roles/{rol['id']}", headers=auth(token))
    assert resp.status_code == 204


def test_no_desactivar_rol_con_usuarios(client):
    admin = crear_admin(client)
    crear_usuario(client, rol="ESTUDIANTE")
    roles = client.get("/roles", headers=auth(admin["token"])).json()
    rol_estudiante = next(r for r in roles if r["nombre"] == "ESTUDIANTE")
    resp = client.delete(f"/roles/{rol_estudiante['id']}", headers=auth(admin["token"]))
    assert resp.status_code == 400


def test_crear_usuario_por_admin(client):
    admin = crear_admin(client)
    resp = client.post(
        "/usuarios",
        json={
            "identificacion": "5555555555",
            "nombre": "Nuevo",
            "apellido": "Docente",
            "correo": "nuevo.docente@test.com",
            "password": "contrasenia123",
            "rol": "DOCENTE",
        },
        headers=auth(admin["token"]),
    )
    assert resp.status_code == 201
    assert resp.json()["rol"] == "DOCENTE"

    login = client.post(
        "/auth/login",
        json={"correo": "nuevo.docente@test.com", "password": "contrasenia123"},
    )
    assert login.status_code == 200


def test_listar_usuarios_requiere_modulo(client):
    docente = crear_usuario(client, rol="DOCENTE")
    assert client.get("/usuarios", headers=auth(docente["token"])).status_code == 403

    admin = crear_admin(client)
    assert client.get("/usuarios", headers=auth(admin["token"])).status_code == 200


def test_perfil_propio_o_modulo(client):
    docente = crear_usuario(client, rol="DOCENTE")
    otro = crear_usuario(client, rol="DOCENTE")

    propio = client.get(f"/usuarios/{docente['id_usuario']}", headers=auth(docente["token"]))
    assert propio.status_code == 200
    assert propio.json()["id"] == docente["id_usuario"]

    ajeno = client.get(f"/usuarios/{otro['id_usuario']}", headers=auth(docente["token"]))
    assert ajeno.status_code == 403


def test_eliminar_y_activar_usuario(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")

    resp = client.delete(f"/usuarios/{docente['id_usuario']}", headers=auth(admin["token"]))
    assert resp.status_code == 204
    assert client.get("/auth/me", headers=auth(docente["token"])).status_code == 401

    resp = client.patch(
        f"/usuarios/{docente['id_usuario']}/activar", headers=auth(admin["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] is True


def test_estudiante_solo_ve_sus_solicitudes(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante_a = crear_usuario(client, rol="ESTUDIANTE")
    estudiante_b = crear_usuario(client, rol="ESTUDIANTE")
    modulo = crear_modulo(client, admin["token"])

    sol_a = crear_solicitud(
        client, estudiante_a["token"], docente["id_usuario"], modulo["id"]
    )
    crear_solicitud(client, estudiante_b["token"], docente["id_usuario"], modulo["id"])

    resp = client.get("/solicitudes-consultas", headers=auth(estudiante_a["token"]))
    ids = [s["id"] for s in resp.json()]
    assert ids == [sol_a["id"]]

    resp = client.get("/solicitudes-consultas", headers=auth(admin["token"]))
    assert len(resp.json()) == 2


def test_estudiante_cancela_pero_no_acepta(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante = crear_usuario(client, rol="ESTUDIANTE")
    modulo = crear_modulo(client, admin["token"])

    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 403

    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "CANCELADA", "motivo": "Ya no la necesito"},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "CANCELADA"


def test_gestor_elimina_solicitud(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante = crear_usuario(client, rol="ESTUDIANTE")
    modulo = crear_modulo(client, admin["token"])

    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    resp = client.delete(
        f"/solicitudes-consultas/{sol['id']}", headers=auth(estudiante["token"])
    )
    assert resp.status_code == 403

    resp = client.delete(
        f"/solicitudes-consultas/{sol['id']}", headers=auth(admin["token"])
    )
    assert resp.status_code == 204
    assert (
        client.get(
            f"/solicitudes-consultas/{sol['id']}", headers=auth(admin["token"])
        ).status_code
        == 404
    )


def test_eliminar_comentario_autor_o_gestor(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante = crear_usuario(client, rol="ESTUDIANTE")
    modulo = crear_modulo(client, admin["token"])
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth(docente["token"]),
    )
    com = client.post(
        "/comentarios",
        json={"contenido": "Comentario", "solicitudConsultaId": sol["id"]},
        headers=auth(estudiante["token"]),
    ).json()

    resp = client.delete(f"/comentarios/{com['id']}", headers=auth(docente["token"]))
    assert resp.status_code == 403

    resp = client.delete(f"/comentarios/{com['id']}", headers=auth(estudiante["token"]))
    assert resp.status_code == 204


def test_eliminar_notificacion_destinatario(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante = crear_usuario(client, rol="ESTUDIANTE")
    modulo = crear_modulo(client, admin["token"])
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth(docente["token"]),
    )
    client.post(
        "/comentarios",
        json={"contenido": "Comentario", "solicitudConsultaId": sol["id"]},
        headers=auth(estudiante["token"]),
    )
    notif = client.get("/notificaciones", headers=auth(docente["token"])).json()[0]

    resp = client.delete(
        f"/notificaciones/{notif['id']}", headers=auth(estudiante["token"])
    )
    assert resp.status_code == 400

    resp = client.delete(
        f"/notificaciones/{notif['id']}", headers=auth(docente["token"])
    )
    assert resp.status_code == 204


def test_seeds_idempotentes(client):
    from app.db.seeds import ejecutar_seeds
    from app.db.session import SessionLocal
    from app.models.modulo_sistema import ModuloSistema
    from app.models.modulo_x_rol import ModuloXRol
    from app.models.rol import Rol

    with SessionLocal() as db:
        ejecutar_seeds(db)
        db.commit()
        roles_1 = db.query(Rol).count()
        modulos_1 = db.query(ModuloSistema).count()
        mxl_1 = db.query(ModuloXRol).count()

        ejecutar_seeds(db)
        db.commit()
        assert db.query(Rol).count() == roles_1 == 3
        assert db.query(ModuloSistema).count() == modulos_1
        assert db.query(ModuloXRol).count() == mxl_1


def test_crear_programa_requiere_modulo(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    crear_programa(client, admin["token"])

    resp = client.post(
        "/programas", json={"nombre": "Programa docente"}, headers=auth(docente["token"])
    )
    assert resp.status_code == 403