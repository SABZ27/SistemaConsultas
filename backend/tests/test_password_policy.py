from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.core.password_policy import (
    MENSAJE_COMUN,
    MENSAJE_COMPOSICION,
    MENSAJE_DATOS_PERSONALES,
    MENSAJE_ESPACIOS,
    MENSAJE_LONGITUD_MAXIMA,
    MENSAJE_LONGITUD_MINIMA,
)
from app.db.session import SessionLocal, init_db
from app.exceptions.errors import AdminPasswordError
from app.models.password_reset_token import PasswordResetToken
from app.repositories.usuario import UsuarioRepository
from tests.helpers import auth, crear_admin, crear_usuario, login

PASSWORD_FUERTE = "ClaveSegura#2026"
PASSWORD_NUEVA = "NuevaClave#2026"


def _payload(password=PASSWORD_FUERTE, **overrides):
    datos = {
        "identificacion": "1234567890",
        "nombre": "Estudiante",
        "apellido": "Prueba",
        "correo": "policy@test.com",
        "password": password,
        "rol": "ESTUDIANTE",
    }
    datos.update(overrides)
    return datos


def _crear_token_reset(correo, token="token-reset-1"):
    with SessionLocal() as db:
        usuario = UsuarioRepository(db).find_by_correo_and_estado_true(correo)
        assert usuario is not None
        db.add(
            PasswordResetToken(
                token=token,
                usuario_id=usuario.id,
                fecha_expiracion=datetime.now() + timedelta(minutes=30),
                utilizado=False,
            )
        )
        db.commit()
    return token


@pytest.mark.parametrize(
    "password,mensaje",
    [
        ("Ab1!xyz", MENSAJE_LONGITUD_MINIMA),
        ("A1!" + "a" * 70, MENSAJE_LONGITUD_MAXIMA),
        ("Clave Segura#2026", MENSAJE_ESPACIOS),
        ("clavesegura#2026", MENSAJE_COMPOSICION),
        ("CLAVESEGURA#2026", MENSAJE_COMPOSICION),
        ("ClaveSegura#", MENSAJE_COMPOSICION),
        ("ClaveSegura2026", MENSAJE_COMPOSICION),
        ("Password1!", MENSAJE_COMUN),
    ],
)
def test_registro_rechaza_password_debil(client, password, mensaje):
    resp = client.post("/auth/register", json=_payload(password))

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["password"] == mensaje


@pytest.mark.parametrize(
    "campo,valor,password",
    [
        ("correo", "persona@test.com", "Persona#2026"),
        ("nombre", "Persona", "Persona#2026"),
        ("apellido", "Apellido", "Apellido#2026"),
        ("identificacion", "9876543210", "A9876543210#x"),
    ],
)
def test_registro_rechaza_datos_personales(client, campo, valor, password):
    resp = client.post("/auth/register", json=_payload(password, **{campo: valor}))

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["password"] == MENSAJE_DATOS_PERSONALES


def test_terminos_de_menos_de_cuatro_caracteres_no_se_comprueban(client):
    resp = client.post("/auth/register", json=_payload("Ana#2026Segura", nombre="Ana"))

    assert resp.status_code == 201, resp.text


