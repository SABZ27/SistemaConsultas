const { extraerToken, verificarToken } = require('../utils/jwt');
const { noAutorizado, prohibido } = require('../utils/errores');
const { incluirInactivos } = require('../utils/query');

const MODULO_INFRAESTRUCTURA = 'INFRAESTRUCTURA';

function autenticar(req, _res, next) {
  const token = extraerToken(req);
  if (!token) {
    return next(noAutorizado('No se encontró una sesión activa.'));
  }
  try {
    req.usuario = verificarToken(token);
  } catch (error) {
    if (error.name === 'AppError') {
      return next(error);
    }
    return next(noAutorizado('Token inválido o expirado.'));
  }
  return next();
}

function tieneInfraestructura(req) {
  const modulos = req.usuario && Array.isArray(req.usuario.modulos) ? req.usuario.modulos : [];
  return modulos.includes(MODULO_INFRAESTRUCTURA);
}

function requiereInfraestructura(req, _res, next) {
  if (!tieneInfraestructura(req)) {
    return next(prohibido());
  }
  return next();
}

function requiereInfraestructuraSiInactivos(req, _res, next) {
  if (incluirInactivos(req) && !tieneInfraestructura(req)) {
    return next(prohibido());
  }
  return next();
}

module.exports = {
  autenticar,
  requiereInfraestructura,
  requiereInfraestructuraSiInactivos,
  MODULO_INFRAESTRUCTURA,
};
