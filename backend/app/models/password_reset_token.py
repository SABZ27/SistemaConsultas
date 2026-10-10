from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha_expiracion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    utilizado: Mapped[bool] = mapped_column(nullable=False, default=False)

    usuario: Mapped["Usuario"] = relationship()