"""Bot de Telegram del asistente de consultas academicas.

- long polling (infinity_polling, SIN webhook), telebot/pyTelegramBotAPI, threaded
- token, URL, modelo y coleccion desde el entorno (ia/.env)
- una sola llamada a POST {OPENWEBUI_URL}/api/chat/completions por mensaje,
  con stream=false y timeout de 300 s
- ENRUTADOR (ROUTING_MODE=auto): DOCUMENTACION usa files=[collection],
  DATOS usa tool_ids (sin files). La ruta DATOS exige TELEGRAM_ALLOWED_USERS.

SEGURIDAD: no se registra en logs el contenido de los mensajes ni el token,
ni se imprimen las claves. Los errores al usuario son amigables, en espanol.
"""
from __future__ import annotations

import logging
import os
import re
import threading
import unicodedata
from pathlib import Path

import requests
import telebot
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
URL = os.environ.get("OPENWEBUI_URL", "http://localhost:3000").rstrip("/")
CLAVE = os.environ.get("OPENWEBUI_API_KEY", "")
MODELO = os.environ.get("OLLAMA_MODEL", "consultas-asistente")
KNOWLEDGE_ID = os.environ.get("KNOWLEDGE_ID", "").strip()
TOOL_IDS = [x.strip() for x in os.environ.get("OPENWEBUI_TOOL_IDS", "").split(",") if x.strip()]
ROUTING_MODE = os.environ.get("ROUTING_MODE", "auto").strip().lower() or "auto"
PERMITIDOS = {x.strip() for x in os.environ.get("TELEGRAM_ALLOWED_USERS", "").split(",") if x.strip()}
try:
    TIMEOUT = int(os.environ.get("TELEGRAM_TIMEOUT_SEGUNDOS", "300"))
except ValueError:
    TIMEOUT = 300

MAX_CARACTERES = 4096
RUTA_DOC = "DOCUMENTACION"
RUTA_DATOS = "DATOS"

# Palabras de intencion de DATOS (sin tildes; se compara con texto normalizado).
PALABRAS_DATOS = frozenset({
    "cuantas", "cuantos", "lista", "listar", "listado", "proximas",
    "proximos", "agenda", "disponibilidad", "promedio", "recursos",
    "sede", "sedes", "cantidad", "total", "cuantas consultas",
})

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ia.telegram")
# Evitar que telebot registre updates (que contienen el texto del usuario).
telebot.logger.setLevel(logging.CRITICAL)

_PATRON_THINK_CERRADO = re.compile(r"<think\b[^>]*>.*?</think>", re.DOTALL | re.IGNORECASE)
_PATRON_THINK_ABIERTO = re.compile(r"<think\b[^>]*>.*", re.DOTALL | re.IGNORECASE)

if not TOKEN:
    raise SystemExit("Falta TELEGRAM_BOT_TOKEN en ia/.env. No se inicia el bot.")

bot = telebot.TeleBot(TOKEN, threaded=True, parse_mode=None)

_bloqueos: dict[str, threading.Lock] = {}
_candado_bloqueos = threading.Lock()


def bloqueo_de(usuario_id: str) -> threading.Lock:
    with _candado_bloqueos:
        if usuario_id not in _bloqueos:
            _bloqueos[usuario_id] = threading.Lock()
        return _bloqueos[usuario_id]


def normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def clasificar(texto: str) -> str:
    """Reglas simples de intencion. auto | documentacion | datos."""
    if ROUTING_MODE == "documentacion":
        return RUTA_DOC
    if ROUTING_MODE == "datos":
        return RUTA_DATOS
    n = normalizar(texto)
    return RUTA_DATOS if any(p in n for p in PALABRAS_DATOS) else RUTA_DOC


def limpiar_respuesta(texto: str) -> str:
    """Elimina bloques <think>...</think> si el modelo los emite."""
    t = _PATRON_THINK_CERRADO.sub("", texto or "")
    t = _PATRON_THINK_ABIERTO.sub("", t)
    return t.strip()


def autorizado(mensaje) -> bool:
    if not PERMITIDOS:
        return True
    return str(mensaje.from_user.id) in PERMITIDOS


