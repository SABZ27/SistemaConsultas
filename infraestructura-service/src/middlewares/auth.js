const { extraerToken, verificarToken } = require('../utils/jwt');
const { noAutorizado, prohibido } = require('../utils/errores');

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

// Exige que el token tenga el rol indicado (por ejemplo ADMINISTRADOR).
function requiereRol(rol) {
  return (req, _res, next) => {
    const rolUsuario = req.usuario ? req.usuario.rol : null;
    if (rolUsuario !== rol) {
      return next(prohibido());
    }
    return next();
  };
}

module.exports = { autenticar, requiereRol };
