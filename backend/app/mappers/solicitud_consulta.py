from app.models.solicitud_consulta import SolicitudConsulta
from app.models.usuario import Usuario
from app.models.enums import Rol
from app.mappers.usuario import nombre_completo
from app.schemas.solicitud import SolicitudConsultaResponse


def solicitud_consulta_response(
    s: SolicitudConsulta, usuario_actual: Usuario | None = None
) -> SolicitudConsultaResponse:
    """Enmascara la identificación de la otra parte según quién consulta.

    Cada participante ve solo su propia identificación; el administrador ve
    ambas; cualquier otro usuario autenticado no ve ninguna. Los campos siguen
    en el contrato, con valor ``None`` cuando no corresponden.
    """
    estudiante = s.estudiante
    docente = s.docente
    modulo = s.modulo
    programa = estudiante.programa if estudiante else None

    es_admin = usuario_actual is not None and usuario_actual.rol == Rol.ADMINISTRADOR
    id_actual = usuario_actual.id if usuario_actual is not None else None
    ve_estudiante = es_admin or (
        estudiante is not None and id_actual == estudiante.id
    )
    ve_docente = es_admin or (docente is not None and id_actual == docente.id)

    return SolicitudConsultaResponse(
        id=s.id,
        numeroConsulta=s.numero_consulta,
        estado=s.estado_consulta,
        prioridad=s.prioridad,
        asunto=s.asunto,
        descripcion=s.descripcion,
        fechaCreacion=s.creado,
        fechaConsulta=s.fecha_consulta,
        horaConsulta=s.hora_consulta,
        estudianteId=estudiante.id,
        identificacionEstudiante=(
            estudiante.identificacion if ve_estudiante else None
        ),
        nombreCompletoEstudiante=nombre_completo(estudiante),
        docenteId=docente.id,
        identificacionDocente=(docente.identificacion if ve_docente else None),
        nombreCompletoDocente=nombre_completo(docente),
        moduloId=modulo.id,
        nombreModulo=modulo.nombre,
        nombrePrograma=programa.nombre if programa else "Sin programa",
        recursoFisicoId=s.recurso_fisico_id,
        nombreRecursoFisico=s.recurso_fisico_nombre or "Sin asignar",
    )
