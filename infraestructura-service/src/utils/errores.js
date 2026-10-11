const NOMBRE_ERROR = {
  400: 'Bad Request',
  401: 'Unauthorized',
  403: 'Forbidden',
  404: 'Not Found',
  405: 'Method Not Allowed',
  409: 'Conflict',
  422: 'Unprocessable Entity',
  500: 'Internal Server Error',
};

class AppError extends Error {
  constructor(status, message, errors = null) {
    super(message);
    this.name = 'AppError';
    this.status = status;
    this.errors = errors;
  }
}

const noEncontrado = (message = 'Recurso no encontrado.') => new AppError(404, message);
const solicitudInvalida = (message, errors = null) => new AppError(400, message, errors);
const noAutorizado = (message = 'No se encontró una sesión activa.') => new AppError(401, message);
const prohibido = (message = 'No tiene permisos para realizar esta acción.') => new AppError(403, message);

function cuerpoError(status, message, errors = null) {
  return {
    timestamp: new Date().toISOString(),
    status,
    error: NOMBRE_ERROR[status] || 'Error',
    message,
    errors,
  };
}

function traducirDuplicado(error, mensaje) {
  if (error && error.code === 'ER_DUP_ENTRY') {
    return solicitudInvalida(mensaje);
  }
  return error;
}

module.exports = {
  NOMBRE_ERROR,
  AppError,
  noEncontrado,
  solicitudInvalida,
  noAutorizado,
  prohibido,
  cuerpoError,
  traducirDuplicado,
};
