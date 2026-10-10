from tests.helpers import crear_admin, crear_usuario, login


def test_registrar_estudiante(client):
    resp = client.post(
        "/auth/register",
        json={
            "identificacion": "1000000001",
            "nombre": "Nombre1",
            "apellido": "Apellido",
            "correo": "estudiante@test.com",
            "password": "contrasenia123",
            "rol": "ESTUDIANTE",
        },
    )
    assert resp.status_code == 201
    assert resp.json() == "Usuario registrado correctamente."

    res = login(client, "estudiante@test.com")
    assert res["token"]
    assert res["tipo"] == "Bearer"
    assert res["rol"] == "ESTUDIANTE"
    assert res["nombre"] == "Nombre1 Apellido"


def test_registro_correo_duplicado(client):
    crear_usuario(client, correo="repe@test.com")
    resp = client.post(
        "/auth/register",
        json={
            "identificacion": "1234567890",
            "nombre": "Otro",
            "apellido": "Usuario",
            "correo": "repe@test.com",
            "password": "contrasenia123",
            "rol": "ESTUDIANTE",
        },
    )
    assert resp.status_code == 400
    cuerpo = resp.json()
    assert cuerpo["status"] == 400
    assert cuerpo["error"] == "Bad Request"
    assert cuerpo["message"] == "El correo ya está registrado"
    assert "timestamp" in cuerpo and "errors" in cuerpo


def test_registro_identificacion_duplicada(client):
    crear_usuario(client, identificacion="SAME-IDENT")
    resp = client.post(
        "/auth/register",
        json={
            "identificacion": "SAME-IDENT",
            "nombre": "Otro",
            "apellido": "Usuario",
            "correo": "otro@test.com",
            "password": "contrasenia123",
            "rol": "ESTUDIANTE",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "La identificación ya está registrada."


def test_registro_rol_admin_permitido(client):
    admin = crear_admin(client)
    assert admin["rol"] == "ADMINISTRADOR"
    assert admin["token"]


def test_registro_programa_inexistente(client):
    resp = client.post(
        "/auth/register",
        json={
            "identificacion": "22222222",
            "nombre": "Prog",
            "apellido": "X",
            "correo": "prog@test.com",
            "password": "contrasenia123",
            "rol": "ESTUDIANTE",
            "programaId": 99999,
        },
    )
    assert resp.status_code == 404
    assert resp.json()["message"] == "Programa académico no encontrado"


def test_login_ok(client):
    crear_usuario(client, correo="login@test.com")
    res = login(client, "login@test.com")
    assert res["token"] and res["tipo"] == "Bearer"


def test_login_error_credenciales(client):
    crear_usuario(client, correo="pass@test.com")
    resp = client.post(
        "/auth/login", json={"correo": "pass@test.com", "password": "incorrecta"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "Unauthorized"


def test_login_usuario_desconocido(client):
    resp = client.post(
        "/auth/login", json={"correo": "noexiste@test.com", "password": "x"}
    )
    assert resp.status_code == 401


def test_reset_password_token_invalido(client):
    resp = client.post(
        "/auth/reset-password",
        json={"token": "token-invalido", "nuevaPassword": "nuevaContrasenia"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "Bad Request"
    assert resp.json()["message"] == "El token no es válido."


def test_forgot_password_flujo(client):
    crear_usuario(client, correo="forgot@test.com")
    resp = client.post("/auth/forgot-password", json={"correo": "forgot@test.com"})
    assert resp.status_code == 200
    assert resp.json() == "Se ha generado un token de recuperación."


def test_forgot_password_usuario_inexistente(client):
    resp = client.post("/auth/forgot-password", json={"correo": "nadie@test.com"})
    assert resp.status_code == 400
    assert resp.json()["message"] == "No existe un usuario registrado con ese correo."


def test_programas_publicos(client):
    resp = client.get("/programas")
    assert resp.status_code == 200


def test_solicitudes_listar_publicos(client):
    resp = client.get("/solicitudes-consultas")
    assert resp.status_code == 200