const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, crearSede, crearZona, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('CRUD de sedes', () => {
  test('crear, obtener, actualizar y listar', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });

    const obtener = await request(app).get(`/sedes/${sede.id}`).set(auth([]));
    expect(obtener.status).toBe(200);
    expect(obtener.body.nombre).toBe('Sede Norte');

    const actualizar = await request(app)
      .put(`/sedes/${sede.id}`)
      .set(auth())
      .send({ nombre: 'Sede Norte Renombrada', tipoEstructura: 'SALONES' });
    expect(actualizar.status).toBe(200);
    expect(actualizar.body.nombre).toBe('Sede Norte Renombrada');

    const listar = await request(app).get('/sedes').set(auth([]));
    expect(listar.body).toHaveLength(1);
  });

  test('no permite dos sedes activas con el mismo nombre', async () => {
    await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    const res = await request(app)
      .post('/sedes')
      .set(auth())
      .send({ nombre: 'Sede Norte', tipoEstructura: 'BLOQUES' });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Bad Request');
  });

  test('no cambia el tipo de estructura si la sede tiene zonas activas', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });

    const res = await request(app)
      .put(`/sedes/${sede.id}`)
      .set(auth())
      .send({ nombre: 'Sede Principal', tipoEstructura: 'SALONES' });
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/tipo de estructura/i);
  });

  test('no desactiva una sede con zonas activas', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });

    const res = await request(app).delete(`/sedes/${sede.id}`).set(auth());
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/zonas activas/i);
  });

  test('no desactiva una sede con recursos activos', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Salones', tipoEstructura: 'SALONES' });
    await request(app)
      .post('/recursos-fisicos')
      .set(auth())
      .send({ sedeId: sede.id, nombre: 'Salón 1' });

    const res = await request(app).delete(`/sedes/${sede.id}`).set(auth());
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/recursos/i);
  });

  test('cambia el tipo de estructura cuando no hay hijos activos', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Cambiable', tipoEstructura: 'BLOQUES' });
    const res = await request(app)
      .put(`/sedes/${sede.id}`)
      .set(auth())
      .send({ nombre: 'Sede Cambiable', tipoEstructura: 'PISOS' });
    expect(res.status).toBe(200);
    expect(res.body.tipoEstructura).toBe('PISOS');
  });

  test('incluir_inactivos requiere INFRAESTRUCTURA', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    await request(app).delete(`/sedes/${sede.id}`).set(auth());

    const sinPermiso = await request(app).get('/sedes?incluir_inactivos=true').set(auth([]));
    expect(sinPermiso.status).toBe(403);

    const conPermiso = await request(app).get('/sedes?incluir_inactivos=true').set(auth());
    expect(conPermiso.status).toBe(200);
    expect(conPermiso.body).toHaveLength(1);
    expect(conPermiso.body[0].estado).toBe(false);
  });

  test('GET /sedes/:id/estructura responde 404 si la sede no existe', async () => {
    const res = await request(app).get('/sedes/999/estructura').set(auth([]));
    expect(res.status).toBe(404);
  });
});
