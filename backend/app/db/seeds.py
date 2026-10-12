import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.enums import Rol
from app.models.modulo_sistema import ModuloSistema
from app.models.modulo_x_rol import ModuloXRol
from app.models.rol import Rol as RolEntidad
from app.models.usuario import Usuario
from app.repositories.modulo_sistema import ModuloSistemaRepository
from app.repositories.modulo_x_rol import ModuloXRolRepository
from app.repositories.rol import RolRepository
from app.repositories.usuario import UsuarioRepository
from app.repositories.tipo_documento import TipoDocumentoRepository
from app.models.tipo_documento import TipoDocumento
from app.repositories.periodo_academico import PeriodoAcademicoRepository
from app.models.periodo_academico import PeriodoAcademico
from datetime import date

logger = logging.getLogger("sistema_consultas.db")

NOMBRES_ROLES = [rol.value for rol in Rol]

MODULOS_SISTEMA = {
    "DASHBOARD": {"descripcion": "Panel principal", "ruta": "/dashboard", "icono": "dashboard"},
    "PERFIL": {"descripcion": "Datos del perfil propio", "ruta": "/perfil", "icono": "person"},
    "NOTIFICACIONES": {"descripcion": "Centro de notificaciones", "ruta": "/notificaciones", "icono": "notifications"},
    "MIS_SOLICITUDES": {"descripcion": "Solicitudes de consulta propias", "ruta": "/mis-solicitudes", "icono": "assignment"},
    "ATENCION_SOLICITUDES": {"descripcion": "Atención de solicitudes asignadas", "ruta": "/atender-solicitudes", "icono": "support_agent"},
    "GESTION_SOLICITUDES": {"descripcion": "Gestión global de solicitudes", "ruta": "/solicitudes", "icono": "manage_search"},
    "USUARIOS": {"descripcion": "Administración de usuarios", "ruta": "/usuarios", "icono": "group"},
    "ROLES_PERMISOS": {"descripcion": "Administración de roles y permisos", "ruta": "/roles-permisos", "icono": "security"},
    "PROGRAMAS_ASIGNATURAS": {"descripcion": "Programas académicos y asignaturas", "ruta": "/programas-asignaturas", "icono": "school"},
    "INFRAESTRUCTURA": {"descripcion": "Administración de infraestructura física", "ruta": "/infraestructura", "icono": "location_on"},
    "ASIGNACION_DOCENTES": {"descripcion": "Asignación de docentes a módulos", "ruta": "/asignacion-docentes", "icono": "assignment_ind"},
    "PERIODOS_ACADEMICOS": {"descripcion": "Periodos académicos", "ruta": "/periodos-academicos", "icono": "event"},
    "TIPOS_DOCUMENTO": {"descripcion": "Tipos de documento de identidad", "ruta": "/tipos-documento", "icono": "badge"},
    "DISPONIBILIDAD_DOCENTE": {"descripcion": "Disponibilidad horaria de docentes", "ruta": "/disponibilidad-docente", "icono": "schedule"},
    "CALIFICACIONES": {"descripcion": "Calificaciones de consultas", "ruta": "/calificaciones", "icono": "star"},
}

MATRIZ_MODULOS_X_ROL = {
    "DASHBOARD": {Rol.ADMINISTRADOR, Rol.DOCENTE, Rol.ESTUDIANTE},
    "PERFIL": {Rol.ADMINISTRADOR, Rol.DOCENTE, Rol.ESTUDIANTE},
    "NOTIFICACIONES": {Rol.ADMINISTRADOR, Rol.DOCENTE, Rol.ESTUDIANTE},
    "MIS_SOLICITUDES": {Rol.ESTUDIANTE},
    "ATENCION_SOLICITUDES": {Rol.DOCENTE},
    "GESTION_SOLICITUDES": {Rol.ADMINISTRADOR},
    "USUARIOS": {Rol.ADMINISTRADOR},
    "ROLES_PERMISOS": {Rol.ADMINISTRADOR},
    "PROGRAMAS_ASIGNATURAS": {Rol.ADMINISTRADOR},
    "INFRAESTRUCTURA": {Rol.ADMINISTRADOR},
    "ASIGNACION_DOCENTES": {Rol.ADMINISTRADOR},
    "PERIODOS_ACADEMICOS": {Rol.ADMINISTRADOR},
    "TIPOS_DOCUMENTO": {Rol.ADMINISTRADOR},
    "DISPONIBILIDAD_DOCENTE": {Rol.ADMINISTRADOR, Rol.DOCENTE},
    "CALIFICACIONES": {Rol.ADMINISTRADOR, Rol.DOCENTE, Rol.ESTUDIANTE},
}


