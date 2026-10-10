from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken
from app.repositories.base import RepoBase


class PasswordResetTokenRepository(RepoBase):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cls = PasswordResetToken

    def find_by_token(self, token: str) -> PasswordResetToken | None:
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()

    def find_by_usuario_id(self, usuario_id: int) -> PasswordResetToken | None:
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.usuario_id == usuario_id
        ).first()

    def delete_by_usuario_id(self, usuario_id: int) -> None:
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.usuario_id == usuario_id
        ).delete()