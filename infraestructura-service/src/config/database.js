const mysql = require('mysql2/promise');

const env = require('./env');

// SSL opcional para MySQL gestionado. Con DB_SSL=true se cifra la conexion;
// rejectUnauthorized=false acepta los certificados del proveedor sin CA propia.
const opcionesSsl = env.db.ssl ? { ssl: { rejectUnauthorized: false } } : {};

const pool = mysql.createPool({
  host: env.db.host,
  port: env.db.port,
  user: env.db.user,
  password: env.db.password,
  database: env.db.database,
  waitForConnections: true,
  connectionLimit: env.db.connectionLimit,
  queueLimit: 0,
  charset: 'utf8mb4_unicode_ci',
  dateStrings: false,
  ...opcionesSsl,
});

module.exports = pool;
