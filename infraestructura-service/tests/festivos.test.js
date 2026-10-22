const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, mockFetch, respuestaJson, pool } = require('./helpers');
const { FESTIVOS_CO_2026 } = require('./fixtures/nagerCo2026');

const app = crearApp();

const FESTIVOS_ESPERADOS = [
  { fecha: '2026-01-01', nombre: 'Año Nuevo' },
  { fecha: '2026-01-12', nombre: 'Día de los Reyes Magos' },
  { fecha: '2026-03-23', nombre: 'Día de San José' },
  { fecha: '2026-04-02', nombre: 'Jueves Santo' },
  { fecha: '2026-04-03', nombre: 'Viernes Santo' },
  { fecha: '2026-05-01', nombre: 'Día del Trabajo' },
  { fecha: '2026-05-18', nombre: 'Ascensión del Señor' },
  { fecha: '2026-06-08', nombre: 'Corpus Christi' },
  { fecha: '2026-06-15', nombre: 'Sagrado Corazón' },
  { fecha: '2026-06-29', nombre: 'San Pedro y San Pablo' },
  { fecha: '2026-07-13', nombre: 'Día de la Virgen de Chiquinquirá' },
  { fecha: '2026-07-20', nombre: 'Declaración de la Independencia de Colombia' },
  { fecha: '2026-08-07', nombre: 'Batalla de Boyacá' },
  { fecha: '2026-08-17', nombre: 'La Asunción' },
  { fecha: '2026-10-12', nombre: 'Día de la Raza' },
  { fecha: '2026-11-02', nombre: 'Día de los Santos' },
  { fecha: '2026-11-16', nombre: 'Independencia de Cartagena' },
  { fecha: '2026-12-08', nombre: 'La Inmaculada Concepción' },
  { fecha: '2026-12-25', nombre: 'Navidad' },
];

beforeEach(async () => {
  mockFetch(async () => respuestaJson(200, FESTIVOS_CO_2026));
  await limpiarTablas();
});

afterAll(async () => {
  await pool.end();
});

describe('GET /festivos', () => {
  test('sincroniza con Nager.Date y devuelve los 19 festivos de 2026', async () => {
    const res = await request(app).get('/festivos?anio=2026').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(19);
    expect(res.body.map((f) => ({ fecha: f.fecha, nombre: f.nombre }))).toEqual(FESTIVOS_ESPERADOS);
  });

  test('la llamada al proveedor queda registrada en consultas_servicio_externo', async () => {
    await request(app).get('/festivos?anio=2026').set(auth());

    const [filas] = await pool.query('SELECT * FROM consultas_servicio_externo');
    expect(filas).toHaveLength(1);
    expect(filas[0]).toMatchObject({
      exito: 1,
      codigo_http: 200,
    });
    expect(filas[0].endpoint).toContain('/Holidays/CO/2026');
    expect(filas[0].referencia).toMatch(/^[0-9a-f-]{36}$/);
    expect(Number(filas[0].servicio_id)).toBeGreaterThan(0);
  });

  test('los festivos guardados quedan enlazados con la consulta registrada', async () => {
    await request(app).get('/festivos?anio=2026').set(auth());

    const [consultas] = await pool.query('SELECT id FROM consultas_servicio_externo');
    const [festivos] = await pool.query('SELECT consulta_servicio_id FROM festivos LIMIT 1');
    expect(consultas).toHaveLength(1);
    expect(Number(festivos[0].consulta_servicio_id)).toBe(Number(consultas[0].id));
  });

  test('la segunda consulta del mismo año no vuelve a llamar al proveedor', async () => {
    const fetchSpy = mockFetch(async () => respuestaJson(200, FESTIVOS_CO_2026));

    await request(app).get('/festivos?anio=2026').set(auth());
    await request(app).get('/festivos?anio=2026').set(auth());

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  test('el filtro por pais y anio se respeta en la cache', async () => {
    const res = await request(app).get('/festivos?anio=2026&pais=CO').set(auth());
    expect(res.status).toBe(200);
    expect(res.body.every((f) => f.pais === 'CO' && f.anio === 2026)).toBe(true);
  });
});

describe('GET /festivos/validar', () => {
  test('la Ascensión se observa el lunes siguiente (corrección Ley Emiliani)', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-05-18').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      fecha: '2026-05-18',
      pais: 'CO',
      esFestivo: true,
      nombre: 'Ascensión del Señor',
    });
  });

  test('el día de la plegaria (2026-05-14) no es festivo tras la corrección', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-05-14').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ fecha: '2026-05-14', esFestivo: false, nombre: null });
  });

  test('Corpus Christi se observa el lunes siguiente (corrección Ley Emiliani)', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-06-08').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      fecha: '2026-06-08',
      esFestivo: true,
      nombre: 'Corpus Christi',
    });
  });

  test('el día de la plegaria (2026-06-04) no es festivo tras la corrección', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-06-04').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ fecha: '2026-06-04', esFestivo: false, nombre: null });
  });

  test('un festivo que ya es lunes no se mueve', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-06-15').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      fecha: '2026-06-15',
      esFestivo: true,
      nombre: 'Sagrado Corazón',
    });
  });

  test('una fecha común no es festivo', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-02-10').set(auth());

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ fecha: '2026-02-10', esFestivo: false, nombre: null });
  });
});

