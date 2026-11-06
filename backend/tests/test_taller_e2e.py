"""Bloque C · C3/C5: flujo de extremo a extremo con los tres roles del taller.

Estudiante crea consulta -> docente la atiende y retroalimenta -> administrador
asigna recurso -> docente la resuelve -> estudiante califica y ve la nota +
retroalimentación en su propia consulta -> docente y administrador ven la nota.

Nota sobre el orden: ``_validar_estado`` (app/services/solicitud_consulta.py)
solo permite asignar recurso en PENDIENTE o EN_PROCESO, por lo que la
asignación del administrador se hace en EN_PROCESO, antes de RESUELTA. No se
modificó esa regla de negocio (Bloque C: solo cambios aditivos).

La regla de calificación NO se invierte: la crea el estudiante dueño y solo
con la consulta en RESUELTA (app/services/calificacion_consulta.py).
"""

from sqlalchemy import event

from app.db.session import engine
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
    assert sol["retroalimentacionDocente"] is None
    assert sol["fechaActualizacion"] is not None
    assert sol["identificacionDocente"] is None  # enmascaramiento del Bloque G
    assert sol["identificacionEstudiante"] is not None

    # 2. Docente la atiende (EN_PROCESO) y retroalimenta con un comentario.
    r = client.patch(
        f"/solicitudes-consultas/{sid}/estado",
        json={"estado": "EN_PROCESO", "motivo": "Reviso el caso con el estudiante."},
        headers=auth(docente["token"]),
    )
    assert r.status_code == 200, r.text

    texto_retroalimentacion = (
        "Retroalimentación del docente: revise el tema 3 del módulo y traiga "
        "el ejercicio resuelto a la próxima asesoría."
    )
    r = client.post(
        "/comentarios",
        json={"contenido": texto_retroalimentacion, "solicitudConsultaId": sid},
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
    assert "identificacion" not in nota and "correo" not in nota

    # El docente NO puede calificar: la regla no se invirtió.
    r = client.post(
        f"/solicitudes-consultas/{sid}/calificacion",
        json={"puntaje": 3, "comentario": "Intento del docente"},
        headers=auth(docente["token"]),
    )
    assert r.status_code == 403

    # 6. El estudiante ve nota y retroalimentación en el DETALLE, sin segundo viaje.
    r = client.get(
        f"/solicitudes-consultas/{sid}", headers=auth(estudiante["token"])
    )
    assert r.status_code == 200
    detalle = r.json()
    assert detalle["calificacion"]["puntaje"] == 5
    assert detalle["calificacion"]["comentario"] == "Excelente orientación, muy claro."
    assert detalle["calificacion"]["fecha"] is not None
    assert detalle["retroalimentacionDocente"] == texto_retroalimentacion
    assert detalle["fechaActualizacion"] is not None
    # Enmascaramiento intacto.
    assert detalle["identificacionDocente"] is None
    assert detalle["identificacionEstudiante"] is not None
    assert detalle["nombreCompletoDocente"] and detalle["nombreCompletoEstudiante"]

    # 7. El estudiante ve nota y retroalimentación también en el LISTADO.
    r = client.get("/solicitudes-consultas", headers=auth(estudiante["token"]))
    assert r.status_code == 200
    fila = next(s for s in r.json() if s["id"] == sid)
    assert fila["calificacion"]["puntaje"] == 5
    assert fila["retroalimentacionDocente"] == texto_retroalimentacion

    # Y ve la retroalimentación escrita por el docente en los comentarios.
    r = client.get(
        f"/comentarios/solicitud/{sid}", headers=auth(estudiante["token"])
    )
    assert r.status_code == 200
    assert any(c["id"] == comentario_id for c in r.json())

    # 8. Sin comentarios del docente -> retroalimentacionDocente null.
    sin_comentarios = crear_solicitud(
        client, estudiante["token"], docente["id_usuario"], modulo["id"],
        hora="07:30",
    )
    r = client.get(
        f"/solicitudes-consultas/{sin_comentarios['id']}",
        headers=auth(estudiante["token"]),
    )
    assert r.status_code == 200
    assert r.json()["retroalimentacionDocente"] is None
    assert r.json()["calificacion"] is None
    r = client.get("/solicitudes-consultas", headers=auth(estudiante["token"]))
    fila_sin = next(s for s in r.json() if s["id"] == sin_comentarios["id"])
    assert fila_sin["retroalimentacionDocente"] is None

    # 9. Docente y administrador ven la nota (participante / gestor).
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

    # 10. El promedio del docente incluye su nombre legible.
    r = client.get(
        f"/docentes/{docente['id_usuario']}/calificaciones/promedio",
        headers=auth(estudiante["token"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["nombreDocente"]
    assert r.json()["total"] >= 1

    # 11. El endpoint de módulos sigue leyendo modulos_x_rol para cada rol.
    for quien in (estudiante, docente, admin):
        r = client.get("/auth/me/modulos", headers=auth(quien["token"]))
        assert r.status_code == 200
        assert r.json()

    # 12. Usuario, comentario y notificación exponen fechaActualizacion.
    r = client.get(
        f"/usuarios/{estudiante['id_usuario']}", headers=auth(estudiante["token"])
    )
    assert r.json()["fechaActualizacion"] is not None
    r = client.get("/notificaciones", headers=auth(estudiante["token"]))
    assert r.status_code == 200
    for notificacion in r.json():
        assert notificacion["fechaActualizacion"] is not None


def test_listado_carga_calificaciones_y_comentarios_por_lote(client):
    """Ni `calificacion` ni `retroalimentacionDocente` generan N+1 en el listado."""
    _, docente, estudiante, modulo = escenario_completo(client)
    for i in range(4):
        sol = crear_solicitud(
            client, estudiante["token"], docente["id_usuario"], modulo["id"],
            hora=f"0{i + 6}:30",
        )
        r = client.patch(
            f"/solicitudes-consultas/{sol['id']}/estado",
            json={"estado": "EN_PROCESO"},
            headers=auth(docente["token"]),
        )
        assert r.status_code == 200, r.text
        r = client.post(
            "/comentarios",
            json={
                "contenido": f"Retroalimentación {i} del docente.",
                "solicitudConsultaId": sol["id"],
            },
            headers=auth(docente["token"]),
        )
        assert r.status_code == 201, r.text

    sentencias: list[str] = []

    def registrar(_conn, _cursor, statement, _parameters, _context, _executemany):
        sentencias.append(" ".join(statement.split()))

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        r = client.get(
            "/solicitudes-consultas", headers=auth(estudiante["token"])
        )
        assert r.status_code == 200
        assert len(r.json()) >= 4
        assert all(s["retroalimentacionDocente"] for s in r.json())
    finally:
        event.remove(engine, "before_cursor_execute", registrar)

    consultas_comentarios = [
        s for s in sentencias if "FROM comentarios" in s
    ]
    consultas_calificaciones = [
        s for s in sentencias if "FROM calificaciones_consulta" in s
    ]
    assert len(consultas_comentarios) <= 1
    assert len(consultas_calificaciones) <= 1
