require('dotenv').config();

function numero(valor, porDefecto) {
  const n = Number(valor);
  return Number.isFinite(n) && valor !== '' && valor !== undefined ? n : porDefecto;
}

const env = {
  nodeEnv: process.env.NODE_ENV || 'development',
  port: numero(process.env.PORT, 3001),
  db: {
    host: process.env.DB_HOST || '127.0.0.1',
    port: numero(process.env.DB_PORT, 3306),
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'sistema_consultas_infra',
    connectionLimit: numero(process.env.DB_CONNECTION_LIMIT, 10),
  },
  jwtSecret: process.env.JWT_SECRET || '',
  corsOrigins: (process.env.CORS_ORIGINS || '*')
    .split(',')
    .map((origen) => origen.trim())
    .filter(Boolean),
};

module.exports = env;