describe('borrado lógico de festivos', () => {
  test('DELETE sin rol ADMINISTRADOR responde 403', async () => {
    await request(app).get('/festivos?anio=2026').set(auth());
    const [filas] = await pool.query('SELECT id FROM festivos LIMIT 1');

    const res = await request(app)
      .delete(`/festivos/${filas[0].id}`)
      .set(auth(['INFRAESTRUCTURA'], 'TECNICO'));

    expect(res.status).toBe(403);
    expect(res.body).toMatchObject({ status: 403, error: 'Forbidden' });
  });

  test('DELETE con ADMINISTRADOR desactiva el festivo', async () => {
    await request(app).get('/festivos?anio=2026').set(auth());
    const [filas] = await pool.query('SELECT id FROM festivos WHERE fecha = ?', ['2026-01-01']);

    const res = await request(app).delete(`/festivos/${filas[0].id}`).set(auth());

    expect(res.status).toBe(204);
    const [actualizados] = await pool.query('SELECT estado FROM festivos WHERE id = ?', [filas[0].id]);
    expect(actualizados[0].estado).toBe(0);
  });

  test('un festivo desactivado no aparece ni se resincroniza', async () => {
    const fetchSpy = mockFetch(async () => respuestaJson(200, FESTIVOS_CO_2026));

    await request(app).get('/festivos?anio=2026').set(auth());
    const [filas] = await pool.query('SELECT id FROM festivos WHERE fecha = ?', ['2026-01-01']);
    await request(app).delete(`/festivos/${filas[0].id}`).set(auth());

    const llamadasAntes = fetchSpy.mock.calls.length;
    const listado = await request(app).get('/festivos?anio=2026').set(auth());

    expect(listado.status).toBe(200);
    expect(listado.body.map((f) => f.fecha)).not.toContain('2026-01-01');
    expect(listado.body).toHaveLength(18);
    expect(fetchSpy.mock.calls.length).toBe(llamadasAntes);

    const validacion = await request(app).get('/festivos/validar?fecha=2026-01-01').set(auth());
    expect(validacion.body).toMatchObject({ esFestivo: false, nombre: null });

    const [estado] = await pool.query('SELECT estado FROM festivos WHERE id = ?', [filas[0].id]);
    expect(estado[0].estado).toBe(0);
  });

  test('DELETE de un festivo inexistente responde 404', async () => {
    const res = await request(app).delete('/festivos/999999').set(auth());
    expect(res.status).toBe(404);
  });
});

describe('fallos del proveedor de festivos', () => {
  test('un error de red responde 502 y deja la llamada registrada', async () => {
    mockFetch(async () => {
      throw new Error('fetch failed');
    });

    const res = await request(app).get('/festivos?anio=2026').set(auth());

    expect(res.status).toBe(502);

    const [consultas] = await pool.query('SELECT * FROM consultas_servicio_externo');
    expect(consultas).toHaveLength(1);
    expect(consultas[0].codigo_http).toBeNull();
    expect(consultas[0].exito).toBe(0);
    expect(consultas[0].detalle).toBe('sin respuesta');
  });

  test('un 5xx se reintenta una vez y luego responde 502', async () => {
    const fetchSpy = mockFetch(async () => respuestaJson(500, { message: 'error' }));

    const res = await request(app).get('/festivos?anio=2026').set(auth());

    expect(res.status).toBe(502);
    expect(fetchSpy).toHaveBeenCalledTimes(2);

    const [consultas] = await pool.query('SELECT * FROM consultas_servicio_externo');
    expect(consultas).toHaveLength(1);
    expect(consultas[0].codigo_http).toBe(500);
    expect(consultas[0].exito).toBe(0);
  });

  test('un 404 del proveedor no se reintenta', async () => {
    const fetchSpy = mockFetch(async () => respuestaJson(404, { message: 'not found' }));

    const res = await request(app).get('/festivos?anio=2026').set(auth());

    expect(res.status).toBe(502);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