def _sembrar_tipos_documento(db: Session) -> None:
    repo = TipoDocumentoRepository(db)
    datos = [
        ("Cédula de Ciudadanía", "CC"),
        ("Tarjeta de Identidad", "TI"),
        ("Cédula de Extranjería", "CE"),
        ("Pasaporte", "PAS"),
    ]
    for nombre, sigla in datos:
        if repo.find_by_nombre_and_estado_true(nombre) is None and repo.find_by_sigla_and_estado_true(sigla) is None:
            repo.save(TipoDocumento(nombre=nombre, sigla=sigla))


def _sembrar_periodo_vigente(db: Session) -> None:
    repo = PeriodoAcademicoRepository(db)
    year = date.today().year
    nombre = f"{year}-1"
    inicio = date(year, 1, 1)
    fin = date(year, 12, 31)
    if repo.find_by_nombre_and_estado_true(nombre) is None:
        if repo.existe_solape(inicio, fin):
            return
        repo.save(PeriodoAcademico(nombre=nombre, fecha_inicio=inicio, fecha_fin=fin))


def _sembrar_roles(db: Session) -> None:
    repo = RolRepository(db)
    for nombre in NOMBRES_ROLES:
        if repo.find_by_nombre(nombre) is None:
            repo.save(RolEntidad(nombre=nombre))


def _sembrar_modulos_sistema(db: Session) -> None:
    repo = ModuloSistemaRepository(db)
    for nombre, datos in MODULOS_SISTEMA.items():
        if repo.find_by_nombre(nombre) is None:
            repo.save(ModuloSistema(nombre=nombre, **datos))


def _sembrar_modulos_x_rol(db: Session) -> None:
    rol_repo = RolRepository(db)
    modulo_repo = ModuloSistemaRepository(db)
    repo = ModuloXRolRepository(db)
    for nombre_modulo, roles in MATRIZ_MODULOS_X_ROL.items():
        modulo = modulo_repo.find_by_nombre(nombre_modulo)
        if modulo is None:
            continue
        for rol_enum in roles:
            rol = rol_repo.find_by_nombre(rol_enum.value)
            if rol is None:
                continue
            if repo.find_by_rol_and_modulo(rol.id, modulo.id) is None:
                repo.save(ModuloXRol(rol_id=rol.id, modulo_id=modulo.id))


def _sembrar_admin(db: Session) -> None:
    if not (settings.admin_correo and settings.admin_password and settings.admin_identificacion):
        logger.warning(
            "No se sembró el administrador inicial: faltan las variables "
            "ADMIN_CORREO/ADMIN_PASSWORD/ADMIN_IDENTIFICACION en el entorno."
        )
        return

    user_repo = UsuarioRepository(db)
    if user_repo.find_admin_activo() is not None:
        return

    rol_repo = RolRepository(db)
    rol_admin = rol_repo.find_by_nombre_and_estado_true(Rol.ADMINISTRADOR.value)
    if rol_admin is None:
        return

    user_repo.save(
        Usuario(
            identificacion=settings.admin_identificacion,
            nombre="Administrador",
            apellido="Sistema",
            correo=settings.admin_correo,
            password=hash_password(settings.admin_password),
            rol_id=rol_admin.id,
        )
    )
    logger.info("Administrador inicial sembrado correctamente.")


def ejecutar_seeds(db: Session) -> None:
    _sembrar_roles(db)
    _sembrar_modulos_sistema(db)
    _sembrar_modulos_x_rol(db)
    _sembrar_admin(db)
    _sembrar_tipos_documento(db)
    _sembrar_periodo_vigente(db)