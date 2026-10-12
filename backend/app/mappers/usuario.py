from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioResponse


def usuario_response(u: Usuario) -> UsuarioResponse:
    programa = u.programa
    tipo_documento = u.tipo_documento
    return UsuarioResponse(
        id=u.id,
        identificacion=u.identificacion,
        nombre=u.nombre,
        apellido=u.apellido,
        correo=u.correo,
        rol=u.rol,
        programaId=programa.id if programa else None,
        programaNombre=programa.nombre if programa else None,
        tipoDocumentoId=tipo_documento.id if tipo_documento else None,
        tipoDocumentoSigla=tipo_documento.sigla if tipo_documento else None,
        tipoDocumentoNombre=tipo_documento.nombre if tipo_documento else None,
        estado=u.estado,
        fechaCreacion=u.creado,
    )


def nombre_completo(u: Usuario) -> str:
    return f"{u.nombre} {u.apellido}"