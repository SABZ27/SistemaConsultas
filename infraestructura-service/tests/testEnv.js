require('dotenv').config();

const NOMBRE_POR_DEFECTO = 'sistema_consultas_infra_test';
const SUFIJO_OBLIGATORIO = '_test';

// El nombre de la base de pruebas es EXCLUSIVAMENTE TEST_DB_NAME (o su valor por
// defecto). No se deriva de DB_NAME ni se recalcula a partir de DB_NAME, de modo
// que aplicarEnvDePrueba() es idempotente aunque DB_NAME ya esté mutado.
function partesBase() {
  return {
    host: process.env.TEST_DB_HOST || process.env.DB_HOST || '127.0.0.1',
    port: Number(process.env.TEST_DB_PORT || process.env.DB_PORT || 3306),
    user: process.env.TEST_DB_USER || process.env.DB_USER || 'root',
    password: process.env.TEST_DB_PASSWORD ?? process.env.DB_PASSWORD ?? '',
    database: process.env.TEST_DB_NAME || NOMBRE_POR_DEFECTO,
  };
}

// Inserta "_w<workerId>" antes del sufijo "_test" para que cada worker de Jest
// use su propia base y no interfiera con los demás (y siga terminando en _test).
function nombreParaWorker(database, workerId) {
  if (workerId === undefined || workerId === null || workerId === '') {
    return database;
  }
  const sinSufijo = database.endsWith(SUFIJO_OBLIGATORIO)
    ? database.slice(0, -SUFIJO_OBLIGATORIO.length)
    : database;
  return `${sinSufijo}_w${workerId}${SUFIJO_OBLIGATORIO}`;
}

function resolverConfigDePrueba(workerId) {
  const base = partesBase();
  return { ...base, database: nombreParaWorker(base.database, workerId) };
}

function asegurarNombreDePrueba(database) {
  if (typeof database !== 'string' || !database.endsWith(SUFIJO_OBLIGATORIO)) {
    throw new Error(
      `Nombre de base de datos de pruebas inseguro: "${database}". ` +
        `Debe terminar en "${SUFIJO_OBLIGATORIO}" (variable TEST_DB_NAME).`
    );
  }
}

// Idempotente: para un mismo workerId (o ausencia de él) llamarla N veces
// produce siempre el mismo resultado y los mismos valores en process.env.
function aplicarEnvDePrueba(workerId) {
  const config = resolverConfigDePrueba(workerId);
  asegurarNombreDePrueba(config.database);

  process.env.DB_HOST = config.host;
  process.env.DB_PORT = String(config.port);
  process.env.DB_USER = config.user;
  process.env.DB_PASSWORD = config.password;
  process.env.DB_NAME = config.database;
  process.env.JWT_SECRET =
    process.env.JWT_SECRET || 'secreto-de-pruebas-con-mas-de-treinta-y-dos-caracteres';
  process.env.NODE_ENV = 'test';

  return config;
}

module.exports = {
  NOMBRE_POR_DEFECTO,
  SUFIJO_OBLIGATORIO,
  partesBase,
  nombreParaWorker,
  resolverConfigDePrueba,
  asegurarNombreDePrueba,
  aplicarEnvDePrueba,
};
