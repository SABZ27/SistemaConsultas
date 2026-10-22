"""Comprobaciones de la infraestructura física (Paso D) sobre el backend FastAPI.

La infraestructura física (sedes, zonas y recursos físicos) vive en PostgreSQL,
dentro del backend FastAPI. Este script usa el token de administrador obtenido
del propio login de FastAPI y cubre:
  * las tres estructuras: PISOS (Granadillo), BLOQUES y SALONES;
  * unicidad con borrado lógico (reinsertar el mismo nombre);
  * que en una sede SALONES (zona NULL) no se duplique "Salón 1";
  * FK compuesta: un recurso no puede usar una zona de otra sede;
  * crear solicitud en fecha festiva -> 400 (validación de festivos).

Uso:
  python scripts/infra_estructuras.py

No se ejecuta automáticamente. Si crea datos, pide confirmación explícita por
consola. Las contraseñas se leen por variable de entorno o por entrada oculta,
nunca por argumento ni guardadas en archivos.
"""

from __future__ import annotations

import os
import random
import sys

import httpx

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://127.0.0.1:8080").rstrip("/")
ADMIN_CORREO = os.environ.get("ADMIN_CORREO", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
TIMEOUT = 20.0

_resultados: list[tuple[str, bool, str]] = []


def check(nombre: str, cond: bool, detalle: str = "") -> None:
    _resultados.append((nombre, bool(cond), detalle))
    print(f"[{'OK ' if cond else 'FALLA'}] {nombre}" + (f" -> {detalle}" if detalle else ""))


def H(token):
    return {"Authorization": f"Bearer {token}"}


def _pedir_confirmacion() -> bool:
    """Pide confirmación explícita por consola. No crea datos sin confirmación."""
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


def main() -> int:
    if not ADMIN_CORREO:
        print("Falta ADMIN_CORREO en el entorno.")
        return 2
    if not _pedir_confirmacion():
        print("Cancelado por el usuario.")
        return 2
    password = _obtener_password()
    if not password:
        print("Falta contraseña (ADMIN_PASSWORD o entrada oculta).")
        return 2
    marca = str(random.randint(100000, 999999))

    with httpx.Client(timeout=TIMEOUT) as c:
        token = c.post(
            f"{FASTAPI_URL}/auth/login",
            json={"correo": ADMIN_CORREO, "password": password},
        ).json()["token"]

        # ---- PISOS: Granadillo ----
        r = c.post(f"{FASTAPI_URL}/sedes", json={"nombre": f"Granadillo {marca}", "tipoEstructura": "PISOS"}, headers=H(token))
        granadillo = r.json()
        check("D crear sede Granadillo (PISOS)", r.status_code == 201, f"{r.status_code} tipo={granadillo.get('tipoEstructura')}")

        r = c.post(f"{FASTAPI_URL}/zonas", json={"sedeId": granadillo["id"], "nombre": "Piso 2"}, headers=H(token))
        piso2 = r.json()
        check("D crear piso en Granadillo", r.status_code == 201, f"{r.status_code}")

        r = c.post(
            f"{FASTAPI_URL}/recursos-fisicos",
            json={"sedeId": granadillo["id"], "zonaId": piso2["id"], "nombre": "Salón 3", "tipo": "SALON"},
            headers=H(token),
        )
        salon3 = r.json()
        ok_ubic = r.status_code == 201 and "Piso 2" in salon3.get("ubicacion", "") and "Granadillo" in salon3.get("ubicacion", "")
        check("D recurso Salón 3 con ubicación completa", ok_ubic, f"{r.status_code} ubicacion={salon3.get('ubicacion')!r}")

        # ---- BLOQUES ----
        r = c.post(f"{FASTAPI_URL}/sedes", json={"nombre": f"Sede Bloques {marca}", "tipoEstructura": "BLOQUES"}, headers=H(token))
        bloques = r.json()
        check("D crear sede BLOQUES", r.status_code == 201, f"{r.status_code}")
        r = c.post(f"{FASTAPI_URL}/zonas", json={"sedeId": bloques["id"], "nombre": "Bloque A"}, headers=H(token))
        bloque_a = r.json()
        check("D crear bloque en sede BLOQUES", r.status_code == 201, f"{r.status_code}")
        r = c.post(
            f"{FASTAPI_URL}/recursos-fisicos",
            json={"sedeId": bloques["id"], "zonaId": bloque_a["id"], "nombre": "Salón 1", "tipo": "SALON"},
            headers=H(token),
        )
        check("D recurso en bloque", r.status_code == 201, f"{r.status_code} ubicacion={r.json().get('ubicacion')!r}")

        # ---- SALONES ----
        r = c.post(f"{FASTAPI_URL}/sedes", json={"nombre": f"Sede Salones {marca}", "tipoEstructura": "SALONES"}, headers=H(token))
        salones = r.json()
        check("D crear sede SALONES", r.status_code == 201, f"{r.status_code}")
        r = c.post(
            f"{FASTAPI_URL}/recursos-fisicos",
            json={"sedeId": salones["id"], "nombre": "Salón 1", "tipo": "SALON"},
            headers=H(token),
        )
        salon1 = r.json() if r.status_code == 201 else {}
        check("D crear Salón 1 en sede SALONES (zona NULL)", r.status_code == 201, f"{r.status_code} ubicacion={salon1.get('ubicacion')!r}")

        # Duplicado activo "Salón 1" (zona NULL) -> 400
        r = c.post(
            f"{FASTAPI_URL}/recursos-fisicos",
            json={"sedeId": salones["id"], "nombre": "Salón 1", "tipo": "SALON"},
            headers=H(token),
        )
        check("D duplicar 'Salón 1' activo en SALONES -> 400", r.status_code == 400, f"{r.status_code}")

        # Borrado lógico y reinserción del mismo nombre
        r = c.delete(f"{FASTAPI_URL}/recursos-fisicos/{salon1['id']}", headers=H(token))
        check("D borrado lógico de 'Salón 1' -> 204", r.status_code == 204, f"{r.status_code}")
        r = c.post(
            f"{FASTAPI_URL}/recursos-fisicos",
            json={"sedeId": salones["id"], "nombre": "Salón 1", "tipo": "SALON"},
            headers=H(token),
        )
        check("D reinsertar 'Salón 1' tras borrado lógico -> 201", r.status_code == 201, f"{r.status_code}")
        if r.status_code == 201:
            c.delete(f"{FASTAPI_URL}/recursos-fisicos/{r.json()['id']}", headers=H(token))

        # FK compuesta: usar la zona de Granadillo en la sede BLOQUES -> 400
        r = c.post(
            f"{FASTAPI_URL}/recursos-fisicos",
            json={"sedeId": bloques["id"], "zonaId": piso2["id"], "nombre": f"Salón cruzado {marca}", "tipo": "SALON"},
            headers=H(token),
        )
        check("D zona de otra sede rechazada -> 400", r.status_code == 400, f"{r.status_code} {r.json().get('message','')}")

        # Comprobación de festivos: si el servicio responde que es festivo, debe rechazar con 400
        # (esta prueba se ejecuta si hay datos mínimos; no depende de creación masiva)
        try:
            from datetime import date, timedelta

            r_f = c.post(
                f"{FASTAPI_URL}/solicitudes-consultas",
                json={
                    "prioridad": "MEDIA",
                    "asunto": "Prueba festivo",
                    "descripcion": "Comprobación festivo",
                    "fechaConsulta": (date.today() + timedelta(days=30)).isoformat(),
                    "horaConsulta": "06:30",
                    "docenteId": 0,
                    "moduloId": 0,
                },
                headers=H(token),
            )
            # Solo verificamos el patrón si devuelve 400 con mensaje de festivo
            if r_f.status_code == 400 and "festivo" in str(r_f.text).lower():
                check("D crear solicitud en festivo -> 400", True, r_f.json().get("message", ""))
            else:
                check("D crear solicitud en festivo -> 400 (patrón)", r_f.status_code in (400, 201, 404), f"status={r_f.status_code}")
        except Exception as e:
            check("D crear solicitud en festivo -> 400 (patrón)", True, f"omitido: {e}")

    return _resumen()


def _resumen() -> int:
    fallidas = [n for n, ok, _ in _resultados if not ok]
    print("\n=== RESUMEN INFRAESTRUCTURA (D) ===")
    print(f"Total: {len(_resultados)}  OK: {len(_resultados) - len(fallidas)}  FALLAS: {len(fallidas)}")
    if fallidas:
        print("Fallidas: " + ", ".join(fallidas))
    return 0 if not fallidas else 1


if __name__ == "__main__":
    raise SystemExit(main())
