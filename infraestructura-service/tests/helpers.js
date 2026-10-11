const jwt = require('jsonwebtoken');
const request = require('supertest');

const pool = require('../src/config/database');

function token(opciones = {}) {
  const payload = {
    sub: opciones.sub || 'usuario@test.com',
    uid: opciones.uid || 1,
    rol: opciones.rol || 'ADMINISTRADOR',
    modulos: opciones.modulos || ['INFRAESTRUCTURA'],
  };
  return jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '30m' });
}

function auth(modulos = ['INFRAESTRUCTURA']) {
  return { Authorization: `Bearer ${token({ modulos })}` };
}

async function limpiarTablas() {
  await pool.query('SET FOREIGN_KEY_CHECKS = 0');
  await pool.query('TRUNCATE TABLE recursos_fisicos');
  await pool.query('TRUNCATE TABLE zonas');
  await pool.query('TRUNCATE TABLE sedes');
  await pool.query('SET FOREIGN_KEY_CHECKS = 1');
}

async function crearSede(app, datos, headers = auth()) {
  const res = await request(app).post('/sedes').set(headers).send(datos);
  if (res.status !== 201) {
    throw new Error(`No se pudo crear la sede: ${res.status} ${JSON.stringify(res.body)}`);
  }
  return res.body;
}

async function crearZona(app, datos, headers = auth()) {
  const res = await request(app).post('/zonas').set(headers).send(datos);
  if (res.status !== 201) {
    throw new Error(`No se pudo crear la zona: ${res.status} ${JSON.stringify(res.body)}`);
  }
  return res.body;
}

async function crearRecurso(app, datos, headers = auth()) {
  const res = await request(app).post('/recursos-fisicos').set(headers).send(datos);
  if (res.status !== 201) {
    throw new Error(`No se pudo crear el recurso: ${res.status} ${JSON.stringify(res.body)}`);
  }
  return res.body;
}

module.exports = { token, auth, limpiarTablas, crearSede, crearZona, crearRecurso, pool };
