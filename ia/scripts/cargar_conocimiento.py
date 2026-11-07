"""Crea la coleccion de conocimiento en Open WebUI por API y sube los archivos.

Flujo verificado contra la referencia de API de Open WebUI 0.13.0:
  1) POST /api/v1/knowledge/create          -> crea la coleccion (KNOWLEDGE_ID)
  2) POST /api/v1/files/                     -> sube cada archivo (multipart)
  3) GET  /api/v1/files/{id}/process/status  -> espera a que termine el procesado
  4) POST /api/v1/knowledge/{id}/file/add   -> vincula el archivo a la coleccion

El Bearer se toma del entorno (ia/.env). NUNCA se imprime la clave.
Si KNOWLEDGE_ID ya esta definido se reutiliza (idempotente); los contenidos
duplicados (por ejemplo un .md y su version .pdf) se omiten con aviso.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

URL = os.environ.get("OPENWEBUI_URL", "http://localhost:3000").rstrip("/")
CLAVE = os.environ.get("OPENWEBUI_API_KEY", "")
NOMBRE = os.environ.get("KNOWLEDGE_NAME", "consultas-academicas")
DESCRIPCION = "Documentacion del Sistema de Gestion de Consultas Academicas"
CARPETA = RAIZ / "conocimiento"
EXTENSIONES = {".md", ".txt", ".pdf"}
TIMEOUT_HTTP = 60
ESPERA_PROCESADO = 300
INTERVALO_POLL = 2


def cabeceras() -> dict:
    return {"Authorization": "Bearer " + CLAVE, "Accept": "application/json"}


def crear_coleccion() -> str | None:
    r = requests.post(
        URL + "/api/v1/knowledge/create",
        headers={**cabeceras(), "Content-Type": "application/json"},
        json={"name": NOMBRE, "description": DESCRIPCION},
        timeout=TIMEOUT_HTTP,
    )
    if r.status_code != 200:
        print(f"ERROR: no se pudo crear la coleccion (HTTP {r.status_code}).")
        return None
    return r.json().get("id")


def esperar_procesado(file_id: str) -> str:
    inicio = time.monotonic()
    while time.monotonic() - inicio < ESPERA_PROCESADO:
        try:
            r = requests.get(
                URL + f"/api/v1/files/{file_id}/process/status",
                headers=cabeceras(),
                timeout=TIMEOUT_HTTP,
            )
            if r.status_code == 200:
                estado = r.json().get("status")
                if estado in ("completed", "failed"):
                    return estado
        except requests.RequestException:
            pass
        time.sleep(INTERVALO_POLL)
    return "timeout"


def main() -> int:
    if not CLAVE:
        print("ERROR: falta OPENWEBUI_API_KEY en el entorno (ia/.env).")
        print("Activa API Keys en Open WebUI: Settings > Account > API Keys.")
        return 1

    knowledge_id = os.environ.get("KNOWLEDGE_ID", "").strip()
    if knowledge_id:
        print("Reutilizando el KNOWLEDGE_ID definido en el entorno.")
    else:
        knowledge_id = crear_coleccion()
        if not knowledge_id:
            return 1
        print("Coleccion creada.")

    archivos = sorted(
        p for p in CARPETA.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSIONES
    )
    if not archivos:
        print("ERROR: no hay documentos .md/.txt/.pdf en ia/conocimiento/.")
        return 1

    print(f"Subiendo {len(archivos)} archivos a la coleccion ...")
    print("(La PRIMERA carga descarga el modelo de embeddings: requiere internet.)")
    anadidos = 0

    for ruta in archivos:
        try:
            with ruta.open("rb") as fh:
                r = requests.post(
                    URL + "/api/v1/files/",
                    headers=cabeceras(),
                    files={"file": (ruta.name, fh)},
                    timeout=TIMEOUT_HTTP,
                )
            if r.status_code != 200:
                print(f"  [SUBIDA FALLIDA] {ruta.name}: HTTP {r.status_code}")
                continue
            file_id = r.json().get("id")
            if not file_id:
                print(f"  [SIN ID] {ruta.name}")
                continue

            estado = esperar_procesado(file_id)
            if estado != "completed":
                print(f"  [PROCESADO={estado}] {ruta.name}: no vinculado")
                continue

            add = requests.post(
                URL + f"/api/v1/knowledge/{knowledge_id}/file/add",
                headers={**cabeceras(), "Content-Type": "application/json"},
                json={"file_id": file_id},
                timeout=TIMEOUT_HTTP,
            )
            if add.status_code == 200:
                anadidos += 1
                print(f"  [OK] {ruta.name}")
            elif add.status_code == 400 and "uplicate" in add.text:
                print(f"  [DUPLICADO OMITIDO] {ruta.name}")
            else:
                print(f"  [NO VINCULADO] {ruta.name}: HTTP {add.status_code}")
        except requests.RequestException as exc:
            print(f"  [ERROR DE RED] {ruta.name}: {type(exc).__name__}")

    print()
    print(f"Documentos vinculados en esta ejecucion: {anadidos}/{len(archivos)}")
    print(f"KNOWLEDGE_ID={knowledge_id}")
    print("Copia ese valor en ia/.env -> KNOWLEDGE_ID.")
    print("Nunca compartas ni imprimas la OPENWEBUI_API_KEY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
