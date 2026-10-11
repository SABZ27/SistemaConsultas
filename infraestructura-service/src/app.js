const express = require('express');
const cors = require('cors');

const env = require('./config/env');
const rutas = require('./routes');
const { notFoundHandler, errorHandler } = require('./middlewares/errorHandler');

function crearApp() {
  const app = express();

  app.disable('x-powered-by');
  app.use(express.json());
  app.use(
    cors({
      origin: env.corsOrigins.includes('*') ? true : env.corsOrigins,
      credentials: true,
    })
  );

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', servicio: 'infraestructura' });
  });

  app.use(rutas);

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = crearApp;
