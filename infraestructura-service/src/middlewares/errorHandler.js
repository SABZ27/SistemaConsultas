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
  if (error && (error.type === 'entity.too.large' || error.status === 413)) {
    return res
      .status(413)
      .json(cuerpoError(413, 'El cuerpo de la solicitud es demasiado grande.'));
  }

  // Solo el tipo: el mensaje podria contener correos, tokens o contenidos.
  const tipo = error && error.name ? error.name : 'Error';
  console.error('Error no controlado (%s).', tipo);
  return res.status(500).json(cuerpoError(500, 'Error interno del servidor.'));
}

module.exports = { notFoundHandler, errorHandler };
