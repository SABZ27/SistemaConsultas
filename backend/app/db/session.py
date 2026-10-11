import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("sistema_consultas.db")

_engine_kwargs = {"pool_pre_ping": True}
_url = settings.database_url
if _url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(_url, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _crear_triggers_actualizado_postgres() -> None:
    from app.models import Base

    funcion = """
    CREATE OR REPLACE FUNCTION set_actualizado()
    RETURNS trigger AS $$
    BEGIN
        NEW.actualizado = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    with engine.begin() as conn:
        conn.execute(text(funcion))
        for tabla in Base.metadata.sorted_tables:
            nombre = tabla.name
            conn.execute(
                text(
                    f"DROP TRIGGER IF EXISTS trg_{nombre}_actualizado ON {nombre}"
                )
            )
            conn.execute(
                text(
                    f"CREATE TRIGGER trg_{nombre}_actualizado "
                    f"BEFORE UPDATE ON {nombre} FOR EACH ROW "
                    f"EXECUTE FUNCTION set_actualizado()"
                )
            )


def init_db() -> None:
    from app.models import Base  # noqa: F401  (registra todos los modelos)

    try:
        Base.metadata.create_all(bind=engine)
        if engine.dialect.name == "postgresql":
            _crear_triggers_actualizado_postgres()
        from app.db.seeds import ejecutar_seeds

        with SessionLocal() as db:
            ejecutar_seeds(db)
            db.commit()
        logger.info("Esquema verificado/creado correctamente en la base de datos.")
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudo conectar a la base de datos (%s). Verifica DB_URL y que Neon esté activo.", type(exc).__name__)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()