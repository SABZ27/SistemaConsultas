const jwt = require('jsonwebtoken');
const request = require('supertest');

const crearApp = require('../src/app');
const env = require('../src/config/env');
const { errorHandler } = require('../src/middlewares/errorHandler');
const { pool } = require('./helpers');

const app = crearApp();

afterAll(async () => {
  await pool.end();
});

describe('cabeceras de seguridad', () => {
  test('GET /health aplica Helmet y oculta x-powered-by', async () => {
    const res = await request(app).get('/health');

    expect(res.status).toBe(200);
    expect(res.headers['x-powered-by']).toBeUndefined();
    expect(res.headers['x-content-type-options']).toBe('nosniff');
    expect(res.headers['x-frame-options']).toBe('DENY');
    expect(res.headers['referrer-policy']).toBe('no-referrer');
    expect(res.headers['cross-origin-resource-policy']).toBe('cross-origin');
  });
});

describe('CORS por lista', () => {
  test('permite un origen configurado', async () => {
    const res = await request(app)
      .get('/health')
      .set('Origin', 'http://localhost:5173');

    expect(res.headers['access-control-allow-origin']).toBe(
      'http://localhost:5173'
    );
  });

  test('no permite un origen no configurado', async () => {
    const res = await request(app)
      .get('/health')
      .set('Origin', 'http://malicioso.test');

    expect(res.headers['access-control-allow-origin']).toBeUndefined();
  });
});

describe('límite de cuerpo', () => {
  test('un JSON mayor de 1 MiB responde 413 con formato de error', async () => {
    const grande = JSON.stringify({
      para: 'a@b.com',
      asunto: 'Prueba',
      contenido: 'x'.repeat(1024 * 1024 + 100),
    });

    const res = await request(app)
      .post('/correos')
      .set('Content-Type', 'application/json')
      .send(grande);

    expect(res.status).toBe(413);
    expect(res.body).toMatchObject({
      status: 413,
      error: 'Payload Too Large',
      message: 'El cuerpo de la solicitud es demasiado grande.',
    });
  });
});

describe('JWT endurecido', () => {
  function firmar(payload, opciones = {}) {
    return jwt.sign(payload, process.env.JWT_SECRET, {
      algorithm: 'HS256',
      ...opciones,
    });
  }

  test('un token sin exp responde 401', async () => {
    const token = firmar({
      sub: 'usuario@test.com',
      uid: 1,
      rol: 'ADMINISTRADOR',
      modulos: ['INFRAESTRUCTURA'],
    });

    const res = await request(app)
      .get('/servicios-externos')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(401);
  });

  test('un token con exp firmado en HS256 sigue siendo válido', async () => {
    const token = firmar(
      {
        sub: 'usuario@test.com',
        uid: 1,
        rol: 'ADMINISTRADOR',
        modulos: ['INFRAESTRUCTURA'],
      },
      { expiresIn: '5m' }
    );

    const res = await request(app)
      .get('/servicios-externos')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
  });
});

describe('validación de configuración de arranque', () => {
  const original = {
    jwtSecret: env.jwtSecret,
    corsOrigins: env.corsOrigins,
  };

  afterEach(() => {
    env.jwtSecret = original.jwtSecret;
    env.corsOrigins = original.corsOrigins;
  });

  test('rechaza JWT_SECRET corto', () => {
    env.jwtSecret = 'corto';
    expect(() => env.validarConfiguracion()).toThrow(/32/);
  });

  test('rechaza JWT_SECRET de ejemplo', () => {
    env.jwtSecret = env.JWT_SECRET_EJEMPLO;
    expect(() => env.validarConfiguracion()).toThrow(/ejemplo/);
  });

  test('rechaza CORS con comodín o sin orígenes', () => {
    env.corsOrigins = ['*'];
    expect(() => env.validarConfiguracion()).toThrow(/CORS_ORIGINS/);

    env.corsOrigins = [];
    expect(() => env.validarConfiguracion()).toThrow(/al menos un origen/);
  });
});

describe('error 500', () => {
  test('no expone el mensaje original ni lo registra en el log', () => {
    const error = new Error(
      'correo@secreto.test token-super-secreto password=ClaveSegura#2026'
    );
    const res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
    };
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

    try {
      errorHandler(error, {}, res, () => {});

      expect(res.status).toHaveBeenCalledWith(500);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 500,
          error: 'Internal Server Error',
          message: 'Error interno del servidor.',
        })
      );

      const registrado = spy.mock.calls.flat().join(' ');
      expect(registrado).not.toContain('correo@secreto.test');
      expect(registrado).not.toContain('token-super-secreto');
      expect(registrado).not.toContain('ClaveSegura#2026');
    } finally {
      spy.mockRestore();
    }
  });
});
