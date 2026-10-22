const request = require('supertest');

const crearApp = require('../src/app');
const { auth, limpiarTablas, mockFetch, respuestaJson, pool } = require('./helpers');

const app = crearApp();

const CORREO = {
  para: 'destinatario@ejemplo.com',
  paraNombre: 'Destinatario de Prueba',
  asunto: 'Confirmación de la solicitud',
  contenido: 'Su solicitud fue registrada correctamente.',
};

const API_KEY_ORIGINAL = process.env.EMAIL_PROVIDER_API_KEY;
const FROM_ORIGINAL = process.env.EMAIL_FROM;
const FROM_NAME_ORIGINAL = process.env.EMAIL_FROM_NAME;

beforeEach(async () => {
  process.env.EMAIL_PROVIDER_API_KEY = 'clave-de-prueba';
  process.env.EMAIL_FROM = 'no-reply@ejemplo.com';
  process.env.EMAIL_FROM_NAME = 'Sistema de Consultas';
  mockFetch(async () => respuestaJson(201, { messageId: '<abc123@ejemplo.com>' }));
  await limpiarTablas();
});

afterEach(() => {
  restaurar('EMAIL_PROVIDER_API_KEY', API_KEY_ORIGINAL);
  restaurar('EMAIL_FROM', FROM_ORIGINAL);
  restaurar('EMAIL_FROM_NAME', FROM_NAME_ORIGINAL);
});

function restaurar(nombre, valor) {
  if (valor === undefined) {
    delete process.env[nombre];
    return;
  }
  process.env[nombre] = valor;
}

afterAll(async () => {
  await pool.end();
});

describe('POST /correos', () => {
  test('envía el correo y registra la traza completa', async () => {
    const res = await request(app).post('/correos').set(auth()).send(CORREO);

    expect(res.status).toBe(201);
    expect(res.body).toMatchObject({
      estadoEnvio: 'ENVIADO',
      messageId: '<abc123@ejemplo.com>',
    });
    expect(res.body.id).toBeTruthy();

    const [correos] = await pool.query('SELECT * FROM correos_enviados');
    expect(correos).toHaveLength(1);
    expect(correos[0].estado_envio).toBe('ENVIADO');
    expect(correos[0].respuesta_proveedor).toBe('<abc123@ejemplo.com>');
    expect(correos[0].destinatario).toBe(CORREO.para);
    expect(correos[0].asunto).toBe(CORREO.asunto);

    const [consultas] = await pool.query('SELECT * FROM consultas_servicio_externo');
    expect(consultas).toHaveLength(1);
    expect(consultas[0].exito).toBe(1);
    expect(consultas[0].codigo_http).toBe(201);
    expect(consultas[0].endpoint).toContain('/smtp/email');
    expect(Number(correos[0].consulta_servicio_id)).toBe(Number(consultas[0].id));
  });

  test('la llamada a Brevo usa la API HTTP con la cabecera api-key', async () => {
    const fetchSpy = mockFetch(async () => respuestaJson(201, { messageId: '<abc123@ejemplo.com>' }));

    await request(app).post('/correos').set(auth()).send(CORREO);

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, opciones] = fetchSpy.mock.calls[0];
    expect(url).toBe('https://api.brevo.com/v3/smtp/email');
    expect(opciones.method).toBe('POST');
    expect(opciones.headers['api-key']).toBe('clave-de-prueba');
    expect(opciones.body).toContain('destinatario@ejemplo.com');
    expect(opciones.body).toContain('Confirmación de la solicitud');
  });

  test('no reintenta el envío aunque el proveedor responda 500', async () => {
    const fetchSpy = mockFetch(async () => respuestaJson(500, { message: 'error' }));

    const res = await request(app).post('/correos').set(auth()).send(CORREO);

    expect(res.status).toBe(502);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  test('un error de red deja la llamada registrada y el correo en FALLIDO', async () => {
    mockFetch(async () => {
      throw new Error('fetch failed');
    });

    const res = await request(app).post('/correos').set(auth()).send(CORREO);

    expect(res.status).toBe(502);

    const [consultas] = await pool.query('SELECT * FROM consultas_servicio_externo');
    expect(consultas).toHaveLength(1);
    expect(consultas[0].codigo_http).toBeNull();
    expect(consultas[0].exito).toBe(0);
    expect(consultas[0].detalle).toBe('sin respuesta');

    const [correos] = await pool.query('SELECT * FROM correos_enviados');
    expect(correos).toHaveLength(1);
    expect(correos[0].estado_envio).toBe('FALLIDO');
    expect(correos[0].respuesta_proveedor).toBeNull();
  });

  test('un error del proveedor deja el correo en FALLIDO y responde 502', async () => {
    mockFetch(async () => respuestaJson(400, { message: 'invalid' }));

    const res = await request(app).post('/correos').set(auth()).send(CORREO);

    expect(res.status).toBe(502);

    const [correos] = await pool.query('SELECT * FROM correos_enviados');
    expect(correos[0].estado_envio).toBe('FALLIDO');
  });

  test('cualquier usuario autenticado puede enviar correos', async () => {
    const res = await request(app)
      .post('/correos')
      .set(auth(['INFRAESTRUCTURA'], 'TECNICO'))
      .send(CORREO);

    expect(res.status).toBe(201);
  });

  test('valida el cuerpo de la petición', async () => {
    const res = await request(app)
      .post('/correos')
      .set(auth())
      .send({ para: 'no-es-un-correo', asunto: '', contenido: 'texto' });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Bad Request');
    expect(res.body.errors).toHaveProperty('para');
    expect(res.body.errors).toHaveProperty('asunto');
  });

  test('sin API key configurada responde 503', async () => {
    process.env.EMAIL_PROVIDER_API_KEY = '';

    const res = await request(app).post('/correos').set(auth()).send(CORREO);

    expect(res.status).toBe(503);
  });
});
