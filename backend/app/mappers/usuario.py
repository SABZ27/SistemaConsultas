from app.models.usuario import Usuario
from app.models.enums import Rol
from app.schemas.usuario import UsuarioResponse


def usuario_response(
    u: Usuario, usuario_actual: Usuario | None = None
) -> UsuarioResponse:
    """Enmascara identificación y correo salvo para el propio usuario o admin.

    Los campos siguen en el contrato, con valor ``None`` cuando el rol que
    consulta no debe verlos.
    """
    programa = u.programa
    tipo_documento = u.tipo_documento
    es_admin = usuario_actual is not None and usuario_actual.rol == Rol.ADMINISTRADOR
    puede_ver = es_admin or (
        usuario_actual is not None and usuario_actual.id == u.id
    )
    return UsuarioResponse(
        id=u.id,
        identificacion=u.identificacion if puede_ver else None,
        nombre=u.nombre,
        apellido=u.apellido,
        correo=u.correo if puede_ver else None,
        rol=u.rol,
        programaId=programa.id if programa else None,
        programaNombre=programa.nombre if programa else None,
        tipoDocumentoId=tipo_documento.id if tipo_documento else None,
        tipoDocumentoSigla=tipo_documento.sigla if tipo_documento else None,
        tipoDocumentoNombre=tipo_documento.nombre if tipo_documento else None,
        estado=u.estado,
        fechaCreacion=u.creado,
        fechaActualizacion=u.actualizado,
    )


def nombre_completo(u: Usuario) -> str:
    return f"{u.nombre} {u.apellido}"
