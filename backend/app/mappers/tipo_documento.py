from app.models.tipo_documento import TipoDocumento
from app.schemas.tipo_documento import TipoDocumentoResponse


def tipo_documento_response(t: TipoDocumento) -> TipoDocumentoResponse:
    return TipoDocumentoResponse(
        id=t.id, nombre=t.nombre, sigla=t.sigla, estado=t.estado
    )
