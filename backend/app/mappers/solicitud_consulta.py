from app.models.solicitud_consulta import SolicitudConsulta
from app.mappers.usuario import nombre_completo
from app.schemas.solicitud import SolicitudConsultaResponse


def solicitud_consulta_response(s: SolicitudConsulta) -> SolicitudConsultaResponse:
    estudiante = s.estudiante
    docente = s.docente
    modulo = s.modulo
    recurso = s.recurso_fisico
    programa = estudiante.programa if estudiante else None
    return SolicitudConsultaResponse(
        id=s.id,
        numeroConsulta=s.numero_consulta,
        estado=s.estado,
        prioridad=s.prioridad,
        asunto=s.asunto,
        descripcion=s.descripcion,
        fechaCreacion=s.fecha_creacion,
        fechaConsulta=s.fecha_consulta,
        horaConsulta=s.hora_consulta,
        estudianteId=estudiante.id,
        identificacionEstudiante=estudiante.identificacion,
        nombreCompletoEstudiante=nombre_completo(estudiante),
        docenteId=docente.id,
        identificacionDocente=docente.identificacion,
        nombreCompletoDocente=nombre_completo(docente),
        moduloId=modulo.id,
        nombreModulo=modulo.nombre,
        nombrePrograma=programa.nombre if programa else "Sin programa",
        recursoFisicoId=recurso.id if recurso else None,
        nombreRecursoFisico=recurso.nombre if recurso else "Sin asignar",
    )