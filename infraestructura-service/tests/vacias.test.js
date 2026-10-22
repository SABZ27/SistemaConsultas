const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, mockFetch, respuestaJson, pool } = require('./helpers');

const app = crearApp();

beforeEach(async () => {
  mockFetch(async () => respuestaJson(200, []));
  await limpiarTablas();
});

afterAll(async () => {
  await pool.end();
});

describe('respuestas vacías', () => {
  test('el listado de festivos devuelve un arreglo vacío', async () => {
    const res = await request(app).get('/festivos?anio=2026').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  test('una fecha sin festivo responde esFestivo false', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-02-10').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ esFestivo: false, nombre: null });
  });

  test('GET de un festivo inexistente responde 404', async () => {
    const res = await request(app).delete('/festivos/999').set(auth());
    expect(res.status).toBe(404);
    expect(res.body.error).toBe('Not Found');
  });
});