def llamar_openwebui(pregunta: str, ruta: str) -> str:
    cuerpo = {
        "model": MODELO,
        "messages": [{"role": "user", "content": pregunta}],
        "stream": False,
    }
    if ruta == RUTA_DATOS:
        # Verificado: con stream=false, legacy ejecuta las herramientas en el
        # servidor y devuelve la respuesta en el cuerpo (Path B de la API).
        cuerpo["tool_ids"] = TOOL_IDS
        cuerpo["params"] = {"function_calling": "legacy"}
    else:
        cuerpo["files"] = [{"type": "collection", "id": KNOWLEDGE_ID}]

    r = requests.post(
        URL + "/api/chat/completions",
        headers={"Authorization": "Bearer " + CLAVE, "Content-Type": "application/json"},
        json=cuerpo,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    datos = r.json()
    contenido = datos["choices"][0]["message"]["content"]
    return limpiar_respuesta(contenido)


def enviar_respuesta(chat_id: int, texto: str) -> None:
    if not texto:
        texto = "No obtuve una respuesta. Intenta de nuevo en unos segundos."
    while len(texto) > MAX_CARACTERES:
        corte = texto.rfind("\n", 0, MAX_CARACTERES)
        if corte < MAX_CARACTERES // 2:
            corte = MAX_CARACTERES
        bot.send_message(chat_id, texto[:corte])
        texto = texto[corte:].lstrip("\n")
    if texto:
        bot.send_message(chat_id, texto)


@bot.message_handler(commands=["start"])
def comando_start(mensaje):
    if not autorizado(mensaje):
        return
    bot.reply_to(
        mensaje,
        "Hola. Soy el asistente del Sistema de Consultas Academicas. "
        "Preguntame sobre el sistema y te respondere con la documentacion. "
        "Usa /ayuda para ver los comandos y /id para conocer tu identificador.",
    )


@bot.message_handler(commands=["ayuda"])
def comando_ayuda(mensaje):
    if not autorizado(mensaje):
        return
    bot.reply_to(
        mensaje,
        "Comandos:\n"
        "/start - bienvenida\n"
        "/ayuda - esta ayuda\n"
        "/id - tu identificador de Telegram\n\n"
        "Escribe tu pregunta en texto libre. Las preguntas de documentacion se "
        "responden con la base de conocimiento; las de datos del sistema "
        "(cantidades, listas, agendas) usan las herramientas de solo lectura "
        "y requieren estar en la lista blanca.",
    )


@bot.message_handler(commands=["id"])
def comando_id(mensaje):
    # Disponible sin lista blanca para poder obtenerse el id y anadirlo.
    bot.reply_to(mensaje, "Tu id de Telegram es: " + str(mensaje.from_user.id))


@bot.message_handler(func=lambda m: True, content_types=["text"])
def responder(mensaje):
    if not autorizado(mensaje):
        bot.reply_to(mensaje, "No tienes acceso a este bot.")
        return

    uid = str(mensaje.from_user.id)
    candado = bloqueo_de(uid)
    if not candado.acquire(blocking=False):
        bot.reply_to(mensaje, "Ya estoy atendiendo otra consulta tuya. Espera un momento.")
        return

    try:
        bot.send_chat_action(mensaje.chat.id, "typing")
        pregunta = mensaje.text or ""
        ruta = clasificar(pregunta)

        if ruta == RUTA_DATOS and not PERMITIDOS:
            bot.reply_to(
                mensaje,
                "La consulta de datos del sistema no esta habilitada: falta "
                "configurar TELEGRAM_ALLOWED_USERS.",
            )
            return
        if ruta == RUTA_DATOS and not TOOL_IDS:
            bot.reply_to(
                mensaje,
                "Las herramientas de datos aun no estan configuradas "
                "(OPENWEBUI_TOOL_IDS). Preguntame sobre la documentacion.",
            )
            return
        if ruta == RUTA_DOC and not KNOWLEDGE_ID:
            bot.reply_to(
                mensaje,
                "La base de conocimiento aun no esta configurada (KNOWLEDGE_ID).",
            )
            return
        if not CLAVE:
            bot.reply_to(mensaje, "El servicio no esta configurado todavia. Intenta mas tarde.")
            return

        respuesta = llamar_openwebui(pregunta, ruta)
        enviar_respuesta(mensaje.chat.id, respuesta)
    except Exception as exc:  # amigable y SIN contenido del mensaje en logs
        log.error("Error al atender una consulta: %s", type(exc).__name__)
        bot.reply_to(
            mensaje,
            "No pude obtener una respuesta en este momento. El modelo local "
            "puede estar cargandose; intenta de nuevo en unos segundos.",
        )
    finally:
        candado.release()


def main() -> None:
    log.info("Bot iniciado (modelo=%s, enrutado=%s)", MODELO, ROUTING_MODE)
    log.info("Long polling activo, sin webhook. Ctrl+C para detener.")
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        logger_level=logging.CRITICAL,
        skip_pending=False,
    )


if __name__ == "__main__":
    main()
