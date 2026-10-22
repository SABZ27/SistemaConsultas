const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('GET /servicios-externos', () => {
  test('lista los proveedores activos', async () => {
    const res = await request(app).get('/servicios-externos').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
    expect(res.body.map((s) => s.nombre).sort()).toEqual(['Brevo', 'Nager.Date']);

    const nager = res.body.find((s) => s.nombre === 'Nager.Date');
    expect(nager.urlBase).toBe('https://date.nager.at/api/v4');
    expect(nager.descripcion).toBe('API pública de festivos por país');

    const brevo = res.body.find((s) => s.nombre === 'Brevo');
    expect(brevo.urlBase).toBe('https://api.brevo.com/v3');
    expect(brevo.descripcion).toBe('API de correo transaccional');
  });

  test('no expone la clave de API del proveedor', async () => {
    const res = await request(app).get('/servicios-externos').set(auth());

    expect(JSON.stringify(res.body)).not.toContain('apiKey');
    expect(JSON.stringify(res.body)).not.toContain('api_key');
  });

  test('un proveedor desactivado no aparece en el listado', async () => {
    await pool.query('UPDATE servicios_externos SET estado = 0 WHERE nombre = ?', ['Brevo']);

    const res = await request(app).get('/servicios-externos').set(auth());

    expect(res.status).toBe(200);
    expect(res.body.map((s) => s.nombre)).toEqual(['Nager.Date']);
  });
});
