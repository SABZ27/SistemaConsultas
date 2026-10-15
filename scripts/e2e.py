"""Prueba de extremo a extremo (e2e) del Sistema de Consultas.

Ejercita los dos servicios en ejecución:
  * FastAPI (backend)          -> http://127.0.0.1:8080
  * Express (infraestructura)  -> http://127.0.0.1:3001

Modos:
  full   (por defecto): flujo completo de la Fase E + sonda "sin módulo
           INFRAESTRUCTURA -> 403" al escribir en Express.
  caido  : con Express detenido, asignar un recurso físico debe responder
           503 ("Servicio de infraestructura no disponible").

Configuración por variables de entorno (nunca se imprimen secretos):
  FASTAPI_URL, INFRA_URL, ADMIN_CORREO, ADMIN_PASSWORD

Uso:
  python scripts/e2e.py [full|caido]
"""

from __future__ import annotations

import os
import random
import sys
from datetime import date, timedelta

import httpx

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://127.0.0.1:8080").rstrip("/")
INFRA_URL = os.environ.get("INFRA_URL", "http://127.0.0.1:3001").rstrip("/")
ADMIN_CORREO = os.environ.get("ADMIN_CORREO", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

PASSWORD = "contrasenia123"
TIMEOUT = 20.0

_resultados: list[tuple[str, bool, str]] = []


def registrar(nombre: str, ok: bool, detalle: str = "") -> None:
    _resultados.append((nombre, ok, detalle))
    print(f"[{'OK ' if ok else 'FALLA'}] {nombre}" + (f" -> {detalle}" if detalle else ""))


def _post(client, url, json, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post(url, json=json, headers=headers)


def _patch(client, url, json, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.patch(url, json=json, headers=headers)


def _get(client, url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.get(url, headers=headers)


def login(client, correo, password):
    r = client.post(f"{FASTAPI_URL}/auth/login", json={"correo": correo, "password": password})
    r.raise_for_status()
    return r.json()


def registro(client, correo, identificacion, rol):
    payload = {
        "identificacion": identificacion,
        "nombre": "Nombre",
        "apellido": "Prueba",
        "correo": correo,
        "password": PASSWORD,
        "rol": rol,
    }
    r = client.post(f"{FASTAPI_URL}/auth/register", json=payload)
    if r.status_code != 201:
        raise RuntimeError(f"registro {correo}: {r.status_code} {r.text}")
    return login(client, correo, PASSWORD)


def _nar(n: int) -> str:
    return str(n) + str(random.randint(1000, 9999))


def modo_full() -> int:
    fecha = date.today() + timedelta(days=1)
    marca = fecha.strftime("%H%M%S") + str(random.randint(100, 999))
    anio = date.today().year
    anio_sig = anio + 1

    with httpx.Client(timeout=TIMEOUT) as client:
        admin = login(client, ADMIN_CORREO, ADMIN_PASSWORD)
        registrar("login admin", True, admin.get("rol", ""))

        modulos_admin = {m["nombre"] for m in (admin.get("modulos") or [])}
        registrar("admin tiene módulo INFRAESTRUCTURA", "INFRAESTRUCTURA" in modulos_admin)

        # ---- 1) Infraestructura en Express: sede PISOS -> piso -> salón ----
        r = _post(
            client,
            f"{INFRA_URL}/sedes",
            {"nombre": f"Sede E2E {marca}", "tipoEstructura": "PISOS"},
            admin["token"],
        )
        sede = r.json() if r.status_code == 201 else {}
        registrar("Express: crear sede PISOS", r.status_code == 201, f"{r.status_code}")

        r = _post(
            client,
            f"{INFRA_URL}/zonas",
            {"sedeId": sede.get("id"), "nombre": f"Piso {marca}"},
            admin["token"],
        )
        zona = r.json() if r.status_code == 201 else {}
        registrar("Express: crear piso (zona)", r.status_code == 201, f"{r.status_code}")

        r = _post(
            client,
            f"{INFRA_URL}/recursos-fisicos",
            {
                "sedeId": sede.get("id"),
                "zonaId": zona.get("id"),
                "nombre": f"Salón {marca}",
                "tipo": "SALON",
            },
            admin["token"],
        )
        recurso = r.json() if r.status_code == 201 else {}
        registrar("Express: crear salón (recurso)", r.status_code == 201, f"{r.status_code}")

        # ---- 2) Datos académicos en FastAPI ----
        r = _post(
            client,
            f"{FASTAPI_URL}/programas",
            {"nombre": f"Programa E2E {marca}"},
            admin["token"],
        )
        registrar("FastAPI: crear programa", r.status_code == 201, f"{r.status_code}")

        r = _post(
            client,
            f"{FASTAPI_URL}/modulos",
            {"nombre": f"Módulo E2E {marca}", "descripcion": "Módulo de prueba e2e"},
            admin["token"],
        )
        modulo = r.json() if r.status_code == 201 else {}
        registrar("FastAPI: crear módulo", r.status_code == 201, f"{r.status_code}")

        docente = registro(client, f"docente.e2e.{marca}@test.com", _nar(30), "DOCENTE")
        estudiante = registro(client, f"estudiante.e2e.{marca}@test.com", _nar(10), "ESTUDIANTE")
        registrar("FastAPI: registrar docente y estudiante", True, f"doc={docente['id_usuario']} est={estudiante['id_usuario']}")

        r = _post(
            client,
            f"{FASTAPI_URL}/docentes-modulos",
            {"docenteId": docente["id_usuario"], "moduloId": modulo["id"]},
            admin["token"],
        )
        registrar("FastAPI: asignar docente-módulo", r.status_code == 201, f"{r.status_code}")

        # Crear un periodo académico (año siguiente, sin solape con el sembrado)
        r = _post(
            client,
            f"{FASTAPI_URL}/periodos-academicos",
            {"nombre": f"{anio_sig}-verif-{marca}", "fechaInicio": f"{anio_sig}-01-01", "fechaFin": f"{anio_sig}-12-31"},
            admin["token"],
        )
        registrar("FastAPI: crear periodo académico", r.status_code == 201, f"{r.status_code}")

        r = _post(
            client,
            f"{FASTAPI_URL}/disponibilidad-docente",
            {
                "docenteId": docente["id_usuario"],
                "diaSemana": fecha.isoweekday(),
                "horaInicio": "00:00",
                "horaFin": "23:59",
            },
            admin["token"],
        )
        registrar("FastAPI: crear disponibilidad", r.status_code == 201, f"{r.status_code}")

        # ---- 3) El estudiante crea la solicitud (PENDIENTE) ----
        r = _post(
            client,
            f"{FASTAPI_URL}/solicitudes-consultas",
            {
                "prioridad": "MEDIA",
                "asunto": "Consulta E2E",
                "descripcion": "Flujo completo de extremo a extremo",
                "fechaConsulta": fecha.isoformat(),
                "horaConsulta": "06:30",
                "docenteId": docente["id_usuario"],
                "moduloId": modulo["id"],
            },
            estudiante["token"],
        )
        solicitud = r.json() if r.status_code == 201 else {}
        registrar(
            "FastAPI: estudiante crea solicitud (PENDIENTE)",
            r.status_code == 201 and solicitud.get("estado") == "PENDIENTE",
            f"{r.status_code} estado={solicitud.get('estado')}",
        )
        sid = solicitud.get("id")

        # ---- 4) Asignar recurso físico (FastAPI -> Express, reenvía Bearer) ----
        r = _patch(
            client,
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/recurso-fisico",
            {"recursoFisicoId": recurso.get("id")},
            docente["token"],
        )
        ubic = r.json().get("nombreRecursoFisico", "") if r.status_code == 200 else ""
        ok_recurso = (
            r.status_code == 200
            and r.json().get("recursoFisicoId") == recurso.get("id")
            and "Piso" in ubic
        )
        registrar("Asignar recurso reenvía Bearer y guarda ubicación", ok_recurso, f"{r.status_code} ubicacion={ubic!r}")

        # ---- 5) Transiciones de estado válidas: EN_PROCESO -> RESUELTA ----
        r = _patch(
            client,
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/estado",
            {"estado": "EN_PROCESO"},
            docente["token"],
        )
        registrar("Transición PENDIENTE -> EN_PROCESO", r.status_code == 200 and r.json().get("estado") == "EN_PROCESO", f"{r.status_code}")

        # ---- 6) Comentario (permitido en EN_PROCESO) ----
        r = _post(
            client,
            f"{FASTAPI_URL}/comentarios",
            {"contenido": "Comentario del estudiante en la consulta e2e", "solicitudConsultaId": sid},
            estudiante["token"],
        )
        registrar("Comentario del estudiante en EN_PROCESO", r.status_code == 201, f"{r.status_code}")

        r = _post(
            client,
            f"{FASTAPI_URL}/comentarios",
            {"contenido": "Respuesta del docente en la consulta e2e", "solicitudConsultaId": sid},
            docente["token"],
        )
        registrar("Comentario del docente en EN_PROCESO", r.status_code == 201, f"{r.status_code}")

        r = _patch(
            client,
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/estado",
            {"estado": "RESUELTA"},
            docente["token"],
        )
        registrar("Transición EN_PROCESO -> RESUELTA", r.status_code == 200 and r.json().get("estado") == "RESUELTA", f"{r.status_code}")

        # ---- 7) Calificación (solo estudiante dueño, tras RESUELTA) ----
        r = _post(
            client,
            f"{FASTAPI_URL}/solicitudes-consultas/{sid}/calificacion",
            {"puntaje": 5, "comentario": "Excelente atención"},
            estudiante["token"],
        )
        registrar("Calificación tras RESUELTA", r.status_code == 201 and r.json().get("puntaje") == 5, f"{r.status_code}")

        # ---- 8) Promedio del docente ----
        r = _get(client, f"{FASTAPI_URL}/docentes/{docente['id_usuario']}/calificaciones/promedio", admin["token"])
        body = r.json() if r.status_code == 200 else {}
        registrar("Promedio del docente", r.status_code == 200 and body.get("total", 0) >= 1, f"status={r.status_code} {body}")

        # ---- 9) Notificaciones para docente y estudiante ----
        r = _get(client, f"{FASTAPI_URL}/notificaciones", docente["token"])
        registrar("Notificaciones del docente", r.status_code == 200 and len(r.json()) >= 1, f"{r.status_code} n={len(r.json()) if r.status_code == 200 else '-'}")

        r = _get(client, f"{FASTAPI_URL}/notificaciones", estudiante["token"])
        registrar("Notificaciones del estudiante", r.status_code == 200 and len(r.json()) >= 1, f"{r.status_code} n={len(r.json()) if r.status_code == 200 else '-'}")

        # ---- 10) Sonda: sin módulo INFRAESTRUCTURA -> 403 al escribir en Express ----
        r = _post(
            client,
            f"{INFRA_URL}/sedes",
            {"nombre": f"Sede prohibida {marca}", "tipoEstructura": "BLOQUES"},
            estudiante["token"],
        )
        registrar("Express: sin módulo INFRAESTRUCTURA -> 403", r.status_code == 403, f"{r.status_code}")

    return _resumen()


def modo_caido() -> int:
    fecha = date.today() + timedelta(days=1)
    marca = fecha.strftime("%H%M%S") + str(random.randint(100, 999))
    with httpx.Client(timeout=TIMEOUT) as client:
        admin = login(client, ADMIN_CORREO, ADMIN_PASSWORD)
        docente = registro(client, f"docente.caido.{marca}@test.com", _nar(31), "DOCENTE")
        estudiante = registro(client, f"estudiante.caido.{marca}@test.com", _nar(11), "ESTUDIANTE")
        r = _post(
            client,
            f"{FASTAPI_URL}/modulos",
            {"nombre": f"Módulo caído {marca}", "descripcion": "Módulo de prueba caída"},
            admin["token"],
        )
        modulo = r.json()
        _post(
            client,
            f"{FASTAPI_URL}/docentes-modulos",
            {"docenteId": docente["id_usuario"], "moduloId": modulo["id"]},
            admin["token"],
        )
        _post(
            client,
            f"{FASTAPI_URL}/disponibilidad-docente",
            {
                "docenteId": docente["id_usuario"],
                "diaSemana": fecha.isoweekday(),
                "horaInicio": "00:00",
                "horaFin": "23:59",
            },
            admin["token"],
        )
        r = _post(
            client,
            f"{FASTAPI_URL}/solicitudes-consultas",
            {
                "prioridad": "MEDIA",
                "asunto": "Consulta caída",
                "descripcion": "Descripción de prueba caída",
                "fechaConsulta": fecha.isoformat(),
                "horaConsulta": "06:30",
                "docenteId": docente["id_usuario"],
                "moduloId": modulo["id"],
            },
            estudiante["token"],
        )
        solicitud = r.json()

        r = _patch(
            client,
            f"{FASTAPI_URL}/solicitudes-consultas/{solicitud['id']}/recurso-fisico",
            {"recursoFisicoId": 1},
            docente["token"],
        )
        body = r.json()
        registrar(
            "Express caído -> 503 infraestructura no disponible",
            r.status_code == 503 and body.get("message") == "Servicio de infraestructura no disponible",
            f"{r.status_code} {body.get('message', '')}",
        )
    return _resumen()


def _resumen() -> int:
    fallidas = [n for n, ok, _ in _resultados if not ok]
    print("\n=== RESUMEN E2E ===")
    print(f"Total: {len(_resultados)}  OK: {len(_resultados) - len(fallidas)}  FALLAS: {len(fallidas)}")
    if fallidas:
        print("Fallidas: " + ", ".join(fallidas))
    return 0 if not fallidas else 1


def main() -> int:
    modo = sys.argv[1] if len(sys.argv) > 1 else "full"
    if not ADMIN_CORREO or not ADMIN_PASSWORD:
        print("Faltan ADMIN_CORREO/ADMIN_PASSWORD en el entorno.")
        return 2
    return modo_caido() if modo == "caido" else modo_full()


if __name__ == "__main__":
    raise SystemExit(main())
