"""Envia las preguntas de ia/pruebas/preguntas.md a la API de Open WebUI.

Comprueba palabras clave, muestra aciertos y tiempo por respuesta.
Nunca imprime la OPENWEBUI_API_KEY. La comprobacion es estricta: TODAS las
palabras clave del caso deben aparecer en la respuesta (sin tildes ni
mayusculas). En la Fase 2 se amplia con los casos DATOS y la comparacion
contra el endpoint directo de mcpo.
"""
from __future__ import annotations

import argparse
import os
import re
import time
import unicodedata
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

URL = os.environ.get("OPENWEBUI_URL", "http://localhost:3000").rstrip("/")
CLAVE = os.environ.get("OPENWEBUI_API_KEY", "")
MODELO = os.environ.get("OLLAMA_MODEL", "consultas-asistente")
KNOWLEDGE_ID = os.environ.get("KNOWLEDGE_ID", "").strip()
ARCHIVO = RAIZ / "pruebas" / "preguntas.md"

_PATRON_THINK_CERRADO = re.compile(r"<think\b[^>]*>.*?</think>", re.DOTALL | re.IGNORECASE)
_PATRON_THINK_ABIERTO = re.compile(r"<think\b[^>]*>.*", re.DOTALL | re.IGNORECASE)


def normalizar(texto: str) -> str:
    d = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def limpiar(texto: str) -> str:
    t = _PATRON_THINK_CERRADO.sub("", texto or "")
    return _PATRON_THINK_ABIERTO.sub("", t).strip()


def cargar_casos(ruta: Path) -> list[dict]:
    casos: list[dict] = []
    actual: dict | None = None

    def cerrar():
        nonlocal actual
        if actual and actual.get("TIPO") and actual.get("PREGUNTA"):
            actual["CLAVES"] = [c.strip() for c in actual.get("CLAVES", "").split("|") if c.strip()]
            casos.append(actual)
        actual = None

    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            cerrar()
            actual = {"ID": linea[3:].strip()}
            continue
        if actual is None:
            continue
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            clave = clave.strip().upper()
            if clave in {"TIPO", "PREGUNTA", "CLAVES", "FUENTE", "ESPERADO", "HERRAMIENTA", "ARGS"}:
                actual[clave] = valor.strip()
    cerrar()
    return casos


def construir_cuerpo(caso: dict) -> dict | None:
    """Fase 1: DOCUMENTACION y FUERA usan la coleccion de conocimiento."""
    tipo = caso.get("TIPO", "").upper()
    if tipo == "DATOS":
        return None  # se implementa en la Fase 2
    cuerpo = {
        "model": MODELO,
        "messages": [{"role": "user", "content": caso["PREGUNTA"]}],
        "stream": False,
        "files": [{"type": "collection", "id": KNOWLEDGE_ID}],
    }
    return cuerpo


def extraer_contenido(datos: dict) -> str:
    try:
        return datos["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def comprobar(caso: dict, respuesta: str, datos: dict) -> tuple[bool, str]:
    """Devuelve (acierto, detalle). La Fase 2 anade la verificacion de herramienta."""
    normalizada = normalizar(respuesta)
    claves = [normalizar(c) for c in caso.get("CLAVES", [])]
    faltan = [c for c in claves if c and c not in normalizada]
    if faltan:
        return False, "faltan: " + ", ".join(faltan)
    return True, "palabras clave OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluador de la base de conocimiento")
    parser.add_argument("--limite", type=int, default=0, help="Maximo de casos a enviar (0 = todos)")
    parser.add_argument("--solo", default="", help="IDs separados por coma, p. ej. DOC-01,FUERA-02")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout HTTP en segundos")
    args = parser.parse_args()

    if not CLAVE:
        print("ERROR: falta OPENWEBUI_API_KEY en el entorno (ia/.env).")
        return 1
    if not KNOWLEDGE_ID:
        print("ERROR: falta KNOWLEDGE_ID en el entorno (ia/.env).")
        return 1
    if not ARCHIVO.exists():
        print("ERROR: no existe ia/pruebas/preguntas.md")
        return 1

    casos = cargar_casos(ARCHIVO)
    if args.solo:
        permitidos = {x.strip() for x in args.solo.split(",") if x.strip()}
        casos = [c for c in casos if c["ID"] in permitidos]
    if args.limite > 0:
        casos = casos[: args.limite]
    if not casos:
        print("No hay casos que evaluar.")
        return 1

    cabeceras = {"Authorization": "Bearer " + CLAVE, "Content-Type": "application/json"}
    print(f"Modelo: {MODELO} | Coleccion configurada | Casos: {len(casos)}")
    print("-" * 78)

    aciertos = 0
    tiempo_total = 0.0
    evaluados = 0

    for caso in casos:
        cuerpo = construir_cuerpo(caso)
        if cuerpo is None:
            print(f"{caso['ID']:<10} OMITIDO  (caso DATOS: se evalua en la Fase 2)")
            continue
        inicio = time.perf_counter()
        try:
            r = requests.post(URL + "/api/chat/completions", headers=cabeceras,
                              json=cuerpo, timeout=args.timeout)
            transcurrido = time.perf_counter() - inicio
            tiempo_total += transcurrido
            evaluados += 1
            if r.status_code != 200:
                print(f"{caso['ID']:<10} FALLO    HTTP {r.status_code}  {transcurrido:.2f} s")
                continue
            datos = r.json()
            respuesta = limpiar(extraer_contenido(datos))
            ok, detalle = comprobar(caso, respuesta, datos)
            aciertos += int(ok)
            marca = "ACIERTO" if ok else "FALLO"
            print(f"{caso['ID']:<10} {marca:<8} {transcurrido:6.2f} s  {detalle}")
            if not ok:
                vista = respuesta.replace("\n", " ")[:160]
                print(f"           respuesta: {vista}")
        except requests.RequestException as exc:
            print(f"{caso['ID']:<10} FALLO    {type(exc).__name__}")

    print("-" * 78)
    print(f"Aciertos: {aciertos}/{evaluados} casos evaluados ({len(casos)} casos en total)")
    if evaluados:
        print(f"Tiempo total: {tiempo_total:.2f} s | Promedio: {tiempo_total / evaluados:.2f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
