OBLIGATORIOS = {
    "identificacion": "La identificación es obligatoria",
    "nombre": "El nombre es obligatorio",
    "apellido": "El apellido es obligatorio",
    "correo": "El correo es obligatorio",
    "password": "La contraseña es obligatoria",
    "rol": "El rol es obligatorio",
    "token": "El token es obligatorio",
    "nuevaPassword": "La nueva contraseña es obligatoria",
    "asunto": "El asunto es obligatorio.",
    "descripcion": "La descripción no puede estar vacía",
    "docenteId": "El ID del docente es obligatorio.",
    "moduloId": "El ID del módulo es obligatorio.",
    "recursoFisicoId": "El ID del recurso es obligatorio.",
    "contenido": "El comentario debe tener contenido.",
    "solicitudConsultaId": "La solicitud de consultas es obligatoria.",
    "titulo": "La notificación debe tener un título.",
    "mensaje": "La notificación debe tener un mensaje.",
    "remitenteId": "La notificación debe tener un remitente.",
    "destinatarioId": "La notificación debe tener un destinatario.",
}

TAMANOS = {
    "identificacion": "La identificación no puede superar los 20 caracteres",
    "nombre": "El nombre no puede superar los 100 caracteres",
    "apellido": "El apellido no puede superar los 100 caracteres",
    "password": "La contraseña debe tener entre 8 y 100 caracteres",
    "nuevaPassword": "La contraseña debe tener entre 8 y 100 caracteres",
    "asunto": "El asunto debe tener entre 1 y 100 caracteres.",
    "descripcion_modulo": "La descripcion debe tener entre 10 y 500 caracteres",
    "nombre_programa": "El nombre debe tener entre 4 y 100 caracteres",
    "nombre_modulo": "El nombre debe tener entre 3 y 100 caracteres",
    "nombre_sede": "El nombre debe tener entre 3 y 100 caracteres.",
    "nombre_bloque": "El nombre debe tener entre 1 y 100 caracteres.",
    "nombre_rf": "El nombre debe tener entre 1 y 100 caracteres.",
}

EMAIL_INVALIDO = {
    "correo": "El correo no tiene un formato válido",
    "correo_forgot": "Debe ingresar un correo válido",
}


def etiqueta_campo(campo: str) -> str:
    etiquetas = {
        "identificacion": "La identificación",
        "nombre": "El nombre",
        "apellido": "El apellido",
        "correo": "El correo",
        "password": "La contraseña",
        "nuevaPassword": "La nueva contraseña",
        "rol": "El rol",
        "asunto": "El asunto",
        "descripcion": "La descripción",
        "docenteId": "El ID del docente",
        "moduloId": "El ID del módulo",
        "recursoFisicoId": "El ID del recurso",
        "contenido": "El contenido",
        "solicitudConsultaId": "La solicitud de consultas",
        "estado": "El estado",
        "prioridad": "La prioridad",
        "fechaConsulta": "La fecha de la consulta",
        "horaConsulta": "La hora de la consulta",
        "token": "El token",
    }
    return etiquetas.get(campo, f"El campo {campo}")