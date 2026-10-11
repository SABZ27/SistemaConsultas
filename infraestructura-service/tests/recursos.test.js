const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, crearSede, crearZona, crearRecurso, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('CRUD de recursos físicos', () => {
  test('sede BLOQUES exige zonaId', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    const res = await request(app)
      .post('/recursos-fisicos')
      .set(auth())
      .send({ sedeId: sede.id, nombre: 'Salón 1' });
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/zonaId/i);
  });

  test('sede BLOQUES crea el recurso con zona de la misma sede y calcula ubicacion', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    const zona = await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });
    const recurso = await crearRecurso(app, {
      sedeId: sede.id,
      zonaId: zona.id,
      nombre: 'Salón 3',
    });
    expect(recurso.ubicacion).toBe('Sede Principal · Bloque A · Salón 3');
    expect(recurso.tipo).toBe('SALON');
  });

  test('rechaza una zona de otra sede', async () => {
    const sedeA = await crearSede(app, { nombre: 'Sede A', tipoEstructura: 'BLOQUES' });
    const sedeB = await crearSede(app, { nombre: 'Sede B', tipoEstructura: 'BLOQUES' });
    const zonaB = await crearZona(app, { sedeId: sedeB.id, nombre: 'Bloque B' });

    const res = await request(app)
      .post('/recursos-fisicos')
      .set(auth())
      .send({ sedeId: sedeA.id, zonaId: zonaB.id, nombre: 'Salón 3' });
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/no pertenece/i);
  });

  test('sede SALONES no admite zonaId y calcula ubicacion sin zona', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });

    const conZona = await request(app)
      .post('/recursos-fisicos')
      .set(auth())
      .send({ sedeId: sede.id, zonaId: 1, nombre: 'Salón 12' });
    expect(conZona.status).toBe(400);

    const recurso = await crearRecurso(app, { sedeId: sede.id, nombre: 'Salón 12' });
    expect(recurso.zonaId).toBeNull();
    expect(recurso.ubicacion).toBe('Sede Norte · Salón 12');
  });

  test('sede PISOS incluye el piso en la ubicacion', async () => {
    const sede = await crearSede(app, { nombre: 'Granadillo', tipoEstructura: 'PISOS' });
    const piso = await crearZona(app, { sedeId: sede.id, nombre: 'Piso 2' });
    const recurso = await crearRecurso(app, { sedeId: sede.id, zonaId: piso.id, nombre: 'Salón 3' });
    expect(recurso.ubicacion).toBe('Granadillo · Piso 2 · Salón 3');
  });

  test('no permite dos recursos activos con el mismo nombre en sede sin zona', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    await crearRecurso(app, { sedeId: sede.id, nombre: 'Salón 12' });
    const res = await request(app)
      .post('/recursos-fisicos')
      .set(auth())
      .send({ sedeId: sede.id, nombre: 'Salón 12' });
    expect(res.status).toBe(400);
  });

  test('actualiza el tipo del recurso', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    const recurso = await crearRecurso(app, { sedeId: sede.id, nombre: 'Salón 12' });
    const res = await request(app)
      .put(`/recursos-fisicos/${recurso.id}`)
      .set(auth())
      .send({ nombre: 'Salón 12', tipo: 'LABORATORIO' });
    expect(res.status).toBe(200);
    expect(res.body.tipo).toBe('LABORATORIO');
  });

  test('filtra recursos por sede y por zona', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    const zona = await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });
    await crearRecurso(app, { sedeId: sede.id, zonaId: zona.id, nombre: 'Salón 1' });
    await crearRecurso(app, { sedeId: sede.id, zonaId: zona.id, nombre: 'Salón 2' });

    const porSede = await request(app).get(`/recursos-fisicos?sedeId=${sede.id}`).set(auth([]));
    expect(porSede.body).toHaveLength(2);

    const porZona = await request(app).get(`/zonas/${zona.id}/recursos-fisicos`).set(auth([]));
    expect(porZona.body).toHaveLength(2);
  });
});
