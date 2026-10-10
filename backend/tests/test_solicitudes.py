from datetime import date, timedelta

from tests.helpers import (
    auth,
    crear_admin,
    crear_bloque,
    crear_modulo,
    crear_recurso,
    crear_sede,
    crear_solicitud,
    crear_usuario,
    mañana,
)


def _escenario_base(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante = crear_usuario(client, rol="ESTUDIANTE")
    sede = crear_sede(client, admin["token"])
    bloque = crear_bloque(client, admin["token"], sede["id"])
    recurso = crear_recurso(client, admin["token"], bloque["id"])
    modulo = crear_modulo(client, admin["token"])
    return admin, docente, estudiante, sede, bloque, recurso, modulo


def _poner_en_proceso(client, docente, sol_id):
    resp = client.patch(
        f"/solicitudes-consultas/{sol_id}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 200, resp.text


def test_flujo_solicitud_completo(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)

    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    assert sol["estado"] == "PENDIENTE"
    assert sol["prioridad"] == "MEDIA"
    assert sol["horaConsulta"] == "06:30"
    assert sol["nombrePrograma"] == "Sin programa"
    assert sol["nombreRecursoFisico"] == "Sin asignar"
    assert sol["numeroConsulta"].startswith(f"SC-{date.today().year}-000001")
    assert sol["docenteId"] == docente["id_usuario"]
    assert sol["estudianteId"] == estudiante["id_usuario"]

    resp = client.get("/solicitudes-consultas")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get(
        f"/solicitudes-consultas/{sol['id']}", headers=auth(docente["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == sol["id"]


def test_crear_solicitud_sin_token(client):
    _, docente, _, _, _, _, modulo = _escenario_base(client)
    resp = client.post(
        "/solicitudes-consultas",
        json={
            "prioridad": "MEDIA",
            "asunto": "Asunto",
            "descripcion": "Descripción",
            "fechaConsulta": mañana(),
            "horaConsulta": "06:30",
            "docenteId": docente["id_usuario"],
            "moduloId": modulo["id"],
        },
    )
    assert resp.status_code == 401


def test_crear_solicitud_docente_forbidden(client):
    _, docente, _, _, _, _, modulo = _escenario_base(client)
    resp = client.post(
        "/solicitudes-consultas",
        json={
            "prioridad": "MEDIA",
            "asunto": "Asunto",
            "descripcion": "Descripción",
            "fechaConsulta": mañana(),
            "horaConsulta": "06:30",
            "docenteId": docente["id_usuario"],
            "moduloId": modulo["id"],
        },
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "El usuario indicado no tiene el rol ESTUDIANTE."


def test_crear_solicitud_docente_invalido(client):
    _, _, estudiante, _, _, _, modulo = _escenario_base(client)
    resp = client.post(
        "/solicitudes-consultas",
        json={
            "prioridad": "MEDIA",
            "asunto": "Asunto",
            "descripcion": "Descripción",
            "fechaConsulta": mañana(),
            "horaConsulta": "06:30",
            "docenteId": 99999,
            "moduloId": modulo["id"],
        },
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "Not Found"
    assert resp.json()["message"] == "Docente no encontrado."


def test_crear_solicitud_fecha_pasada(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    ayer = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post(
        "/solicitudes-consultas",
        json={
            "prioridad": "MEDIA",
            "asunto": "Asunto",
            "descripcion": "Descripción",
            "fechaConsulta": ayer,
            "horaConsulta": "06:30",
            "docenteId": docente["id_usuario"],
            "moduloId": modulo["id"],
        },
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 400
    assert (
        resp.json()["message"]
        == "La fecha de la consulta no puede ser anterior a la fecha actual."
    )


def test_crear_solicitud_modulo_invalido(client):
    _, docente, estudiante, _, _, _, _ = _escenario_base(client)
    resp = client.post(
        "/solicitudes-consultas",
        json={
            "prioridad": "MEDIA",
            "asunto": "Asunto",
            "descripcion": "Descripción",
            "fechaConsulta": mañana(),
            "horaConsulta": "06:30",
            "docenteId": docente["id_usuario"],
            "moduloId": 99999,
        },
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 404
    assert resp.json()["message"] == "Módulo no encontrado."


def test_cambiar_estado_flujo_estados(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 200
    rj = resp.json()
    assert rj["estado"] == "EN_PROCESO"
    assert rj["recursoFisicoId"] is None

    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "RESUELTA"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "RESUELTA"


def test_cambiar_estado_requiere_participante(client):
    admin, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth(admin["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "El usuario no pertenece a esta solicitud."


def test_cambiar_estado_mismo_estado(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "PENDIENTE"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "La solicitud ya se encuentra en estado PENDIENTE."


def test_cambiar_estado_motivo_obligatorio(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "RECHAZADA"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "Debe indicar un motivo para RECHAZADA."

    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "RECHAZADA", "motivo": "No disponible"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "RECHAZADA"


def test_asignar_recurso_manual(client):
    _, docente, estudiante, _, _, recurso, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/recurso-fisico",
        json={"recursoFisicoId": recurso["id"]},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["recursoFisicoId"] == recurso["id"]
    assert resp.json()["nombreRecursoFisico"] == recurso["nombre"]


def test_asignar_recurso_solicitud_resuelta(client):
    _, docente, estudiante, _, _, recurso, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    _poner_en_proceso(client, docente, sol["id"])
    client.patch(
        f"/solicitudes-consultas/{sol['id']}/estado",
        json={"estado": "RESUELTA"},
        headers=auth(docente["token"]),
    )

    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/recurso-fisico",
        json={"recursoFisicoId": recurso["id"]},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "No se puede asignar un recurso físico a esta consulta."


def test_reasignar_docente(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    nuevo_docente = crear_usuario(client, rol="DOCENTE")
    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/docente",
        json={"docenteId": nuevo_docente["id_usuario"]},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["docenteId"] == nuevo_docente["id_usuario"]
    assert resp.json()["nombreCompletoDocente"] == nuevo_docente["nombre"]


def test_reasignar_docente_no_docente(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    otro_estudiante = crear_usuario(client, rol="ESTUDIANTE")
    resp = client.patch(
        f"/solicitudes-consultas/{sol['id']}/docente",
        json={"docenteId": otro_estudiante["id_usuario"]},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "El usuario indicado no tiene el rol DOCENTE."


def test_actualizar_solicitud_sin_motivo(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    resp = client.put(
        f"/solicitudes-consultas/{sol['id']}",
        json={
            "prioridad": "BAJA",
            "asunto": "Asunto actualizado",
            "descripcion": "Descripción actualizada",
            "fechaConsulta": (date.today() + timedelta(days=3)).isoformat(),
            "horaConsulta": "08:00",
            "moduloId": modulo["id"],
        },
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 400
    assert (
        resp.json()["message"]
        == "Debe indicar un motivo cuando se modifica la fecha o la hora de la consulta."
    )


def test_actualizar_solicitud_con_motivo(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    resp = client.put(
        f"/solicitudes-consultas/{sol['id']}",
        json={
            "prioridad": "BAJA",
            "asunto": "Asunto actualizado",
            "descripcion": "Descripción actualizada",
            "fechaConsulta": (date.today() + timedelta(days=3)).isoformat(),
            "horaConsulta": "08:00",
            "moduloId": modulo["id"],
            "motivo": "Cambio de horario",
        },
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 200
    rj = resp.json()
    assert rj["asunto"] == "Asunto actualizado"
    assert rj["horaConsulta"] == "08:00"


def test_comentarios_flujo(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    _poner_en_proceso(client, docente, sol["id"])

    resp = client.post(
        "/comentarios",
        json={"contenido": "Primer comentario", "solicitudConsultaId": sol["id"]},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 201
    com = resp.json()
    assert com["numeroConsulta"] == sol["numeroConsulta"]
    assert com["editado"] is False

    resp = client.get(
        f"/comentarios/solicitud/{sol['id']}", headers=auth(docente["token"])
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.put(
        f"/comentarios/{com['id']}",
        json={"contenido": "Comentario editado"},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["contenido"] == "Comentario editado"
    assert resp.json()["editado"] is True

    resp = client.put(
        f"/comentarios/{com['id']}",
        json={"contenido": "No es mío"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "Solo puedes editar tus propios comentarios."

    resp = client.get(f"/comentarios/{com['id']}", headers=auth(estudiante["token"]))
    assert resp.status_code == 200
    assert resp.json()["id"] == com["id"]


def test_comentar_solicitud_pendiente_rechazado(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )

    resp = client.post(
        "/comentarios",
        json={"contenido": "Comentario", "solicitudConsultaId": sol["id"]},
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "No puede comentar esta consulta."


def test_comentar_no_participante(client):
    admin, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    _poner_en_proceso(client, docente, sol["id"])

    resp = client.post(
        "/comentarios",
        json={"contenido": "Intruso", "solicitudConsultaId": sol["id"]},
        headers=auth(admin["token"]),
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "El usuario no pertenece a esta solicitud."


def test_notificaciones_flujo(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    _poner_en_proceso(client, docente, sol["id"])

    client.post(
        "/comentarios",
        json={"contenido": "Comentario", "solicitudConsultaId": sol["id"]},
        headers=auth(estudiante["token"]),
    )

    resp = client.get("/notificaciones", headers=auth(docente["token"]))
    assert resp.status_code == 200
    notificaciones = resp.json()
    assert len(notificaciones) == 1
    notif = notificaciones[0]
    assert notif["numeroConsulta"] == sol["numeroConsulta"]
    assert notif["leida"] is False

    resp = client.get("/notificaciones/no-leidas/count", headers=auth(docente["token"]))
    assert resp.status_code == 200
    assert resp.json() == 1

    resp = client.patch(
        f"/notificaciones/{notif['id']}/leer", headers=auth(docente["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["leida"] is True

    resp = client.get("/notificaciones/no-leidas/count", headers=auth(docente["token"]))
    assert resp.json() == 0


def test_marcar_notificacion_ajena(client):
    _, docente, estudiante, _, _, _, modulo = _escenario_base(client)
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    _poner_en_proceso(client, docente, sol["id"])

    client.post(
        "/comentarios",
        json={"contenido": "Comentario", "solicitudConsultaId": sol["id"]},
        headers=auth(estudiante["token"]),
    )
    notificaciones = client.get(
        "/notificaciones", headers=auth(docente["token"])
    ).json()
    notif_id = notificaciones[0]["id"]

    resp = client.patch(
        f"/notificaciones/{notif_id}/leer", headers=auth(estudiante["token"])
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "Esta notificación no le pertenece."


def test_estado_solicitud_404(client):
    _, docente, _, _, _, _, _ = _escenario_base(client)
    resp = client.patch(
        "/solicitudes-consultas/99999/estado",
        json={"estado": "RESUELTA"},
        headers=auth(docente["token"]),
    )
    assert resp.status_code == 404
    assert resp.json()["message"] == "Solicitud no encontrada."