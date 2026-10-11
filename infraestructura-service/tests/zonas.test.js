const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, crearSede, crearZona, crearRecurso, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('CRUD de zonas', () => {
  test('crea una zona en una sede BLOQUES/PISOS', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    const zona = await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });
    expect(zona).toMatchObject({ nombre: 'Bloque A', sedeId: sede.id, sedeNombre: 'Sede Principal', estado: true });
  });

  test('rechaza crear zonas en una sede SALONES', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Salones', tipoEstructura: 'SALONES' });
    const res = await request(app).post('/zonas').set(auth()).send({ sedeId: sede.id, nombre: 'Bloque A' });
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/SALONES/i);
  });

  test('rechaza crear una zona en una sede inexistente', async () => {
    const res = await request(app).post('/zonas').set(auth()).send({ sedeId: 999, nombre: 'Bloque A' });
    expect(res.status).toBe(404);
  });

  test('no permite dos zonas activas con el mismo nombre en la sede', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });
    const res = await request(app).post('/zonas').set(auth()).send({ sedeId: sede.id, nombre: 'Bloque A' });
    expect(res.status).toBe(400);
  });

  test('get /sedes/:id/zonas devuelve 404 si la sede no existe', async () => {
    const res = await request(app).get('/sedes/999/zonas').set(auth([]));
    expect(res.status).toBe(404);
  });

  test('no desactiva una zona con recursos activos', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    const zona = await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });
    await crearRecurso(app, { sedeId: sede.id, zonaId: zona.id, nombre: 'Salón 1' });

    const res = await request(app).delete(`/zonas/${zona.id}`).set(auth());
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/recursos/i);
  });

  test('lista zonas anidadas por sede', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'PISOS' });
    await crearZona(app, { sedeId: sede.id, nombre: 'Piso 1' });
    await crearZona(app, { sedeId: sede.id, nombre: 'Piso 2' });

    const res = await request(app).get(`/sedes/${sede.id}/zonas`).set(auth([]));
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
  });
});
