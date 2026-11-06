// Bloque D (6): autorización de las rutas de Express. Solo tests, sin tocar
// código de producción. Diseño intencional: /health es la única ruta pública.

const request = require('supertest');

const crearApp = require('../src/app');
const { auth, authServicio, limpiarTablas, mockFetch, respuestaJson, pool } = require('./helpers');

const app = crearApp();

const CORREO = {
  para: 'destinatario@ejemplo.com',
  asunto: 'Prueba de autorización',
  contenido: 'Contenido de prueba.',
};

const ORIGINALES = {
  EMAIL_PROVIDER_API_KEY: process.env.EMAIL_PROVIDER_API_KEY,
  EMAIL_FROM: process.env.EMAIL_FROM,
  EMAIL_FROM_NAME: process.env.EMAIL_FROM_NAME,
};

beforeEach(async () => {
  process.env.EMAIL_PROVIDER_API_KEY = 'clave-de-prueba';
  process.env.EMAIL_FROM = 'no-reply@ejemplo.com';
  process.env.EMAIL_FROM_NAME = 'Sistema de Consultas';
  mockFetch(async () => respuestaJson(201, { messageId: '<abc123@ejemplo.com>' }));
  await limpiarTablas();
});

afterEach(() => {
  for (const [nombre, valor] of Object.entries(ORIGINALES)) {
    if (valor === undefined) {
      delete process.env[nombre];
    } else {
      process.env[nombre] = valor;
    }
  }
});

afterAll(async () => {
  await pool.end();
});

describe('POST /correos por rol', () => {
  test.each(['ESTUDIANTE', 'DOCENTE', 'ADMINISTRADOR'])(
    'un token de usuario (%s) responde 403',
    async (rol) => {
      const res = await request(app).post('/correos').set(auth([], rol)).send(CORREO);

      expect(res.status).toBe(403);
      expect(res.body.error).toBe('Forbidden');
    }
  );

  test('un token SERVICIO responde 2xx (201)', async () => {
    const res = await request(app).post('/correos').set(authServicio()).send(CORREO);

    expect(res.status).toBe(201);
    expect(res.body.estadoEnvio).toBe('ENVIADO');
  });
});

describe('DELETE /festivos/:id por rol', () => {
  test.each(['ESTUDIANTE', 'DOCENTE', 'SERVICIO'])(
    'un rol distinto de ADMINISTRADOR (%s) responde 403',
    async (rol) => {
      const res = await request(app).delete('/festivos/999999').set(auth([], rol));

      expect(res.status).toBe(403);
      expect(res.body.error).toBe('Forbidden');
    }
  );

  test('ADMINISTRADOR pasa el control de rol (404 si el festivo no existe)', async () => {
    const res = await request(app).delete('/festivos/999999').set(auth());

    expect(res.status).not.toBe(401);
    expect(res.status).not.toBe(403);
  });
});

describe('rutas protegidas sin token -> 401', () => {
  test('GET /festivos', async () => {
    const res = await request(app).get('/festivos?anio=2026');
    expect(res.status).toBe(401);
  });

  test('GET /festivos/validar', async () => {
    const res = await request(app).get('/festivos/validar?fecha=2026-01-01');
    expect(res.status).toBe(401);
  });

  test('GET /servicios-externos', async () => {
    const res = await request(app).get('/servicios-externos');
    expect(res.status).toBe(401);
  });

  test('POST /correos', async () => {
    const res = await request(app).post('/correos').send(CORREO);
    expect(res.status).toBe(401);
  });

  test('DELETE /festivos/:id', async () => {
    const res = await request(app).delete('/festivos/999999');
    expect(res.status).toBe(401);
  });
});

describe('diseño intencional: única ruta pública', () => {
  test('GET /health responde 200 sin token', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
  });
});
