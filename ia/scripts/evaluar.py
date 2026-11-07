"""Envia las preguntas de ia/pruebas/preguntas.md a la API de Open WebUI.

Fase 1: 15 casos de DOCUMENTACION + 3 FUERA (coleccion de conocimiento).
Fase 2: + 10 casos DATOS (tool_ids, sin files), con la herramienta esperada.

Para los casos DATOS se intenta primero detectar la herramienta usada en el
array "sources" que devuelve la API (Path B / legacy). Si la API no expone que
herramienta se uso, se compara la respuesta con la LLAMADA DIRECTA al endpoint
de mcpo (POST {MCPO_URL}/{HERRAMIENTA}) y se cuentan los valores coincidentes.

Comprueba palabras clave, muestra aciertos y tiempo por respuesta. Nunca
imprime la OPENWEBUI_API_KEY ni la MCPO_API_KEY.
"""
from __future__ import annotations

import argparse
import json
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
TOOL_IDS = [x.strip() for x in os.environ.get("OPENWEBUI_TOOL_IDS", "").split(",") if x.strip()]
MCPO_URL = os.environ.get("MCPO_URL", "http://localhost:8000").rstrip("/")
MCPO_CLAVE = os.environ.get("MCPO_API_KEY", "")
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
            if "ARGS" in actual:
                try:
                    actual["ARGS"] = json.loads(actual["ARGS"])
                except (ValueError, TypeError):
                    actual["ARGS"] = {}
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


def construir_cuerpo(caso: dict) -> dict:
    """DOCUMENTACION/FUERA -> files=[collection]; DATOS -> tool_ids, sin files."""
    cuerpo = {
        "model": MODELO,
        "messages": [{"role": "user", "content": caso["PREGUNTA"]}],
        "stream": False,
    }
    if caso.get("TIPO", "").upper() == "DATOS":
        # Verificado: con stream=false, legacy ejecuta las herramientas en el
        # servidor y devuelve la respuesta (y "sources") en el cuerpo.
        cuerpo["tool_ids"] = TOOL_IDS
        cuerpo["params"] = {"function_calling": "legacy"}
    else:
        cuerpo["files"] = [{"type": "collection", "id": KNOWLEDGE_ID}]
    return cuerpo


