const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, crearSede, crearZona, crearRecurso, pool } = require('./helpers');

const app = crearApp();

beforeEach(limpiarTablas);
afterAll(async () => {
  await pool.end();
});

describe('estructura de sedes (BLOQUES / SALONES / PISOS)', () => {
  test('SALONES: los recursos cuelgan directo de la sede', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Norte', tipoEstructura: 'SALONES' });
    await crearRecurso(app, { sedeId: sede.id, nombre: 'Salón 1' });
    await crearRecurso(app, { sedeId: sede.id, nombre: 'Salón 2' });

    const res = await request(app).get(`/sedes/${sede.id}/estructura`).set(auth([]));
    expect(res.status).toBe(200);
    expect(res.body.tipoEstructura).toBe('SALONES');
    expect(res.body.zonas).toEqual([]);
    expect(res.body.recursos).toHaveLength(2);
    expect(res.body.recursos[0].ubicacion).toBe('Sede Norte · Salón 1');
  });

  test('BLOQUES: la sede se divide en bloques con recursos', async () => {
    const sede = await crearSede(app, { nombre: 'Sede Principal', tipoEstructura: 'BLOQUES' });
    const bloqueA = await crearZona(app, { sedeId: sede.id, nombre: 'Bloque A' });
    await crearZona(app, { sedeId: sede.id, nombre: 'Bloque B' });
    await crearRecurso(app, { sedeId: sede.id, zonaId: bloqueA.id, nombre: 'Salón 1' });

    const res = await request(app).get(`/sedes/${sede.id}/estructura`).set(auth([]));
    expect(res.status).toBe(200);
    expect(res.body.zonas).toHaveLength(2);
    const zonaA = res.body.zonas.find((z) => z.nombre === 'Bloque A');
    expect(zonaA.recursos).toHaveLength(1);
    expect(zonaA.recursos[0].ubicacion).toBe('Sede Principal · Bloque A · Salón 1');
  });

  test('PISOS (Granadillo): Piso 1..5 con Salón 1..6 en cada piso', async () => {
    const sede = await crearSede(app, { nombre: 'Granadillo', tipoEstructura: 'PISOS' });
    for (let piso = 1; piso <= 5; piso += 1) {
      const zona = await crearZona(app, { sedeId: sede.id, nombre: `Piso ${piso}` });
      for (let salon = 1; salon <= 6; salon += 1) {
        await crearRecurso(app, {
          sedeId: sede.id,
          zonaId: zona.id,
          nombre: `Salón ${salon}`,
        });
      }
    }

    const res = await request(app).get(`/sedes/${sede.id}/estructura`).set(auth([]));
    expect(res.status).toBe(200);
    expect(res.body.nombre).toBe('Granadillo');
    expect(res.body.zonas).toHaveLength(5);
    for (const zona of res.body.zonas) {
      expect(zona.recursos).toHaveLength(6);
    }

    const piso2 = res.body.zonas.find((z) => z.nombre === 'Piso 2');
    const salon3 = piso2.recursos.find((r) => r.nombre === 'Salón 3');
    expect(salon3.ubicacion).toBe('Granadillo · Piso 2 · Salón 3');
  });

  test('estructura de una sede inexistente responde 404', async () => {
    const res = await request(app).get('/sedes/12345/estructura').set(auth([]));
    expect(res.status).toBe(404);
  });
});
