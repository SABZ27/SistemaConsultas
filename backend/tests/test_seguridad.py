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
    LOGIN_IP_MAX_FALLOS,
    MAX_CLAVES_LIMITADOR,
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
IP_EDGE = "172.64.0.1"


def _xff(cliente):
    """Cadena observada detrás de Cloudflare + Render."""
    return f"{cliente}, {IP_EDGE}"


def _login_falla(client, correo, xff=None, password="incorrecta"):
    headers = {"X-Forwarded-For": xff} if xff is not None else {}
    return client.post(
        "/auth/login",
        json={"correo": correo, "password": password},
        headers=headers,
    )


def _login_ok(client, correo, xff):
    return client.post(
        "/auth/login",
        json={"correo": correo, "password": PASSWORD},
        headers={"X-Forwarded-For": xff},
    )


# ---------------------------------------------------------------------------
# Dirección IP del cliente
# ---------------------------------------------------------------------------


def test_obtener_ip_con_hops_1_usa_el_cliente_no_el_edge(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    peticion = SimpleNamespace(
        headers={"x-forwarded-for": f"203.0.113.10, {IP_EDGE}"},
        client=SimpleNamespace(host="192.0.2.10"),
    )

    assert obtener_ip(peticion) == "203.0.113.10"


def test_obtener_ip_cae_a_client_host_si_faltan_entradas_o_es_invalida(
    monkeypatch,
):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    base = {
        "client": SimpleNamespace(host="192.0.2.10"),
    }

    sin_encabezado = SimpleNamespace(headers={}, **base)
    assert obtener_ip(sin_encabezado) == "192.0.2.10"

    # Con hops=1 hacen falta al menos 2 entradas.
    pocas = SimpleNamespace(headers={"x-forwarded-for": "203.0.113.10"}, **base)
    assert obtener_ip(pocas) == "192.0.2.10"

    invalida = SimpleNamespace(
        headers={"x-forwarded-for": f"no-es-ip, {IP_EDGE}"},
        **base,
    )
    assert obtener_ip(invalida) == "192.0.2.10"


def test_cadena_parcialmente_malformada_cae_a_client_host(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    base = {"client": SimpleNamespace(host="192.0.2.10")}

    # La inválida está en la última entrada (el edge), NO en la candidata:
    # antes se devolvía 203.0.113.10; ahora la cadena completa se invalida.
    edge_invalido = SimpleNamespace(
        headers={"x-forwarded-for": "203.0.113.10, no-es-ip"}, **base
    )
    assert obtener_ip(edge_invalido) == "192.0.2.10"

    entrada_vacia = SimpleNamespace(
        headers={"x-forwarded-for": f"203.0.113.10, , {IP_EDGE}"}, **base
    )
    assert obtener_ip(entrada_vacia) == "192.0.2.10"

    coma_final = SimpleNamespace(
        headers={"x-forwarded-for": f"203.0.113.10, {IP_EDGE},"}, **base
    )
    assert obtener_ip(coma_final) == "192.0.2.10"


def test_menos_entradas_que_hops_mas_uno_cae_a_client_host(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 2)
    peticion = SimpleNamespace(
        headers={"x-forwarded-for": f"203.0.113.10, {IP_EDGE}"},
        client=SimpleNamespace(host="192.0.2.10"),
    )
    # Con hops=2 hacen falta 3 entradas; solo hay 2.
    assert obtener_ip(peticion) == "192.0.2.10"


def test_diagnostico_ip_solo_registra_conteos(monkeypatch, caplog):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    monkeypatch.setattr(settings, "diagnostico_ip", True)
    peticion = SimpleNamespace(
        headers={
            "x-forwarded-for": f"203.0.113.10, {IP_EDGE}",
            "true-client-ip": "203.0.113.10",
        },
        client=SimpleNamespace(host="192.0.2.10"),
    )

    with caplog.at_level("INFO", logger="sistema_consultas.ip"):
        assert obtener_ip(peticion) == "203.0.113.10"

    assert "x_forwarded_for_entradas=2" in caplog.text
    assert "true_client_ip=True" in caplog.text
    assert "203.0.113.10" not in caplog.text
    assert IP_EDGE not in caplog.text


def test_dos_ips_se_limitan_por_separado(client, monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    crear_usuario(client, correo="ip@test.com")
    xff = _xff("198.51.100.1")

    for _ in range(5):
        assert _login_falla(client, "ip@test.com", xff).status_code == 401

    bloqueada = _login_falla(client, "ip@test.com", xff)
    assert bloqueada.status_code == 429
    assert bloqueada.json()["message"] == MENSAJE_DEMASIADOS_INTENTOS
    assert int(bloqueada.headers["Retry-After"]) > 0

    otra_ip = _login_falla(client, "ip@test.com", _xff("198.51.100.2"))
    assert otra_ip.status_code == 401


def test_entradas_falsificadas_antepuestas_no_cambian_la_clave(client, monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)

    for _ in range(5):
        assert (
            _login_falla(
                client,
                "spoof@test.com",
                f"203.0.113.50, {_xff('198.51.100.7')}",
            ).status_code
            == 401
        )

    # Cambia la entrada falsificable de la izquierda; el cliente real y el
    # edge de la derecha siguen siendo los mismos.
    resp = _login_falla(
        client, "spoof@test.com", f"192.0.2.99, {_xff('198.51.100.7')}"
    )
    assert resp.status_code == 429


# ---------------------------------------------------------------------------
# Límites de login
# ---------------------------------------------------------------------------


def test_login_correcto_limpia_solo_la_pareja_correo_ip(client, monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    crear_usuario(client, correo="pareja@test.com")
    xff = _xff("198.51.100.50")

    for _ in range(4):
        assert _login_falla(client, "pareja@test.com", xff).status_code == 401

    assert LIMITE_LOGIN_PAR.claves_actuales == 1
    assert LIMITE_LOGIN_IP.claves_actuales == 1

    assert _login_ok(client, "pareja@test.com", xff).status_code == 200

    assert LIMITE_LOGIN_PAR.claves_actuales == 0
    assert LIMITE_LOGIN_IP.claves_actuales == 1

    # El contador de la IP sigue vivo tras el login correcto (solo se limpia
    # la pareja): 4 fallos iniciales + 95 fallos de otros correos + 1 fallo
    # final = 100 = LOGIN_IP_MAX_FALLOS. Ese último fallo dispara el bloqueo
    # de la IP, por eso el login correcto posterior recibe 429.
    for i in range(95):
        assert _login_falla(client, f"otro{i}@test.com", xff).status_code == 401

    assert _login_falla(client, "pareja@test.com", xff).status_code == 401
    assert _login_ok(client, "pareja@test.com", xff).status_code == 429


def test_limite_por_ip_de_login_es_100(client, monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    assert LOGIN_IP_MAX_FALLOS == 100
    xff = _xff("198.51.100.1")

    # Correos distintos: no se disparan los límites por pareja (5) ni por
    # correo (15), solo se acumula la IP.
    for i in range(100):
        assert (
            _login_falla(client, f"ip100-{i}@test.com", xff).status_code == 401
        )

    # El fallo 100 agotó la IP; cualquier intento posterior queda bloqueado.
    assert _login_falla(client, "ip100-extra@test.com", xff).status_code == 429


def test_limite_por_correo_frena_ataques_distribuidos(client, monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    correo = "distribuido@test.com"

    for i in range(15):
        assert (
            _login_falla(
                client, correo, _xff(f"198.51.100.{i + 10}")
            ).status_code
            == 401
        )

    # Una IP nueva no evita el límite solo-correo.
    resp = _login_falla(client, correo, _xff("203.0.113.200"))
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


def test_tope_10000_purga_vencidos_y_luego_evita_las_mas_antiguas():
    ahora = [0.0]
    limitador = RateLimiter(
        maximo=1,
        ventana_segundos=100,
        max_claves=MAX_CLAVES_LIMITADOR,
        reloj=lambda: ahora[0],
    )

    for i in range(MAX_CLAVES_LIMITADOR):
        assert limitador.permitir(f"clave-{i}").permitido

    # Al llenarse, la clave más antigua se elimina para dejar entrar la nueva.
    assert limitador.permitir("nueva").permitido
    assert limitador.claves_actuales == MAX_CLAVES_LIMITADOR
    assert limitador.permitir("nueva").permitido is False

    # "clave-0" era la más antigua: al ser desalojada vuelve a tener cupo.
    assert limitador.permitir("clave-0").permitido is True
    assert limitador.permitir("clave-0").permitido is False

    # Pasada la ventana, la purga elimina las vencidas antes de desalojar.
    ahora[0] = 101
    assert limitador.permitir("tras-expirar").permitido
    assert limitador.claves_actuales == 1


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


def _superar_limite_forgot(client, correo):
    for _ in range(3):
        assert (
            client.post(
                "/auth/forgot-password", json={"correo": correo}
            ).status_code
            == 200
        )
    return client.post("/auth/forgot-password", json={"correo": correo})


def test_forgot_password_inexistente_responde_429_al_superar_el_limite(client):
    resp = _superar_limite_forgot(client, "no-existe@test.com")

    assert resp.status_code == 429
    assert resp.json()["message"] == MENSAJE_DEMASIADAS_SOLICITUDES
    assert resp.json()["error"] == "Too Many Requests"
    assert int(resp.headers["Retry-After"]) > 0


def test_forgot_password_existente_responde_429_al_superar_el_limite(client):
    crear_usuario(client, correo="existe@test.com")

    resp = _superar_limite_forgot(client, "existe@test.com")

    assert resp.status_code == 429
    assert resp.json()["message"] == MENSAJE_DEMASIADAS_SOLICITUDES
    assert resp.json()["error"] == "Too Many Requests"
    assert int(resp.headers["Retry-After"]) > 0


def test_forgot_password_encola_el_correo_en_segundo_plano(
    client, monkeypatch, servicios_externos
):
    from starlette.background import BackgroundTasks

    crear_usuario(client, correo="segundo-plano@test.com")
    tareas = []

    def _capturar(self, func, *args, **kwargs):
        tareas.append((func, args, kwargs))

    monkeypatch.setattr(BackgroundTasks, "add_task", _capturar)

    resp = client.post(
        "/auth/forgot-password", json={"correo": "segundo-plano@test.com"}
    )

    assert resp.status_code == 200
    assert len(tareas) == 1
    assert tareas[0][0].__name__ == "enviar"
    # Nada se envió de forma síncrona antes de devolver la respuesta.
    assert servicios_externos["correos"] == []


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


def test_cuerpo_demasiado_grande_chunked_sin_content_length(client):
    def _trozos():
        yield b'{"correo":"a@b.com","password":"'
        for _ in range(1025):
            yield b"x" * 1024
        yield b'"}'

    resp = client.post(
        "/auth/login",
        content=_trozos(),
        headers={"Content-Type": "application/json"},
    )

    assert "content-length" not in {clave.lower() for clave in resp.request.headers}
    assert resp.status_code == 413
    assert resp.json()["message"] == "El cuerpo de la solicitud es demasiado grande."


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
