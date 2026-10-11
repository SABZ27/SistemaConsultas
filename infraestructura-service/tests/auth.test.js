const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('autenticación y health', () => {
  test('GET /health responde sin autenticación', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok', servicio: 'infraestructura' });
  });

  test('GET /sedes sin token responde 401 con formato FastAPI', async () => {
    const res = await request(app).get('/sedes');
    expect(res.status).toBe(401);
    expect(res.body).toMatchObject({ status: 401, error: 'Unauthorized' });
    expect(typeof res.body.timestamp).toBe('string');
    expect(res.body).toHaveProperty('message');
    expect(res.body).toHaveProperty('errors');
  });

  test('GET /sedes con token inválido responde 401', async () => {
    const res = await request(app).get('/sedes').set('Authorization', 'Bearer no-es-un-token');
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Unauthorized');
  });

  test('GET /sedes con token válido sin INFRAESTRUCTURA responde 200', async () => {
    const res = await request(app).get('/sedes').set(auth([]));
    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  test('POST /sedes sin INFRAESTRUCTURA responde 403', async () => {
    const res = await request(app)
      .post('/sedes')
      .set(auth([]))
      .send({ nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    expect(res.status).toBe(403);
    expect(res.body).toMatchObject({ status: 403, error: 'Forbidden' });
  });

  test('POST /sedes con INFRAESTRUCTURA responde 201', async () => {
    const res = await request(app)
      .post('/sedes')
      .set(auth())
      .send({ nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    expect(res.status).toBe(201);
    expect(res.body).toMatchObject({
      nombre: 'Sede Norte',
      tipoEstructura: 'SALONES',
      estado: true,
    });
  });

  test('POST /sedes con validación inválida responde 400 con errors', async () => {
    const res = await request(app)
      .post('/sedes')
      .set(auth())
      .send({ nombre: 'X', tipoEstructura: 'OTRA' });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Bad Request');
    expect(res.body.errors).toHaveProperty('nombre');
    expect(res.body.errors).toHaveProperty('tipoEstructura');
  });
});
