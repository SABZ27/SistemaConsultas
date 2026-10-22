"""Sondas de seguridad (Paso F) contra los servicios en ejecución.

Requiere FastAPI (http://127.0.0.1:8080) y Express (http://127.0.0.1:3001)
arriba, y las variables ADMIN_CORREO, ADMIN_PASSWORD y JWT_SECRET
(este último para poder forjar/expirar tokens).

La infraestructura física (sedes, zonas, recursos) se consulta en FastAPI; el
servicio Express expone los servicios externos (festivos, correos).

Uso:
  python scripts/seguridad.py

No se ejecuta automáticamente. Si crea datos, pide confirmación explícita por
consola. Las contraseñas se leen por variable de entorno o por entrada oculta,
nunca por argumento ni guardadas en archivos.
"""

from __future__ import annotations

import datetime as dt
import os
import random
import sys
from datetime import date, timedelta

import httpx
import jwt

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://127.0.0.1:8080").rstrip("/")
INFRA_URL = os.environ.get("INFRA_URL", "http://127.0.0.1:3001").rstrip("/")
ADMIN_CORREO = os.environ.get("ADMIN_CORREO", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")

PASSWORD = os.environ.get("TEST_PASSWORD", "contrasenia123")
TIMEOUT = 20.0

_resultados: list[tuple[str, bool, str]] = []


def check(nombre: str, cond: bool, detalle: str = "") -> None:
    _resultados.append((nombre, bool(cond), detalle))
    print(f"[{'OK ' if cond else 'FALLA'}] {nombre}" + (f" -> {detalle}" if detalle else ""))


def hdr(token=None):
    return {"Authorization": f"Bearer {token}"} if token else {}


def _nar() -> str:
    return str(random.randint(100000, 999999)) + str(random.randint(1000, 9999))


def _pedir_confirmacion() -> bool:
    try:
        resp = input("Este script puede crear datos de prueba. ¿Deseas continuar? (escribe SI para confirmar): ")
    except Exception:
        return False
    return resp.strip().upper() == "SI"


def _obtener_password() -> str:
    if ADMIN_PASSWORD:
        return ADMIN_PASSWORD
    try:
        import getpass

        return getpass.getpass("Contraseña de administrador (entrada oculta): ")
    except Exception:
        return ""


def login(client, correo, password):
    return client.post(f"{FASTAPI_URL}/auth/login", json={"correo": correo, "password": password})


def register(client, correo, identificacion, rol):
    return client.post(
        f"{FASTAPI_URL}/auth/register",
        json={
            "identificacion": identificacion,
            "nombre": "Nombre",
            "apellido": "Prueba",
            "correo": correo,
            "password": PASSWORD,
            "rol": rol,
        },
    )


def main() -> int:
    if not ADMIN_CORREO or not JWT_SECRET:
        print("Faltan ADMIN_CORREO/JWT_SECRET en el entorno.")
        return 2
    if not _pedir_confirmacion():
        print("Cancelado por el usuario.")
        return 2
    admin_password = _obtener_password()
    if not admin_password:
        print("Falta contraseña (ADMIN_PASSWORD o entrada oculta).")
        return 2

    fecha = date.today() + timedelta(days=1)
    marca = fecha.strftime("%H%M%S") + str(random.randint(100, 999))

    with httpx.Client(timeout=TIMEOUT) as client:
        admin = login(client, ADMIN_CORREO, admin_password).json()
        admin_id = admin["id_usuario"]
        admin_token = admin["token"]

        # --- preparación de datos ---
        mod = client.post(
            f"{FASTAPI_URL}/modulos",
            json={"nombre": f"Módulo seg {marca}", "descripcion": "Módulo de pruebas de seguridad"},
            headers=hdr(admin_token),
        ).json()
        register(client, f"docente.seg.{marca}@test.com", _nar(), "DOCENTE")
        docente = login(client, f"docente.seg.{marca}@test.com", PASSWORD).json()
        register(client, f"duena.seg.{marca}@test.com", _nar(), "ESTUDIANTE")
        duena = login(client, f"duena.seg.{marca}@test.com", PASSWORD).json()
        register(client, f"ajena.seg.{marca}@test.com", _nar(), "ESTUDIANTE")
        ajena = login(client, f"ajena.seg.{marca}@test.com", PASSWORD).json()
        register(client, f"inactiva.seg.{marca}@test.com", _nar(), "ESTUDIANTE")
        inactiva = login(client, f"inactiva.seg.{marca}@test.com", PASSWORD).json()

        client.post(
            f"{FASTAPI_URL}/docentes-modulos",
            json={"docenteId": docente["id_usuario"], "moduloId": mod["id"]},
            headers=hdr(admin_token),
        )
        client.post(
            f"{FASTAPI_URL}/disponibilidad-docente",
            json={
                "docenteId": docente["id_usuario"],
                "diaSemana": fecha.isoweekday(),
                "horaInicio": "00:00",
                "horaFin": "23:59",
            },
            headers=hdr(admin_token),
        )
        solicitud = client.post(
            f"{FASTAPI_URL}/solicitudes-consultas",
            json={
                "prioridad": "MEDIA",
                "asunto": "Consulta seg",
                "descripcion": "Solicitud para pruebas de seguridad",
                "fechaConsulta": fecha.isoformat(),
                "horaConsulta": "06:30",
                "docenteId": docente["id_usuario"],
                "moduloId": mod["id"],
            },
            headers=hdr(duena["token"]),
        ).json()
        sid = solicitud["id"]

        sede = client.post(
            f"{FASTAPI_URL}/sedes",
            json={"nombre": f"Sede seg {marca}", "tipoEstructura": "SALONES"},
            headers=hdr(admin_token),
        ).json()
        recurso = client.post(
            f"{FASTAPI_URL}/recursos-fisicos",
            json={"sedeId": sede["id"], "nombre": f"Salón seg {marca}", "tipo": "SALON"},
            headers=hdr(admin_token),
        ).json()

        # --- F1: registro con rol ADMINISTRADOR -> rechazado ---
        r = register(client, f"adminfalso.{marca}@test.com", _nar(), "ADMINISTRADOR")
        check("F1 registro con rol ADMINISTRADOR rechazado", r.status_code == 403, f"{r.status_code}")

        # --- F2: estudiante POST /programas -> 403 ---
        r = client.post(f"{FASTAPI_URL}/programas", json={"nombre": f"P seg {marca}"}, headers=hdr(duena["token"]))
        check("F2 estudiante POST /programas -> 403", r.status_code == 403, f"{r.status_code}")

        # --- F3: estudiante DELETE /usuarios/{admin} -> 403 ---
        r = client.delete(f"{FASTAPI_URL}/usuarios/{admin_id}", headers=hdr(duena["token"]))
        check("F3 estudiante DELETE /usuarios/{admin} -> 403", r.status_code == 403, f"{r.status_code}")

        # --- F4: rutas sin token -> 401 ---
        sin_token = [
            ("GET /solicitudes-consultas", client.get(f"{FASTAPI_URL}/solicitudes-consultas")),
            ("POST /programas", client.post(f"{FASTAPI_URL}/programas", json={"nombre": "x"})),
            ("POST /modulos", client.post(f"{FASTAPI_URL}/modulos", json={"nombre": "x", "descripcion": "1234567890"})),
            ("GET /usuarios", client.get(f"{FASTAPI_URL}/usuarios")),
            ("Express POST /correos", client.post(f"{INFRA_URL}/correos", json={"para": "a@b.com", "asunto": "x", "contenido": "y"})),
        ]
        for nombre, r in sin_token:
            check(f"F4 sin token -> 401: {nombre}", r.status_code == 401, f"{r.status_code}")

        # --- F5: usuario ajeno no puede leer/reasignar/asignar recurso ---
        r = client.get(f"{FASTAPI_URL}/solicitudes-consultas/{sid}", headers=hdr(ajena["token"]))
        check("F5a ajena no puede leer la solicitud -> 403", r.status_code == 403, f"{r.status_code}")

        r = client.patch(
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/docente",
            json={"docenteId": docente["id_usuario"]},
            headers=hdr(ajena["token"]),
        )
        check("F5b ajena no puede reasignar su docente -> 403", r.status_code == 403, f"{r.status_code}")

        r = client.patch(
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/recurso-fisico",
            json={"recursoFisicoId": recurso["id"]},
            headers=hdr(ajena["token"]),
        )
        check("F5c ajena no puede asignarle recurso -> 403", r.status_code == 403, f"{r.status_code}")

        # --- F6: estudiante no puede marcar EN_PROCESO ni RESUELTA ---
        r = client.patch(
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/estado",
            json={"estado": "EN_PROCESO"},
            headers=hdr(duena["token"]),
        )
        check("F6a estudiante no puede marcar EN_PROCESO -> 403", r.status_code == 403, f"{r.status_code}")

        r = client.patch(
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/estado",
            json={"estado": "RESUELTA"},
            headers=hdr(duena["token"]),
        )
        check("F6b estudiante no puede marcar RESUELTA -> 403", r.status_code == 403, f"{r.status_code}")

        # --- F7: token con firma alterada -> 401 en FastAPI y Express ---
        firma_alterada = admin_token[:-4] + ("aaaa" if admin_token[-4:] != "aaaa" else "bbbb")
        r = client.get(f"{FASTAPI_URL}/auth/me", headers=hdr(firma_alterada))
        check("F7a firma alterada -> 401 FastAPI", r.status_code == 401, f"{r.status_code}")
        r = client.get(f"{INFRA_URL}/servicios-externos", headers=hdr(firma_alterada))
        check("F7b firma alterada -> 401 Express", r.status_code == 401, f"{r.status_code}")

        # --- F8: token expirado -> 401 en ambos ---
        pasado = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)
        expirado = jwt.encode(
            {
                "sub": ADMIN_CORREO,
                "uid": admin_id,
                "rol": "ADMINISTRADOR",
                "modulos": ["INFRAESTRUCTURA"],
                "iat": pasado - dt.timedelta(hours=1),
                "exp": pasado,
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        r = client.get(f"{FASTAPI_URL}/auth/me", headers=hdr(expirado))
        check("F8a token expirado -> 401 FastAPI", r.status_code == 401, f"{r.status_code}")
        r = client.get(f"{INFRA_URL}/servicios-externos", headers=hdr(expirado))
        check("F8b token expirado -> 401 Express", r.status_code == 401, f"{r.status_code}")

        # --- F9: usuario desactivado no puede iniciar sesión ---
        r = client.delete(f"{FASTAPI_URL}/usuarios/{inactiva['id_usuario']}", headers=hdr(admin_token))
        check("F9a admin desactiva usuario -> 204", r.status_code == 204, f"{r.status_code}")
        r = login(client, f"inactiva.seg.{marca}@test.com", PASSWORD)
        check("F9b usuario desactivado no puede iniciar sesión -> 401", r.status_code == 401, f"{r.status_code}")

        # --- F10: el docente asignado puede asignar el recurso ---
        r = client.patch(
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/recurso-fisico",
            json={"recursoFisicoId": recurso["id"]},
            headers=hdr(docente["token"]),
        )
        ok = r.status_code == 200 and r.json().get("nombreRecursoFisico") == recurso.get("ubicacion")
        check("F10a docente asignado asigna recurso", ok, f"{r.status_code} ubicacion={r.json().get('nombreRecursoFisico') if r.status_code==200 else '-'!r}")

    return _resumen()


def _resumen() -> int:
    fallidas = [n for n, ok, _ in _resultados if not ok]
    print("\n=== RESUMEN SEGURIDAD ===")
    print(f"Total: {len(_resultados)}  OK: {len(_resultados) - len(fallidas)}  FALLAS: {len(fallidas)}")
    if fallidas:
        print("Fallidas: " + ", ".join(fallidas))
    return 0 if not fallidas else 1


if __name__ == "__main__":
    raise SystemExit(main())
