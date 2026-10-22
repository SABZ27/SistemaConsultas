import os

os.environ["DB_URL"] = "sqlite+pysqlite:///./test_bd.sqlite3"
os.environ["ADMIN_CORREO"] = "admin@test.com"
os.environ["ADMIN_PASSWORD"] = "contrasenia123"
os.environ["ADMIN_IDENTIFICACION"] = "9000000000"

import pytest
from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app
from app.models import Base


@pytest.fixture(scope="session", autouse=True)
def _esquema():
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists("test_bd.sqlite3"):
        os.remove("test_bd.sqlite3")


@pytest.fixture(autouse=True)
def _limpiar_bd(_esquema):
    with engine.begin() as conn:
        for tabla in reversed(Base.metadata.sorted_tables):
            conn.execute(tabla.delete())
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def servicios_externos(monkeypatch):
    """Las pruebas nunca salen a la red.

    Se parchean los mÃ©todos del cliente de servicios externos (no httpx), de
    modo que la suite es determinista y no depende de que Express estÃ©
    levantado. Devuelve el registro de llamadas para poder verificar quÃ© se
    pidiÃ³ al microservicio.
    """
    from app.clients.servicios_externos import ServiciosExternosClient

    llamadas = {"festivos": [], "correos": []}

    def _validar_festivo(self, fecha, token):
        llamadas["festivos"].append({"fecha": fecha.isoformat(), "token": token})
        return {
            "id": None,
            "fecha": fecha.isoformat(),
            "pais": "CO",
            "esFestivo": False,
            "nombre": None,
        }

    def _enviar_correo(self, para, asunto, contenido, token, para_nombre=None):
        llamadas["correos"].append(
            {
                "para": para,
                "asunto": asunto,
                "contenido": contenido,
                "token": token,
                "paraNombre": para_nombre,
            }
        )
        return {"id": 1, "messageId": "fake", "estadoEnvio": "ENVIADO"}

    monkeypatch.setattr(ServiciosExternosClient, "validar_festivo", _validar_festivo)
    monkeypatch.setattr(ServiciosExternosClient, "enviar_correo", _enviar_correo)
    return llamadas