def extraer_contenido(datos: dict) -> str:
    try:
        return datos["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def extraer_valores(obj) -> set[str]:
    """Escalares (normalizados) del JSON de mcpo, para comparar con la respuesta."""
    salida: set[str] = set()

    def recorrer(x):
        if isinstance(x, dict):
            for v in x.values():
                recorrer(v)
        elif isinstance(x, list):
            for v in x:
                recorrer(v)
        elif isinstance(x, bool):
            return
        elif isinstance(x, (int, float)):
            salida.add(normalizar(str(x)))
        elif isinstance(x, str):
            salida.add(normalizar(x))

    recorrer(obj)
    return {v for v in salida if v}


def llamar_mcpo(herramienta: str, args: dict):
    """Llamada directa al endpoint OpenAPI de mcpo.

    NO VERIFICADO: mcpo 0.0.20 usa --api-key; aqui se envia como Bearer, que
    es lo que Open WebUI usa para servidores OpenAPI. Si tu mcpo exige otra
    cabecera, ajusta los headers de esta funcion.
    """
    r = requests.post(
        MCPO_URL + "/" + herramienta,
        headers={"Authorization": "Bearer " + MCPO_CLAVE, "Content-Type": "application/json"},
        json=args if isinstance(args, dict) else {},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def comprobar_datos(caso: dict, respuesta: str, datos: dict) -> tuple[bool | None, str]:
    """Devuelve (acierto | None=NO VERIFICADO, detalle)."""
    herramienta = caso.get("HERRAMIENTA", "")
    normalizada = normalizar(respuesta)
    claves = [normalizar(c) for c in caso.get("CLAVES", [])]
    faltan = [c for c in claves if c and c not in normalizada]
    if faltan:
        return False, "faltan palabras clave: " + ", ".join(faltan)

    # 1) La API (Path B) devuelve "sources" con los resultados de las
    #    herramientas. Si ahi aparece la herramienta esperada, ya esta verificado.
    fuentes = datos.get("sources") or []
    if herramienta and herramienta.lower() in json.dumps(fuentes, ensure_ascii=False).lower():
        return True, "herramienta detectada en sources: " + herramienta

    # 2) La API no expone que herramienta se uso: comparar con mcpo directo.
    try:
        resultado = llamar_mcpo(herramienta, caso.get("ARGS") or {})
    except Exception as exc:
        return None, "mcpo no disponible (" + type(exc).__name__ + "): NO VERIFICADO"

    valores = extraer_valores(resultado)
    coincidencias = [v for v in valores if len(v) >= 3 and v in normalizada]
    if coincidencias:
        return True, (
            f"sin tool-id en la API; mcpo: {len(coincidencias)} valor(es) "
            f"coincidente(s) [{herramienta}]"
        )
    return False, f"sin tool-id en la API; la respuesta no coincide con mcpo [{herramienta}]"


def comprobar(caso: dict, respuesta: str, datos: dict) -> tuple[bool | None, str]:
    if caso.get("TIPO", "").upper() == "DATOS":
        return comprobar_datos(caso, respuesta, datos)
    normalizada = normalizar(respuesta)
    claves = [normalizar(c) for c in caso.get("CLAVES", [])]
    faltan = [c for c in claves if c and c not in normalizada]
    if faltan:
        return False, "faltan: " + ", ".join(faltan)
    return True, "palabras clave OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluador de conocimiento y de datos")
    parser.add_argument("--limite", type=int, default=0, help="Maximo de casos a enviar (0 = todos)")
    parser.add_argument("--solo", default="", help="IDs separados por coma, p. ej. DOC-01,DAT-03")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout HTTP en segundos")
    args = parser.parse_args()

    if not CLAVE:
        print("ERROR: falta OPENWEBUI_API_KEY en el entorno (ia/.env).")
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

    hay_doc = any(c.get("TIPO", "").upper() != "DATOS" for c in casos)
    hay_datos = any(c.get("TIPO", "").upper() == "DATOS" for c in casos)
    if hay_doc and not KNOWLEDGE_ID:
        print("ERROR: falta KNOWLEDGE_ID en el entorno (ia/.env).")
        return 1
    if hay_datos and not TOOL_IDS:
        print("AVISO: falta OPENWEBUI_TOOL_IDS; los casos DATOS se omitiran.")

    cabeceras = {"Authorization": "Bearer " + CLAVE, "Content-Type": "application/json"}
    print(f"Modelo: {MODELO} | Casos: {len(casos)} (doc/knowledge + datos/tool_ids)")
    print("-" * 92)

    aciertos = 0
    evaluados = 0
    no_verificados = 0
    tiempo_total = 0.0

    for caso in casos:
        tipo = caso.get("TIPO", "").upper()
        if tipo == "DATOS" and not TOOL_IDS:
            print(f"{caso['ID']:<10} OMITIDO  (falta OPENWEBUI_TOOL_IDS)")
            continue

        cuerpo = construir_cuerpo(caso)
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
            if ok is None:
                no_verificados += 1
                marca = "NO VERIF"
            else:
                aciertos += int(ok)
                marca = "ACIERTO" if ok else "FALLO"
            print(f"{caso['ID']:<10} {marca:<8} {transcurrido:6.2f} s  {detalle}")
            if ok is False:
                vista = respuesta.replace("\n", " ")[:160]
                print(f"           respuesta: {vista}")
        except requests.RequestException as exc:
            print(f"{caso['ID']:<10} FALLO    {type(exc).__name__}")

    print("-" * 92)
    print(f"Aciertos: {aciertos}/{evaluados} evaluados | NO VERIFICADOS: {no_verificados} | casos: {len(casos)}")
    if evaluados:
        print(f"Tiempo total: {tiempo_total:.2f} s | Promedio: {tiempo_total / evaluados:.2f} s")
    print("Los casos DATOS dependen de los datos de demo existentes en la BD.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
