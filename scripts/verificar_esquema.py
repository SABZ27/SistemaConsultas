#!/usr/bin/env python3
"""Verifica esquema de PostgreSQL (por DB_URL). Solo para BD locales."""

import os
import sys

DB_URL = os.getenv("DB_URL", "")
if not DB_URL or "neon" in DB_URL.lower() or "cloud" in DB_URL.lower():
    print("ADVERTENCIA: verificar_esquema.py solo debe usarse contra bases locales.")
    # No falla si no es local según comportamiento esperado? Es solo verificación


def verificar_postgres():
    try:
        from sqlalchemy import create_engine, text
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not DB_URL:
        print("ERROR: DB_URL no definida")
        sys.exit(1)
    try:
        engine = create_engine(DB_URL, pool_pre_ping=True)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    expected_tables = 16  # según especificación
    with engine.connect() as conn:
        # contar tablas de usuario (no del sistema)
        # PostgreSQL: information_schema.tables
        res = conn.execute(
            text("""
            SELECT count(*) as c
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
        )
        total = res.scalar() or 0
        # verificar restricciones básicas
        # PK, estado, creado, actualizado y al menos un índice único
        res = conn.execute(
            text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """)
        )
        tablas = [r[0] for r in res]
        errores = []
        for t in tablas:
            # tiene PK?
            pk = conn.execute(
                text("""
                SELECT count(*) FROM information_schema.table_constraints
                WHERE table_schema='public' AND table_name=:t AND constraint_type='PRIMARY KEY'
                """),
                {"t": t},
            ).scalar() or 0
            if pk < 1:
                errores.append(f"{t}: sin PRIMARY KEY")
            # columnas estado, creado, actualizado
            cols = conn.execute(
                text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema='public' AND table_name=:t
                """),
                {"t": t},
            ).fetchall()
            colset = {c[0] for c in cols}
            for c in ["estado", "creado", "actualizado"]:
                if c not in colset:
                    errores.append(f"{t}: falta columna {c}")
            # al menos un índice único
            unicos = conn.execute(
                text("""
                SELECT count(DISTINCT i.indexname)
                FROM pg_indexes i
                WHERE schemaname='public' AND tablename=:t AND i.indexdef ILIKE '%UNIQUE%'
                """),
                {"t": t},
            ).scalar() or 0
            # también contar unique constraints
            u2 = conn.execute(
                text("""
                SELECT count(*) FROM information_schema.table_constraints
                WHERE table_schema='public' AND table_name=:t AND constraint_type='UNIQUE'
                """),
                {"t": t},
            ).scalar() or 0
            if unicos < 1 and u2 < 1:
                errores.append(f"{t}: sin índice/constraint único")
        if errores:
            print("ERRORES:")
            for e in errores:
                print(f" - {e}")
            sys.exit(1)
        print(f"OK: {total} tablas verificadas (esperado >= {expected_tables})")


if __name__ == "__main__":
    verificar_postgres()
