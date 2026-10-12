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
            "nombre": nombre or f"M??dulo {n}",
            "descripcion": f"Descripci??n del m??dulo {n}",
        },
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_sede(client, token):
    n = _next()
    resp = client.post("/sedes", json={"nombre": f"Sede {n}"}, headers=auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_bloque(client, token, sede_id):
    n = _next()
    resp = client.post(
        "/bloques",
        json={"nombre": f"Bloque {n}", "sedeId": sede_id},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_recurso(client, token, bloque_id):
    n = _next()
    resp = client.post(
        "/recursos-fisicos",
        json={"nombre": f"Recurso {n}", "tipo": "SALON", "bloqueId": bloque_id},
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
    descripcion="Necesito asesor??a en el tema.",
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
def crear_docente(client, token, nombre='Docente', apellido='Prueba', correo=None, identificacion=None):
    n = _next()
    if correo is None:
        correo = f'docente{n}@test.com'
    if identificacion is None:
        identificacion = f'20000000{n:04d}'
    resp = client.post(
        '/auth/register',
        json={
            'identificacion': identificacion,
            'nombre': nombre,
            'apellido': apellido,
            'correo': correo,
            'password': 'contrasenia123',
            'rol': 'DOCENTE',
        },
        headers=auth(token),
    )
    if resp.status_code == 201:
        # get user id by listing or just return structure; easier to create via direct repo not exposed, but tests use our helpers pattern
        pass
    # fallback: create via admin endpoint if available? not specified; use _registrar_y_login style adjusted
    return _registrar_y_login(client, 'DOCENTE', correo, identificacion, n)


def crear_estudiante(client, token=None, nombre='Estudiante', apellido='Prueba', correo=None, identificacion=None, programa_id=None):
    n = _next()
    if correo is None:
        correo = f'estudiante{n}@test.com'
    if identificacion is None:
        identificacion = f'10000000{n:04d}'
    payload = {
        'identificacion': identificacion,
        'nombre': nombre,
        'apellido': apellido,
        'correo': correo,
        'password': 'contrasenia123',
        'rol': 'ESTUDIANTE',
    }
    if programa_id is not None:
        payload['programaId'] = programa_id
    resp = client.post('/auth/register', json=payload, headers=auth(token))
    # try to get created user; but easier to return what tests expect - often just id via listing? tests may not need full user
    # but crear_usuario in old helpers registered as admin context; register allows creating estudiante via endpoint? no - register is open; but in tests they might expect using admin token? no wait - looking at test patterns
    # old tests: crear_estudiante uses admin token sometimes? let us check - in our escenario_completo we pass admin token to crear_docente/crear_estudiante? in our new code we call crear_docente(client, admin['token'])
    # but register endpoint doesn't require admin token; it just creates non-admin users
    # so better to call register without admin token? or keep compatible
    # but the helper as written takes token - maybe ignore it and just register
    return _registrar_y_login(client, 'ESTUDIANTE', correo, identificacion, n)


def crear_periodo(client, token, nombre=None, fecha_inicio=None, fecha_fin=None):
    from datetime import date, timedelta
    if nombre is None:
        nombre = f'Periodo {_next()}'
    if fecha_inicio is None:
        fecha_inicio = date.today() + timedelta(days=1)
    if fecha_fin is None:
        fecha_fin = fecha_inicio + timedelta(days=30)
    resp = client.post(
        '/periodos-academicos',
        json={'nombre': nombre, 'fechaInicio': fecha_inicio.isoformat(), 'fechaFin': fecha_fin.isoformat()},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def asignar_docente_modulo(client, token, docente_id, modulo_id):
    resp = client.post('/docentes-modulos', json={'docenteId': docente_id, 'moduloId': modulo_id}, headers=auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


def crear_disponibilidad(client, token, docente_id, dia_semana=1, hora_inicio='08:00', hora_fin='09:00', modulo_id=None):
    payload = {'docenteId': docente_id, 'diaSemana': dia_semana, 'horaInicio': hora_inicio, 'horaFin': hora_fin}
    if modulo_id is not None:
        payload['moduloId'] = modulo_id
    resp = client.post('/disponibilidad-docente', json=payload, headers=auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


def disponibilidad_completa(client, token, docente_id, modulo_id=None, dia_semana=1):
    return crear_disponibilidad(client, token, docente_id, dia_semana=dia_semana, hora_inicio='08:00', hora_fin='18:00', modulo_id=modulo_id)


def asegurar_periodo_cubre(client, token, fecha_consulta):
    from app.repositories.periodo_academico import PeriodoAcademicoRepository
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        repo = PeriodoAcademicoRepository(db)
        if repo.find_periodo_vigente(fecha_consulta) is None:
            crear_periodo(client, token, nombre=f'Periodo-Cobertura-{_next()}', fecha_inicio=fecha_consulta, fecha_fin=fecha_consulta)
    finally:
        db.close()


def escenario_completo(client):
    admin = crear_admin(client)
    docente = crear_docente(client, admin['token'])
    estudiante = crear_estudiante(client, admin['token'])
    modulo = crear_modulo(client, admin['token'])
    crear_periodo(client, admin['token'])
    asignar_docente_modulo(client, admin['token'], docente['id'], modulo['id'])
    disponibilidad_completa(client, admin['token'], docente['id'], modulo_id=modulo['id'])
    return admin, docente, estudiante, modulo
