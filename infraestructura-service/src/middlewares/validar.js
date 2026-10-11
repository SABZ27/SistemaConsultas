const { solicitudInvalida } = require('../utils/errores');

function validar(schema, fuente = 'body') {
  return (req, _res, next) => {
    const datos = req[fuente] ?? {};
    const resultado = schema.safeParse(datos);
    if (!resultado.success) {
      const errors = {};
      for (const issue of resultado.error.issues) {
        const campo = issue.path.join('.') || 'cuerpo';
        if (!errors[campo]) {
          errors[campo] = issue.message;
        }
      }
      return next(solicitudInvalida('Error de validación.', errors));
    }
    req.datos = resultado.data;
    return next();
  };
}

module.exports = { validar };
