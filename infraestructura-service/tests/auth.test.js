const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, mockFetch, respuestaJson, pool } = require('./helpers');
const { FESTIVOS_CO_2026 } = require('./fixtures/nagerCo2026');

const app = crearApp();

// Las pruebas nunca salen a la red: el proveedor siempre esta simulado.
beforeEach(async () => {
  mockFetch(async () => respuestaJson(200, FESTIVOS_CO_2026));
  await limpiarTablas();
});
afterAll(async () => {
  await pool.end();
});

describe('autenticación y health', () => {
  test('GET /health responde sin autenticación', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok', servicio: 'infraestructura' });
  });

  test('GET /servicios-externos sin token responde 401 con formato FastAPI', async () => {
    const res = await request(app).get('/servicios-externos');
    expect(res.status).toBe(401);
    expect(res.body).toMatchObject({ status: 401, error: 'Unauthorized' });
    expect(typeof res.body.timestamp).toBe('string');
    expect(res.body).toHaveProperty('message');
    expect(res.body).toHaveProperty('errors');
  });

  test('GET /servicios-externos con token inválido responde 401', async () => {
    const res = await request(app)
      .get('/servicios-externos')
      .set('Authorization', 'Bearer no-es-un-token');
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Unauthorized');
  });

  test('GET /servicios-externos con token válido responde 200', async () => {
    const res = await request(app).get('/servicios-externos').set(auth());
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });

  test('GET /festivos sin token responde 401', async () => {
    const res = await request(app).get('/festivos?anio=2026');
    expect(res.status).toBe(401);
  });

  test('GET /festivos con token válido responde 200', async () => {
    const res = await request(app).get('/festivos?anio=2026').set(auth());
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });

  test('GET /festivos con año inválido responde 400 con errors', async () => {
    const res = await request(app).get('/festivos?anio=abc').set(auth());
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Bad Request');
    expect(res.body.errors).toHaveProperty('anio');
  });

  test('GET /festivos/validar con fecha inválida responde 400 con errors', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-13-99').set(auth());
    expect(res.status).toBe(400);
    expect(res.body.errors).toHaveProperty('fecha');
  });

  test('POST /correos sin token responde 401', async () => {
    const res = await request(app)
      .post('/correos')
      .send({ para: 'a@b.com', asunto: 'Prueba', contenido: 'Hola' });
    expect(res.status).toBe(401);
  });
});
