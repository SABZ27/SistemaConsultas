import httpx
import pytest

from app.clients import infraestructura
from app.clients.infraestructura import InfraestructuraClient
from app.exceptions.errors import ServiceUnavailableException


class _Respuesta:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class _ClienteHttpFalso:
    def __init__(self, respuestas):
        self._respuestas = respuestas
        self.llamadas = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def get(self, url, headers=None):
        self.llamadas.append((url, headers))
        resultado = self._respuestas.pop(0)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado


def _parchear(monkeypatch, respuestas):
    creados = []

    def fabrica(*_args, **_kwargs):
        cliente = _ClienteHttpFalso(respuestas)
        creados.append(cliente)
        return cliente

    monkeypatch.setattr(infraestructura.httpx, "Client", fabrica)
    return creados


def test_obtener_recurso_404_devuelve_none(monkeypatch):
    _parchear(monkeypatch, [_Respuesta(404)])

    assert InfraestructuraClient().obtener_recurso_fisico(1, "token") is None


def test_obtener_recurso_ok_reenvia_bearer(monkeypatch):
    creados = _parchear(
        monkeypatch, [_Respuesta(200, {"id": 3, "ubicacion": "Sede · Salón 3"})]
    )

    datos = InfraestructuraClient().obtener_recurso_fisico(3, "token-abc")

    assert datos == {"id": 3, "ubicacion": "Sede · Salón 3"}
    _, headers = creados[0].llamadas[0]
    assert headers == {"Authorization": "Bearer token-abc"}


def test_obtener_recurso_5xx_reintenta_y_falla(monkeypatch):
    creados = _parchear(monkeypatch, [_Respuesta(500), _Respuesta(500)])

    with pytest.raises(ServiceUnavailableException):
        InfraestructuraClient().obtener_recurso_fisico(1, "token")

    assert len(creados) == 2


def test_obtener_recurso_5xx_luego_ok(monkeypatch):
    _parchear(monkeypatch, [_Respuesta(500), _Respuesta(200, {"id": 9})])

    assert InfraestructuraClient().obtener_recurso_fisico(9, "token") == {"id": 9}


def test_obtener_recurso_error_de_red_reintenta_y_falla(monkeypatch):
    creados = _parchear(
        monkeypatch, [httpx.ConnectError("caído"), httpx.ConnectError("caído")]
    )

    with pytest.raises(ServiceUnavailableException):
        InfraestructuraClient().obtener_recurso_fisico(1, "token")

    assert len(creados) == 2
