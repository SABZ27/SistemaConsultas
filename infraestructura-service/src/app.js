const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const env = require('./config/env');
const rutas = require('./routes');
const { notFoundHandler, errorHandler } = require('./middlewares/errorHandler');

// Los cuerpos JSON nunca superan 1 MiB. Un cuerpo mayor responde 413.
const LIMITE_CUERPO = '1mb';

function crearApp() {
  env.validarConfiguracion();

  const app = express();

  app.disable('x-powered-by');
  app.use(
    helmet({
      frameguard: { action: 'deny' },
      crossOriginResourcePolicy: { policy: 'cross-origin' },
    })
  );
  app.use(
    cors({
      origin: env.corsOrigins,
      credentials: true,
    })
  );
  app.use(express.json({ limit: LIMITE_CUERPO }));

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', servicio: 'infraestructura' });
  });

  app.use(rutas);

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = crearApp;
