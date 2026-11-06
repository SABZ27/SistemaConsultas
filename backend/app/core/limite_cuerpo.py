"""Límite de tamaño del cuerpo de las solicitudes HTTP."""

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.exceptions.handlers import _cuerpo

MAX_CUERPO_BYTES = 1024 * 1024
MENSAJE_CUERPO_GRANDE = "El cuerpo de la solicitud es demasiado grande."


class LimiteCuerpoMiddleware:
    """Lee el cuerpo con un tope, lo replica y responde 413 si se excede."""

    def __init__(self, app: ASGIApp, max_bytes: int = MAX_CUERPO_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        mensajes: list[Message] = []
        total = 0

        while True:
            mensaje = await receive()
            mensajes.append(mensaje)

            if mensaje["type"] != "http.request":
                break

            total += len(mensaje.get("body", b""))
            if total > self.max_bytes:
                await self._responder_413(send)
                return
            if not mensaje.get("more_body", False):
                break

        indice = 0

        async def recibir_de_nuevo() -> Message:
            nonlocal indice
            if indice < len(mensajes):
                mensaje = mensajes[indice]
                indice += 1
                return mensaje
            return {"type": "http.disconnect"}

        await self.app(scope, recibir_de_nuevo, send)

    async def _responder_413(self, send: Send) -> None:
        cuerpo = json.dumps(
            _cuerpo(413, MENSAJE_CUERPO_GRANDE), ensure_ascii=False
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(cuerpo)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": cuerpo})
