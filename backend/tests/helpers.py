from datetime import date, timedelta

_contador = {"n": 0}


def _next():
    _contador["n"] += 1
    return _contador["n"]


def _registrar_y_login(client, rol, correo, identificacion, n):
    payload = {
        "identificacion": identificacion,
        "nombre": f"Nombre{n}",
        "apellido": "Apellido",
        "correo": correo,
        "password": "contrasenia123",
        "rol": rol,
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return login(client, correo)


def crear_usuario(client, rol="ESTUDIANTE", correo=None, identificacion=None):
    n = _next()
    correo = correo or f"usuario{n}@test.com"
    identificacion = identificacion or f"10000000{n:04d}"
    return _registrar_y_login(client, rol, correo, identificacion, n)


def login(client, correo, password="contrasenia123"):
    resp = client.post("/auth/login", json={"correo": correo, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def crear_admin(client):
    return login(client, "admin@test.com")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def crear_programa(client, token, nombre=None):
    n = _next()
    resp = client.post(
        "/programas",
        json={"nombre": nombre or f"Programa {n}"},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_modulo(client, token, nombre=None):
    n = _next()
    resp = client.post(
        "/modulos",
        json={
            "nombre": nombre or f"Módulo {n}",
            "descripcion": f"Descripción del módulo {n}",
        },
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_solicitud(
    client,
    token,
    docente_id,
    modulo_id,
    fecha=None,
    hora="06:30",
    prioridad="MEDIA",
    asunto="Consulta de prueba",
    descripcion="Necesito asesoría en el tema.",
):
    resp = client.post(
        "/solicitudes-consultas",
        json={
            "prioridad": prioridad,
            "asunto": asunto,
            "descripcion": descripcion,
            "fechaConsulta": fecha or (date.today() + timedelta(days=1)).isoformat(),
            "horaConsulta": hora,
            "docenteId": docente_id,
            "moduloId": modulo_id,
        },
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def mañana():
    return (date.today() + timedelta(days=1)).isoformat()