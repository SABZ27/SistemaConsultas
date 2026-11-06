"""Bloque C · C5: flujo de extremo a extremo con los tres roles del taller.

Estudiante crea consulta -> docente la atiende y retroalimenta -> administrador
asigna recurso -> docente la resuelve -> estudiante califica y ve la nota en su
propia consulta -> docente y administrador ven la nota.

Nota sobre el orden: ``_validar_estado`` (app/services/solicitud_consulta.py)
solo permite asignar recurso en PENDIENTE o EN_PROCESO, por lo que la
asignación del administrador se hace en EN_PROCESO, antes de RESUELTA. No se
modificó esa regla de negocio (Bloque C: solo cambios aditivos).

La regla de calificación NO se invierte: la crea el estudiante dueño y solo
con la consulta en RESUELTA (app/services/calificacion_consulta.py).
"""

from tests.helpers import (
    auth,
    crear_recurso,
    crear_sede,
    crear_solicitud,
    crear_zona,
    escenario_completo,
)


def test_flujo_tres_roles_estudiante_docente_administrador(client):
    admin, docente, estudiante, modulo = escenario_completo(client)

    # 1. Estudiante crea la consulta.
    sol = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"]
    )
    sid = sol["id"]
    assert sol["estado"] == "PENDIENTE"
    assert sol["calificacion"] is None
    assert sol["fechaActualizacion"] is not None
    assert sol["identificacionDocente"] is None  # enmascaramiento del Bloque G

    # 2. Docente la atiende (EN_PROCESO, con motivo) y retroalimenta.
    r = client.patch(
        f"/solicitudes-consultas/{sid}/estado",
        json={"estado": "EN_PROCESO", "motivo": "Reviso el caso con el estudiante."},
        headers=auth(docente["token"]),
    )
    assert r.status_code == 200, r.text

    r = client.post(
        "/comentarios",
        json={
            "contenido": "Retroalimentación del docente: revise el tema 3 del módulo.",
            "solicitudConsultaId": sid,
        },
        headers=auth(docente["token"]),
    )
    assert r.status_code == 201, r.text
    comentario_id = r.json()["id"]
    assert r.json()["fechaActualizacion"] is not None

    # 3. Administrador asigna el recurso físico (permitido en EN_PROCESO).
    sede = crear_sede(client, admin["token"], nombre="Sede Taller C5")
    zona = crear_zona(client, admin["token"], sede["id"], nombre="Bloque Taller C5")
    recurso = crear_recurso(
        client, admin["token"], sede["id"], zona["id"], nombre="Salón Taller C5"
    )
    r = client.patch(
        f"/solicitudes-consultas/{sid}/recurso-fisico",
        json={"recursoFisicoId": recurso["id"]},
        headers=auth(admin["token"]),
    )
    assert r.status_code == 200, r.text
    assert "Salón Taller C5" in r.json()["nombreRecursoFisico"]

    # 4. Docente resuelve la consulta.
    r = client.patch(
        f"/solicitudes-consultas/{sid}/estado",
        json={"estado": "RESUELTA", "motivo": "Caso resuelto en la asesoría."},
        headers=auth(docente["token"]),
    )
    assert r.status_code == 200, r.text

    # 5. Estudiante califica (regla existente, sin invertir).
    r = client.post(
        f"/solicitudes-consultas/{sid}/calificacion",
        json={"puntaje": 5, "comentario": "Excelente orientación, muy claro."},
        headers=auth(estudiante["token"]),
    )
    assert r.status_code == 201, r.text
    nota = r.json()
    assert nota["puntaje"] == 5
    assert nota["numeroConsulta"] == sol["numeroConsulta"]
    assert nota["nombreEstudiante"] and nota["nombreDocente"]
    assert nota["fechaActualizacion"] is not None
    # El enmascaramiento de datos personales se respeta: sin documento ni correo.
    assert "identificacion" not in nota and "correo" not in nota

    # El docente NO puede calificar: la regla no se invirtió.
    r = client.post(
        f"/solicitudes-consultas/{sid}/calificacion",
        json={"puntaje": 3, "comentario": "Intento del docente"},
        headers=auth(docente["token"]),
    )
    assert r.status_code == 403

    # 6. El estudiante ve la nota embebida en SU consulta, sin un segundo viaje.
    r = client.get(
        f"/solicitudes-consultas/{sid}", headers=auth(estudiante["token"])
    )
    assert r.status_code == 200
    detalle = r.json()
    assert detalle["calificacion"]["puntaje"] == 5
    assert detalle["calificacion"]["comentario"] == "Excelente orientación, muy claro."
    assert detalle["calificacion"]["fecha"] is not None
    assert detalle["fechaActualizacion"] is not None

    # Y ve la retroalimentación escrita por el docente.
    r = client.get(
        f"/comentarios/solicitud/{sid}", headers=auth(estudiante["token"])
    )
    assert r.status_code == 200
    assert any(c["id"] == comentario_id for c in r.json())

    # 7. Docente y administrador ven la nota (participante / gestor).
    for quien in (docente, admin):
        r = client.get(
            f"/solicitudes-consultas/{sid}/calificacion",
            headers=auth(quien["token"]),
        )
        assert r.status_code == 200, r.text
        assert r.json()["puntaje"] == 5
        r = client.get(
            f"/solicitudes-consultas/{sid}", headers=auth(quien["token"])
        )
        assert r.json()["calificacion"]["puntaje"] == 5

    # 8. El promedio del docente incluye su nombre legible.
    r = client.get(
        f"/docentes/{docente['id_usuario']}/calificaciones/promedio",
        headers=auth(estudiante["token"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["nombreDocente"]
    assert r.json()["total"] >= 1

    # 9. El endpoint de módulos sigue leyendo modulos_x_rol para cada rol.
    for quien in (estudiante, docente, admin):
        r = client.get("/auth/me/modulos", headers=auth(quien["token"]))
        assert r.status_code == 200
        assert r.json()

    # 10. Usuario, comentario y notificación exponen fechaActualizacion.
    r = client.get(
        f"/usuarios/{estudiante['id_usuario']}", headers=auth(estudiante["token"])
    )
    assert r.json()["fechaActualizacion"] is not None
    r = client.get("/notificaciones", headers=auth(estudiante["token"]))
    assert r.status_code == 200
    for notificacion in r.json():
        assert notificacion["fechaActualizacion"] is not None
