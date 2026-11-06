"""Comando IDEMPOTENTE para sembrar los datos de demostración en LOCAL.

Uso:
    python scripts/sembrar_demo.py

El script aplica ``docs/sql/05_datos_demo_postgres.sql`` sobre el backend y,
si se configuran las variables ``DEMO_MYSQL_*`` y existe el cliente ``mysql``,
aplica también ``docs/sql/06_datos_demo_mysql.sql``. Ambos .sql son
idempotentes (``ON CONFLICT DO NOTHING`` / ``INSERT IGNORE``), por lo que se
puede ejecutar las veces que haga falta sin duplicar filas.

``05`` está auditado para PostgreSQL real: lleva ``BEGIN``/``COMMIT`` y 19
``SELECT setval(pg_get_serial_sequence(...))``. En motores que no son
PostgreSQL (por defecto, SQLite local) el script omite esas sentencias:
SQLAlchemy ya maneja la transacción con ``motor.begin()`` y SQLite no tiene
``pg_get_serial_sequence`` ni secuencias SERIAL. El ``.sql`` completo se
ejecuta tal cual en Neon con ``psql``.

Variables de entorno (OPCIONALES). El script **no lee ningún archivo .env**,
no imprime contraseñas ni cadenas de conexión y no se conecta a Neon ni a
Aiven:

    DEMO_DB_URL              URL SQLAlchemy del backend; por defecto un
                             SQLite local en el directorio temporal del sistema
    DEMO_MYSQL_HOST          host MySQL local (por defecto 127.0.0.1)
    DEMO_MYSQL_PORT          puerto MySQL local (por defecto 3307)
    DEMO_MYSQL_USER          usuario MySQL local
    DEMO_MYSQL_PASSWORD      contraseña MySQL local
    DEMO_MYSQL_DATABASE      base MySQL local (debe terminar en _test)

Si no se configuran las variables MySQL, el script siembra solo el backend e
imprime el comando equivalente para MySQL (ver docs/sql/SEMBRAR_DEMO.md).

No se ejecuta automáticamente. Solo bases locales.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SQL_DIR = RAIZ / "docs" / "sql"
sys.path.insert(0, str(RAIZ / "backend"))

from sqlalchemy import create_engine, text  # noqa: E402


def _sentencias(ruta: Path) -> list[str]:
    """Divide por ';' respetando los literales entre comillas simples.

    Un ';' dentro de un texto (por ejemplo un comentario o una descripción)
    no es un fin de sentencia.
    """
    contenido = ruta.read_text(encoding="utf-8")
    sin_comentarios = "\n".join(
        linea
        for linea in contenido.splitlines()
        if not linea.strip().startswith("--")
    )
    sentencias: list[str] = []
    actual: list[str] = []
    en_literal = False
    i = 0
    while i < len(sin_comentarios):
        caracter = sin_comentarios[i]
        if en_literal:
            actual.append(caracter)
            if caracter == "'":
                if i + 1 < len(sin_comentarios) and sin_comentarios[i + 1] == "'":
                    actual.append("'")
                    i += 2
                    continue
                en_literal = False
            i += 1
            continue
        if caracter == "'":
            en_literal = True
            actual.append(caracter)
            i += 1
            continue
        if caracter == ";":
            texto = "".join(actual).strip()
            if texto:
                sentencias.append(texto)
            actual = []
            i += 1
            continue
        actual.append(caracter)
        i += 1
    texto = "".join(actual).strip()
    if texto:
        sentencias.append(texto)
    return sentencias


def _sembrar_backend() -> None:
    from app.models import Base  # import local: no lee .env
    url = os.environ.get("DEMO_DB_URL") or (
        "sqlite+pysqlite:///" + str(Path(tempfile.gettempdir()) / "sistema_consultas_demo.sqlite3")
    )
    motor = create_engine(url)
    if motor.dialect.name == "sqlite":
        Base.metadata.create_all(bind=motor)
    sentencias = _sentencias(SQL_DIR / "05_datos_demo_postgres.sql")
    es_postgres = motor.dialect.name == "postgresql"
    # BEGIN/COMMIT los gestiona SQLAlchemy con motor.begin(); los setval son
    # exclusivos de PostgreSQL (pg_get_serial_sequence + secuencias SERIAL).
    sentencias = [
        s for s in sentencias
        if s.strip().upper() not in ("BEGIN", "COMMIT")
        and (es_postgres or "pg_get_serial_sequence" not in s)
    ]
    with motor.begin() as conexion:
        for sentencia in sentencias:
            conexion.exec_driver_sql(sentencia)
    with motor.connect() as conexion:
        total = conexion.execute(text("SELECT COUNT(*) FROM usuarios")).scalar()
    print(f"Backend sembrado: {len(sentencias)} sentencias, {total} usuarios.")


def _sembrar_mysql() -> None:
    host = os.environ.get("DEMO_MYSQL_HOST", "127.0.0.1")
    puerto = os.environ.get("DEMO_MYSQL_PORT", "3307")
    usuario = os.environ.get("DEMO_MYSQL_USER", "")
    clave = os.environ.get("DEMO_MYSQL_PASSWORD", "")
    base = os.environ.get("DEMO_MYSQL_DATABASE", "")
    cliente = shutil.which("mysql")

    if not (usuario and base and cliente):
        print(
            "MySQL: sin DEMO_MYSQL_USER/DEMO_MYSQL_DATABASE o sin cliente "
            "'mysql' en PATH. Ejecuta manualmente (idempotente):\n"
            "  mysql -h 127.0.0.1 -P 3307 -u <usuario> -p <base_test> "
            "< docs/sql/06_datos_demo_mysql.sql\n"
            "Ver docs/sql/SEMBRAR_DEMO.md."
        )
        return

    argumentos = [
        cliente,
        f"--host={host}",
        f"--port={puerto}",
        f"--user={usuario}",
        "--default-character-set=utf8mb4",
        base,
    ]
    if clave:
        argumentos.append(f"--password={clave}")  # nunca se imprime
    with open(SQL_DIR / "06_datos_demo_mysql.sql", "rb") as archivo:
        resultado = subprocess.run(argumentos, stdin=archivo, check=False)
    if resultado.returncode != 0:
        raise SystemExit("No se pudo aplicar 06_datos_demo_mysql.sql.")
    print("MySQL sembrado: 06_datos_demo_mysql.sql aplicado.")


def main() -> int:
    _sembrar_backend()
    _sembrar_mysql()
    print("Siembra de demostración completada (solo local).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
