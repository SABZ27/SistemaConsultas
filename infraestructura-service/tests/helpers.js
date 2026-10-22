const jwt = require('jsonwebtoken');
const request = require('supertest');

const pool = require('../src/config/database');

const SERVICIOS = [
  {
    nombre: 'Nager.Date',
    url_base: 'https://date.nager.at/api/v4',
    descripcion: 'API pública de festivos por país',
  },
  {
    nombre: 'Brevo',
    url_base: 'https://api.brevo.com/v3',
    descripcion: 'API de correo transaccional',
  },
];

function token(opciones = {}) {
  const payload = {
    sub: opciones.sub || 'usuario@test.com',
    uid: opciones.uid || 1,
    rol: opciones.rol || 'ADMINISTRADOR',
    modulos: opciones.modulos || ['INFRAESTRUCTURA'],
  };
  return jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '30m' });
}

function auth(modulos = ['INFRAESTRUCTURA'], rol = 'ADMINISTRADOR') {
  return { Authorization: `Bearer ${token({ modulos, rol })}` };
}

// Los proveedores externos se buscan por nombre, asi que la semilla debe
// existir siempre que se prueba.
async function sembrarServicios() {
  for (const servicio of SERVICIOS) {
    await pool.query(
      `INSERT INTO servicios_externos (nombre, url_base, descripcion, estado)
       VALUES (?, ?, ?, 1)
       ON DUPLICATE KEY UPDATE url_base = VALUES(url_base), descripcion = VALUES(descripcion), estado = 1`,
      [servicio.nombre, servicio.url_base, servicio.descripcion]
    );
  }
}

async function limpiarTablas() {
  await pool.query('SET FOREIGN_KEY_CHECKS = 0');
  await pool.query('TRUNCATE TABLE correos_enviados');
  await pool.query('TRUNCATE TABLE festivos');
  await pool.query('TRUNCATE TABLE consultas_servicio_externo');
  await pool.query('TRUNCATE TABLE servicios_externos');
  await pool.query('SET FOREIGN_KEY_CHECKS = 1');
  await sembrarServicios();
}

// Respuesta minima que imita la de fetch: solo se usa ok, status y text().
function respuestaJson(status, datos) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => (datos === undefined ? '' : JSON.stringify(datos)),
  };
}

// Instala un mock de fetch (las pruebas nunca salen a la red).
function mockFetch(impl) {
  const spy = jest.fn(impl);
  global.fetch = spy;
  return spy;
}

module.exports = {
  token,
  auth,
  limpiarTablas,
  sembrarServicios,
  SERVICIOS,
  respuestaJson,
  mockFetch,
  pool,
};