def test_password_primero_en_el_json_tambien_valida_datos_personales(client):
    resp = client.post(
        "/auth/register",
        json={
            "password": "Correo#2026",
            "rol": "ESTUDIANTE",
            "correo": "correo@test.com",
            "identificacion": "1111111111",
            "nombre": "Estudiante",
            "apellido": "Prueba",
        },
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["password"] == MENSAJE_DATOS_PERSONALES


def test_registro_password_fuerte_guarda_bcrypt_y_no_expone(client, caplog):
    with caplog.at_level("DEBUG"):
        resp = client.post("/auth/register", json=_payload())

    assert resp.status_code == 201, resp.text
    assert PASSWORD_FUERTE not in resp.text
    assert PASSWORD_FUERTE not in caplog.text

    with SessionLocal() as db:
        usuario = UsuarioRepository(db).find_by_correo_and_estado_true(
            "policy@test.com"
        )
        assert usuario is not None
        assert usuario.password.startswith("$2b$12$")
        assert usuario.password != PASSWORD_FUERTE

    login(client, "policy@test.com", PASSWORD_FUERTE)


def test_admin_crea_usuario_con_password_debil(client):
    admin = crear_admin(client)

    resp = client.post(
        "/usuarios",
        json=_payload("debil"),
        headers=auth(admin["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["password"] == MENSAJE_LONGITUD_MINIMA


def test_admin_crea_usuario_con_password_fuerte(client):
    admin = crear_admin(client)
    payload = _payload(
        PASSWORD_FUERTE,
        correo="creado@test.com",
        identificacion="2222222222",
    )

    resp = client.post("/usuarios", json=payload, headers=auth(admin["token"]))

    assert resp.status_code == 201, resp.text
    login(client, "creado@test.com", PASSWORD_FUERTE)


def test_cambiar_password_exito(client):
    usuario = crear_usuario(client, correo="cambio@test.com")

    resp = client.post(
        "/auth/cambiar-password",
        json={
            "passwordActual": PASSWORD_FUERTE,
            "nuevaPassword": PASSWORD_NUEVA,
        },
        headers=auth(usuario["token"]),
    )

    assert resp.status_code == 200, resp.text
    assert resp.json() == "Contraseña actualizada correctamente."
    login(client, "cambio@test.com", PASSWORD_NUEVA)


def test_cambiar_password_actual_incorrecta(client):
    usuario = crear_usuario(client, correo="malactual@test.com")

    resp = client.post(
        "/auth/cambiar-password",
        json={
            "passwordActual": "NoEsLaClave#1",
            "nuevaPassword": PASSWORD_NUEVA,
        },
        headers=auth(usuario["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["message"] == "La contraseña actual es incorrecta."
    assert resp.json()["errors"] is None


def test_cambiar_password_nueva_debil(client):
    usuario = crear_usuario(client, correo="nuevadebil@test.com")

    resp = client.post(
        "/auth/cambiar-password",
        json={"passwordActual": PASSWORD_FUERTE, "nuevaPassword": "debil"},
        headers=auth(usuario["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["nuevaPassword"] == MENSAJE_LONGITUD_MINIMA


def test_cambiar_password_igual_a_la_actual(client):
    usuario = crear_usuario(client, correo="igual@test.com")

    resp = client.post(
        "/auth/cambiar-password",
        json={
            "passwordActual": PASSWORD_FUERTE,
            "nuevaPassword": PASSWORD_FUERTE,
        },
        headers=auth(usuario["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert (
        resp.json()["message"]
        == "La nueva contraseña debe ser diferente a la actual."
    )
    assert (
        resp.json()["errors"]["nuevaPassword"]
        == "La nueva contraseña debe ser diferente a la actual."
    )


def test_cambiar_password_usa_datos_reales_del_usuario(client):
    usuario = crear_usuario(client, correo="real@test.com")

    resp = client.post(
        "/auth/cambiar-password",
        json={
            "passwordActual": PASSWORD_FUERTE,
            "nuevaPassword": "Real#2026Clave",
        },
        headers=auth(usuario["token"]),
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["nuevaPassword"] == MENSAJE_DATOS_PERSONALES


def test_cambiar_password_sin_token(client):
    resp = client.post(
        "/auth/cambiar-password",
        json={
            "passwordActual": PASSWORD_FUERTE,
            "nuevaPassword": PASSWORD_NUEVA,
        },
    )

    assert resp.status_code == 401


def test_reset_password_rechaza_nueva_debil(client):
    resp = client.post(
        "/auth/reset-password",
        json={"token": "token-invalido", "nuevaPassword": "debil"},
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["nuevaPassword"] == MENSAJE_LONGITUD_MINIMA


def test_reset_password_rechaza_datos_reales_del_usuario(client):
    crear_usuario(client, correo="reset@test.com")
    token = _crear_token_reset("reset@test.com")

    resp = client.post(
        "/auth/reset-password",
        json={"token": token, "nuevaPassword": "Apellido#2026"},
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["errors"]["nuevaPassword"] == MENSAJE_DATOS_PERSONALES


def test_reset_password_exitoso(client):
    crear_usuario(client, correo="reset-ok@test.com")
    token = _crear_token_reset("reset-ok@test.com", token="token-reset-ok")

    resp = client.post(
        "/auth/reset-password",
        json={"token": token, "nuevaPassword": PASSWORD_NUEVA},
    )

    assert resp.status_code == 200, resp.text
    login(client, "reset-ok@test.com", PASSWORD_NUEVA)

    segundo_uso = client.post(
        "/auth/reset-password",
        json={"token": token, "nuevaPassword": "OtraClave#2026"},
    )
    assert segundo_uso.status_code == 400
    assert segundo_uso.json()["message"] == "El token no es válido."


def test_arranque_falla_si_no_hay_admin_y_password_debil(monkeypatch):
    monkeypatch.setattr(settings, "admin_password", "debil")

    with pytest.raises(AdminPasswordError) as error:
        init_db()

    assert "ADMIN_PASSWORD" in str(error.value)
    assert "debil" not in str(error.value)


def test_arranque_avisa_si_admin_existe_y_password_debil(
    client, monkeypatch, caplog
):
    crear_admin(client)
    monkeypatch.setattr(settings, "admin_password", "debil")

    with caplog.at_level("WARNING"):
        init_db()

    assert "administrador ya existe" in caplog.text
    assert "debil" not in caplog.text
