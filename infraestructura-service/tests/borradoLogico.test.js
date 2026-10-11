const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, crearSede, crearZona, crearRecurso, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('borrado lógico y únicos con reactivación', () => {
  test('la sede desactivada desaparece del listado y reaparece con incluir_inactivos', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });

    const borrar = await request(app).delete(`/sedes/${sede.id}`).set(auth());
    expect(borrar.status).toBe(204);

    const listado = await request(app).get('/sedes').set(auth([]));
    expect(listado.body).toHaveLength(0);

    const obtener = await request(app).get(`/sedes/${sede.id}`).set(auth([]));
    expect(obtener.status).toBe(404);

    const conInactivos = await request(app).get('/sedes?incluir_inactivos=true').set(auth());
    expect(conInactivos.body).toHaveLength(1);
    expect(conInactivos.body[0].estado).toBe(false);
  });

  test('reactivar una sede la vuelve a exponer', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    await request(app).delete(`/sedes/${sede.id}`).set(auth());

    const activar = await request(app).patch(`/sedes/${sede.id}/activar`).set(auth());
    expect(activar.status).toBe(200);
    expect(activar.body.estado).toBe(true);

    const listado = await request(app).get('/sedes').set(auth([]));
    expect(listado.body).toHaveLength(1);
  });

  test('permite reutilizar el nombre tras el borrado lógico', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    await request(app).delete(`/sedes/${sede.id}`).set(auth());

    const nueva = await request(app)
      .post('/sedes')
      .set(auth())
      .send({ nombre: 'Sede Norte', tipoEstructura: 'BLOQUES' });
    expect(nueva.status).toBe(201);

    // Reactivar la antigua choca con la nueva activa.
    const reactivar = await request(app).patch(`/sedes/${sede.id}/activar`).set(auth());
    expect(reactivar.status).toBe(400);
  });

  test('una zona libera su nombre único tras el borrado lógico', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    const zona = await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });

    const borrar = await request(app).delete(`/zonas/${zona.id}`).set(auth());
    expect(borrar.status).toBe(204);

    const reutilizar = await request(app)
      .post('/zonas')
      .set(auth())
      .send({ sedeId: sede.id, nombre: 'Bloque A' });
    expect(reutilizar.status).toBe(201);

    const reactivar = await request(app).patch(`/zonas/${zona.id}/activar`).set(auth());
    expect(reactivar.status).toBe(400);
  });

  test('un recurso libera su nombre único tras el borrado lógico', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    const recurso = await crearRecurso(app, { sedeId: sede.id, nombre: 'Salón 12' });

    const borrar = await request(app).delete(`/recursos-fisicos/${recurso.id}`).set(auth());
    expect(borrar.status).toBe(204);

    const reutilizar = await request(app)
      .post('/recursos-fisicos')
      .set(auth())
      .send({ sedeId: sede.id, nombre: 'Salón 12' });
    expect(reutilizar.status).toBe(201);

    const reactivar = await request(app)
      .patch(`/recursos-fisicos/${recurso.id}/activar`)
      .set(auth());
    expect(reactivar.status).toBe(400);
  });
});
