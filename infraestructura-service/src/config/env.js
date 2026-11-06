require('dotenv').config();

const JWT_SECRET_MINIMO = 32;
const JWT_SECRET_EJEMPLO = 'REEMPLAZAR_POR_UN_SECRET_DE_AL_MENOS_32_CARACTERES';
const CORS_ORIGINS_POR_DEFECTO = 'http://localhost:5173,http://localhost:3000';

function numero(valor, porDefecto) {
  const n = Number(valor);
  return Number.isFinite(n) && valor !== '' && valor !== undefined ? n : porDefecto;
}

// Lista separada por comas. Se rechaza '*' porque se envían credenciales.
function listaOrigenes(valor) {
  return String(valor || '')
    .split(',')
    .map((origen) => origen.trim().replace(/\/$/, ''))
    .filter(Boolean);
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
    // DB_SSL=true activa SSL en la conexion MySQL (exigido por algunos
    // proveedores gestionados). Por defecto false (MySQL local sin TLS).
    ssl: String(process.env.DB_SSL || '').trim().toLowerCase() === 'true',
  },
  jwtSecret: process.env.JWT_SECRET || '',
  corsOrigins: listaOrigenes(
    process.env.CORS_ORIGINS || CORS_ORIGINS_POR_DEFECTO
  ),
  // Proveedores externos. La url_base de cada uno vive en la tabla
  // servicios_externos; si la fila no esta sembrada el servicio responde 503.
  externos: {
    nagerPais: (process.env.NAGER_PAIS || 'CO').toUpperCase(),
    httpTimeoutMs: numero(process.env.HTTP_TIMEOUT_MS, 15000),
  },
  // Se leen en cada llamada (getters) para que las pruebas puedan ajustar el
  // entorno sin recargar el modulo. La API key de Brevo NUNCA va en la base de
  // datos: solo vive en la variable de entorno.
  email: {
    get providerApiKey() {
      return process.env.EMAIL_PROVIDER_API_KEY || '';
    },
    get from() {
      return process.env.EMAIL_FROM || '';
    },
    get fromName() {
      return process.env.EMAIL_FROM_NAME || '';
    },
  },
};

// Falla el arranque si la configuracion de seguridad no es valida. No se
// imprime ningun valor: solo se indica que variable corregir.
function validarConfiguracion() {
  if (!env.jwtSecret || env.jwtSecret.length < JWT_SECRET_MINIMO) {
    throw new Error(
      `JWT_SECRET debe tener al menos ${JWT_SECRET_MINIMO} caracteres.`
    );
  }
  if (env.jwtSecret === JWT_SECRET_EJEMPLO) {
    throw new Error('JWT_SECRET no puede ser el valor de ejemplo.');
  }
  if (env.corsOrigins.length === 0) {
    throw new Error('CORS_ORIGINS debe definir al menos un origen.');
  }
  if (env.corsOrigins.includes('*')) {
    throw new Error(
      "CORS_ORIGINS no puede contener '*' cuando se usan credenciales."
    );
  }
}

env.validarConfiguracion = validarConfiguracion;
env.JWT_SECRET_MINIMO = JWT_SECRET_MINIMO;
env.JWT_SECRET_EJEMPLO = JWT_SECRET_EJEMPLO;
env.CORS_ORIGINS_POR_DEFECTO = CORS_ORIGINS_POR_DEFECTO;

module.exports = env;
