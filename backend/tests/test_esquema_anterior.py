import pytest
from sqlalchemy import create_engine, text

from app.db.session import (
    motivo_esquema_anterior,
    verificar_esquema_anterior,
)
from app.exceptions.errors import EsquemaAnteriorError


def _engine_temporal(tmp_path, nombre="legacy.sqlite3"):
    url = f"sqlite+pysqlite:///{tmp_path / nombre}"
    return create_engine(url)


def test_detecta_tabla_con_columna_activo(tmp_path):
    engine = _engine_temporal(tmp_path)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE usuarios ("
                "id INTEGER PRIMARY KEY, activo BOOLEAN NOT NULL DEFAULT 1)"
            )
        )

    motivo = motivo_esquema_anterior(engine)

    assert motivo is not None
    assert "activo" in motivo
    assert "usuarios" in motivo


def test_detecta_estado_sin_estado_consulta(tmp_path):
    engine = _engine_temporal(tmp_path)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE solicitudes_consultas ("
                "id INTEGER PRIMARY KEY, estado VARCHAR(20))"
            )
        )

    motivo = motivo_esquema_anterior(engine)

    assert motivo is not None
    assert "estado_consulta" in motivo


def test_verificar_aborta_con_esquema_anterior(tmp_path):
    engine = _engine_temporal(tmp_path)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE sedes ("
                "id INTEGER PRIMARY KEY, activo BOOLEAN NOT NULL DEFAULT 1)"
            )
        )

    with pytest.raises(EsquemaAnteriorError) as excinfo:
        verificar_esquema_anterior(engine)

    mensaje = str(excinfo.value)
    assert "esquema anterior" in mensaje.lower()
    assert "recrea" in mensaje.lower()


def test_esquema_nuevo_no_se_detecta_como_anterior(tmp_path):
    engine = _engine_temporal(tmp_path)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE solicitudes_consultas ("
                "id INTEGER PRIMARY KEY, estado_consulta VARCHAR(20), "
                "estado BOOLEAN NOT NULL DEFAULT 1)"
            )
        )

    assert motivo_esquema_anterior(engine) is None
    verificar_esquema_anterior(engine)
