const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('tablas vacías', () => {
  test('los listados devuelven arreglos vacíos', async () => {
    const sedes = await request(app).get('/sedes').set(auth([]));
    const zonas = await request(app).get('/zonas').set(auth([]));
    const recursos = await request(app).get('/recursos-fisicos').set(auth([]));

    expect(sedes.status).toBe(200);
    expect(zonas.status).toBe(200);
    expect(recursos.status).toBe(200);
    expect(sedes.body).toEqual([]);
    expect(zonas.body).toEqual([]);
    expect(recursos.body).toEqual([]);
  });

  test('GET de un recurso inexistente responde 404', async () => {
    const res = await request(app).get('/sedes/999').set(auth([]));
    expect(res.status).toBe(404);
    expect(res.body.error).toBe('Not Found');
  });
});
