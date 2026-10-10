from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.errors import BadRequestException


class RepoBase:
    def __init__(self, db: Session):
        self.db = db

    def save(self, obj):
        self.db.add(obj)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise BadRequestException("Ya existe un registro con el mismo valor único.") from exc
        return obj

    def delete(self, obj):
        try:
            self.db.delete(obj)
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise BadRequestException("No se puede eliminar el registro porque está en uso.") from exc

    def exists_by_id(self, entidad_cls, id_: int) -> bool:
        return self.db.get(entidad_cls, id_) is not None