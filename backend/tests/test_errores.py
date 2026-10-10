from tests.helpers import (
    auth,
    crear_admin,
    crear_modulo,
    crear_solicitud,
    crear_usuario,
    mañana,
)


def test_formato_error_404(client):
    admin = crear_admin(client)
    resp = client.get("/programas/99999", headers=auth(admin["token"]))
    body = resp.json()
    assert resp.status_code == 404
    assert set(body) == {"timestamp", "status", "error", "message", "errors"}
    assert body["status"] == 404
    assert body["error"] == "Not Found"
    assert body["message"] == "Programa académico no encontrado."
    assert body["errors"] is None


def test_formato_error_validacion(client):
    estudiante = crear_usuario(client)
    docente = crear_usuario(client, rol="DOCENTE")
    admin = crear_admin(client)
    modulo = crear_modulo(client, admin["token"])

    resp = client.post(
        "/solicitudes-consultas",
        json={
            "prioridad": "MEDIA",
            "asunto": "",
            "descripcion": "Descripción",
            "fechaConsulta": mañana(),
            "horaConsulta": "06:30",
            "docenteId": docente["id_usuario"],
            "moduloId": modulo["id"],
        },
        headers=auth(estudiante["token"]),
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "Bad Request"
    assert body["errors"]["asunto"] == "El asunto no puede estar vacío"


def test_formato_hora_hhmm(client):
    admin = crear_admin(client)
    docente = crear_usuario(client, rol="DOCENTE")
    estudiante = crear_usuario(client)
    modulo = crear_modulo(client, admin["token"])

    sol = crear_solicitud(
        client,
        estudiante["token"],
        docente["id_usuario"],
        modulo["id"],
        hora="09:15",
    )
    assert sol["horaConsulta"] == "09:15"


def test_validacion_correo_formato(client):
    resp = client.post(
        "/auth/register",
        json={
            "identificacion": "0000000001",
            "nombre": "X",
            "apellido": "Y",
            "correo": "correo-mal-formato",
            "password": "contrasenia123",
            "rol": "ESTUDIANTE",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["errors"]["correo"] == "El correo no tiene un formato válido"