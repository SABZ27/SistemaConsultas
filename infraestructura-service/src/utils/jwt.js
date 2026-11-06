const jwt = require('jsonwebtoken');

const env = require('../config/env');
const { noAutorizado } = require('./errores');

function extraerToken(req) {
  const header = req.headers.authorization || '';
  if (!header.toLowerCase().startsWith('bearer ')) {
    return null;
  }
  return header.slice(7).trim();
}

function verificarToken(token) {
  if (!env.jwtSecret) {
    throw noAutorizado('El servicio no tiene configurado JWT_SECRET.');
  }

  // Solo HS256 y exp obligatorio: un token sin caducidad no es aceptable.
  const payload = jwt.verify(token, env.jwtSecret, { algorithms: ['HS256'] });
  if (typeof payload.exp !== 'number') {
    throw noAutorizado('Token inválido o expirado.');
  }
  return payload;
}

module.exports = { extraerToken, verificarToken };
