from datetime import datetime

from sqlalchemy import Boolean, DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AuditoriaMixin:
    estado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=text("CURRENT_TIMESTAMP")
    )
    actualizado: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.now,
    )