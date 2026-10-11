const { AppError, cuerpoError } = require('../utils/errores');

function notFoundHandler(_req, res) {
  res.status(404).json(cuerpoError(404, 'Recurso no encontrado.'));
}

// eslint-disable-next-line no-unused-vars
function errorHandler(error, _req, res, _next) {
  if (error instanceof AppError) {
    return res.status(error.status).json(cuerpoError(error.status, error.message, error.errors));
  }
  if (error && error.code === 'ER_DUP_ENTRY') {
    return res
      .status(400)
      .json(cuerpoError(400, 'Ya existe un registro con el mismo valor único.'));
  }
  if (error && error.type === 'entity.parse.failed') {
    return res.status(400).json(cuerpoError(400, 'El cuerpo de la solicitud no es un JSON válido.'));
  }
  console.error('Error no controlado:', error);
  return res.status(500).json(cuerpoError(500, 'Error interno del servidor.'));
}

module.exports = { notFoundHandler, errorHandler };
