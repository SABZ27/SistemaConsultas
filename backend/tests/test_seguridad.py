"""Pruebas del Bloque C: límites, tokens, JWT, CORS y cabeceras."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import (
    JWT_SECRET_EJEMPLO,
    origenes_cors,
    settings,
    validar_jwt_secret,
)
from app.core.rate_limit import (
    LIMITE_LOGIN_IP,
    LIMITE_LOGIN_PAR,
    MENSAJE_DEMASIADAS_SOLICITUDES,
    MENSAJE_DEMASIADOS_INTENTOS,
    RateLimiter,
    obtener_ip,
)
from app.core.security import hash_token
from app.db.session import SessionLocal
from app.main import app, crear_app
from app.models.password_reset_token import PasswordResetToken
from tests.helpers import crear_usuario, login

PASSWORD = "ClaveSegura#2026"


def _login_falla(client, correo, ip=None, password="incorrecta"):
    headers = {"X-Forwarded-For": ip} if ip is not None else {}
    return client.post(
        "/auth/login",
        json={"correo": correo, "password": password},
        headers=headers,
    )


def _login_ok(client, correo, ip):
    return client.post(
        "/auth/login",
        json={"correo": correo, "password": PASSWORD},
        headers={"X-Forwarded-For": ip},
    )


# ---------------------------------------------------------------------------
# Dirección IP del cliente
# ---------------------------------------------------------------------------


def test_obtener_ip_usa_la_ultima_entrada_de_x_forwarded_for():
    peticion = SimpleNamespace(
        headers={"x-forwarded-for": "203.0.113.1, 198.51.100.9"},
        client=SimpleNamespace(host="192.0.2.10"),
    )

    assert obtener_ip(peticion) == "198.51.100.9"


def test_obtener_ip_usa_conexion_directa_sin_encabezado():
    peticion = SimpleNamespace(
        headers={},
        client=SimpleNamespace(host="192.0.2.10"),
    )

    assert obtener_ip(peticion) == "192.0.2.10"


def test_dos_ips_se_limitan_por_separado(client):
    crear_usuario(client, correo="ip@test.com")

    for _ in range(5):
        assert _login_falla(client, "ip@test.com", "198.51.100.1").status_code == 401

    bloqueada = _login_falla(client, "ip@test.com", "198.51.100.1")
    assert bloqueada.status_code == 429
    assert bloqueada.json()["message"] == MENSAJE_DEMASIADOS_INTENTOS
    assert int(bloqueada.headers["Retry-After"]) > 0

    otra_ip = _login_falla(client, "ip@test.com", "198.51.100.2")
    assert otra_ip.status_code == 401


def test_primera_entrada_falsificada_no_cambia_la_clave(client):
    for _ in range(5):
        assert (
            _login_falla(
                client,
                "spoof@test.com",
                "203.0.113.50, 198.51.100.7",
            ).status_code
            == 401
        )

    # Cambia la primera entrada (falsificable), pero la última IP es la misma.
    resp = _login_falla(client, "spoof@test.com", "192.0.2.99, 198.51.100.7")
    assert resp.status_code == 429


# ---------------------------------------------------------------------------
# Límites de login
# ---------------------------------------------------------------------------


def test_login_correcto_limpia_solo_la_pareja_correo_ip(client):
    crear_usuario(client, correo="pareja@test.com")
    ip = "198.51.100.50"

    for _ in range(4):
        assert _login_falla(client, "pareja@test.com", ip).status_code == 401

    assert LIMITE_LOGIN_PAR.claves_actuales == 1
    assert LIMITE_LOGIN_IP.claves_actuales == 1

    assert _login_ok(client, "pareja@test.com", ip).status_code == 200

    assert LIMITE_LOGIN_PAR.claves_actuales == 0
    assert LIMITE_LOGIN_IP.claves_actuales == 1

    # El contador de la IP sigue vivo: 15 fallos de otros correos + 1 más
    # alcanzan el máximo de 20 aunque la pareja se haya limpiado.
    for i in range(15):
        assert _login_falla(client, f"otro{i}@test.com", ip).status_code == 401

    assert _login_falla(client, "pareja@test.com", ip).status_code == 401
    assert _login_ok(client, "pareja@test.com", ip).status_code == 429


def test_limite_por_correo_frena_ataques_distribuidos(client):
    correo = "distribuido@test.com"

    for i in range(15):
        assert _login_falla(client, correo, f"198.51.100.{i + 10}").status_code == 401

    # Una IP nueva no evita el límite solo-correo.
    resp = _login_falla(client, correo, "203.0.113.200")
    assert resp.status_code == 429
    assert resp.json()["message"] == MENSAJE_DEMASIADOS_INTENTOS


# ---------------------------------------------------------------------------
# Limitador: purga, tope y bloqueo
# ---------------------------------------------------------------------------


def test_limitador_purga_entradas_vencidas():
    ahora = [0.0]
    limitador = RateLimiter(
        maximo=10,
        ventana_segundos=10,
        max_claves=3,
        reloj=lambda: ahora[0],
    )

    for clave in ("a", "b", "c"):
        assert limitador.permitir(clave).permitido

    ahora[0] = 11
    assert limitador.permitir("d").permitido
    assert limitador.claves_actuales == 1


def test_limitador_respeta_el_tope_de_claves():
    ahora = [0.0]
    limitador = RateLimiter(
        maximo=10,
        ventana_segundos=100,
        max_claves=3,
        reloj=lambda: ahora[0],
    )

    for clave in ("a", "b", "c"):
        assert limitador.permitir(clave).permitido

    assert limitador.permitir("d").permitido
    assert limitador.claves_actuales == 3

    assert limitador.permitir("e").permitido
    assert limitador.claves_actuales == 3


def test_limitador_aplica_bloqueo_temporal():
    ahora = [0.0]
    limitador = RateLimiter(
        maximo=2,
        ventana_segundos=60,
        bloqueo_segundos=30,
        reloj=lambda: ahora[0],
    )

    limitador.registrar_fallo("x")
    limitador.registrar_fallo("x")

    assert limitador.esta_bloqueado("x").permitido is False

    ahora[0] = 29
    assert limitador.esta_bloqueado("x").permitido is False

    ahora[0] = 31
    assert limitador.esta_bloqueado("x").permitido is True


# ---------------------------------------------------------------------------
# Recuperación de contraseña
# ---------------------------------------------------------------------------


def test_forgot_password_responde_429_al_superar_el_limite(client):
    for _ in range(3):
        resp = client.post(
            "/auth/forgot-password", json={"correo": "limite@test.com"}
        )
        assert resp.status_code == 200

    resp = client.post("/auth/forgot-password", json={"correo": "limite@test.com"})
    assert resp.status_code == 429
    assert resp.json()["message"] == MENSAJE_DEMASIADAS_SOLICITUDES
    assert resp.json()["error"] == "Too Many Requests"
    assert int(resp.headers["Retry-After"]) > 0


def test_forgot_password_guarda_solo_el_hash_y_permite_un_uso(
    client, servicios_externos
):
    crear_usuario(client, correo="hash@test.com")

    resp = client.post("/auth/forgot-password", json={"correo": "hash@test.com"})
    assert resp.status_code == 200

    contenido = servicios_externos["correos"][-1]["contenido"]
    token_plano = (
        contenido.split("restablecerla:\n\n", 1)[1].split("\n\n", 1)[0].strip()
    )

    with SessionLocal() as db:
        guardado = db.query(PasswordResetToken).one()
        assert guardado.token == hash_token(token_plano)
        assert guardado.token != token_plano
        assert len(guardado.token) == 64

    assert client.post(
        "/auth/reset-password",
        json={"token": token_plano, "nuevaPassword": "NuevaClave#2026"},
    ).status_code == 200

    segundo = client.post(
        "/auth/reset-password",
        json={"token": token_plano, "nuevaPassword": "OtraClave#2026"},
    )
    assert segundo.status_code == 400
    assert segundo.json()["message"] == "El token no es válido."


def test_reset_password_rechaza_token_expirado(client):
    crear_usuario(client, correo="expirado@test.com")

    with SessionLocal() as db:
        from app.repositories.usuario import UsuarioRepository

        usuario = UsuarioRepository(db).find_by_correo_and_estado_true(
            "expirado@test.com"
        )
        db.add(
            PasswordResetToken(
                token=hash_token("token-expirado"),
                usuario_id=usuario.id,
                fecha_expiracion=datetime.now() - timedelta(minutes=1),
                utilizado=False,
            )
        )
        db.commit()

    resp = client.post(
        "/auth/reset-password",
        json={"token": "token-expirado", "nuevaPassword": "NuevaClave#2026"},
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "El token ha expirado."


# ---------------------------------------------------------------------------
# JWT endurecido
# ---------------------------------------------------------------------------


def _token(**cambios):
    payload = {
        "sub": "usuario@test.com",
        "uid": 1,
        "rol": "ESTUDIANTE",
        "modulos": [],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    payload.update(cambios)
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def test_jwt_sin_exp_es_rechazado(client):
    payload = {
        "sub": "usuario@test.com",
        "uid": 1,
        "rol": "ESTUDIANTE",
        "modulos": [],
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_jwt_de_servicio_no_sirve_para_usuarios(client):
    token = _token(rol="SERVICIO")

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_jwt_con_uid_cero_es_rechazado(client):
    token = _token(uid=0, rol="ADMINISTRADOR")

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Configuración de arranque, CORS y cabeceras
# ---------------------------------------------------------------------------


def test_arranque_rechaza_jwt_secret_corto_o_de_ejemplo(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "corto")
    with pytest.raises(RuntimeError, match="32"):
        crear_app()

    monkeypatch.setattr(settings, "jwt_secret", JWT_SECRET_EJEMPLO)
    with pytest.raises(RuntimeError, match="ejemplo"):
        crear_app()


def test_origenes_cors_rechaza_comodin_y_lista_vacia():
    with pytest.raises(RuntimeError, match="al menos un origen"):
        origenes_cors("")

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        origenes_cors("http://localhost:5173,*")


def test_arranque_rechaza_cors_con_comodin(monkeypatch):
    monkeypatch.setattr(settings, "cors_origins", "*")
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        crear_app()


def test_cors_solo_permite_origenes_configurados(client):
    permitido = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert permitido.headers.get("access-control-allow-origin") == (
        "http://localhost:5173"
    )

    rechazado = client.options(
        "/auth/login",
        headers={
            "Origin": "http://malicioso.test",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert rechazado.headers.get("access-control-allow-origin") is None


def test_cabeceras_de_seguridad_y_hsts(client):
    sin_hsts = client.get("/auth/me")
    assert sin_hsts.headers["X-Content-Type-Options"] == "nosniff"
    assert sin_hsts.headers["X-Frame-Options"] == "DENY"
    assert sin_hsts.headers["Referrer-Policy"] == "no-referrer"
    assert "Strict-Transport-Security" not in sin_hsts.headers

    con_hsts = client.get("/auth/me", headers={"X-Forwarded-Proto": "https"})
    assert con_hsts.headers["Strict-Transport-Security"].startswith("max-age=")


def test_cuerpo_demasiado_grande_responde_413(client):
    cuerpo = '{"correo":"a@b.com","password":"' + ("x" * (1024 * 1024)) + '"}'

    resp = client.post(
        "/auth/login",
        content=cuerpo,
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 413
    assert resp.json()["message"] == "El cuerpo de la solicitud es demasiado grande."
    assert resp.json()["error"] == "Payload Too Large"


def test_error_500_no_filtra_datos_sensibles(client, monkeypatch, caplog):
    from app.services.auth import AuthService

    def _fallar(self, req, ip="desconocida"):
        raise RuntimeError("correo@secreto.test token-super-secreto")

    monkeypatch.setattr(AuthService, "login", _fallar)

    with TestClient(app, raise_server_exceptions=False) as cliente:
        with caplog.at_level("ERROR"):
            resp = cliente.post(
                "/auth/login",
                json={"correo": "a@b.com", "password": "x"},
            )

    assert resp.status_code == 500
    assert resp.json()["message"] == "Error interno del servidor."
    assert "correo@secreto.test" not in caplog.text
    assert "token-super-secreto" not in caplog.text


def test_login_correcto_sigue_funcionando(client):
    crear_usuario(client, correo="normal@test.com")

    assert login(client, "normal@test.com")["token"]
